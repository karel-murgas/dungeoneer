"""BSP dungeon generator.

Produces a DungeonMap with connected rooms and an exit staircase.
Also returns spawn descriptors for the caller to instantiate as entities.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

from dungeoneer.core import settings as _settings
from dungeoneer.core.settings import STAIR_FARTHEST_CANDIDATES
from dungeoneer.world.map import DungeonMap
from dungeoneer.world.room import Room
from dungeoneer.world.tile import TileType


# ---------------------------------------------------------------------------
# Spawn descriptor (no entity objects here — keeps generation pure/testable)
# ---------------------------------------------------------------------------

@dataclass
class SpawnDesc:
    kind: str       # "player", "guard", "drone"
    x: int
    y: int


@dataclass
class GenerationResult:
    dungeon_map: DungeonMap
    rooms: list[Room]
    spawns: list[SpawnDesc]
    stair_pos: tuple[int, int]   # elevator position (legacy name kept for compat)
    entry_pos: tuple[int, int]   # entry elevator position in start room


# ---------------------------------------------------------------------------
# BSP node
# ---------------------------------------------------------------------------

@dataclass
class BSPNode:
    x: int
    y: int
    w: int
    h: int
    left:  Optional["BSPNode"] = field(default=None, repr=False)
    right: Optional["BSPNode"] = field(default=None, repr=False)
    room:  Optional[Room]      = field(default=None, repr=False)

    @property
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None

    def get_room(self) -> Optional[Room]:
        """Return a room from this subtree (any leaf)."""
        if self.room:
            return self.room
        if self.left and self.right:
            return self.left.get_room() or self.right.get_room()
        if self.left:
            return self.left.get_room()
        if self.right:
            return self.right.get_room()
        return None


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

MIN_ROOM_SIZE = 5    # inner floor size
MAX_ROOM_SIZE = 10
MIN_LEAF_SIZE = MIN_ROOM_SIZE + 4   # extra margin for walls + corridor space

# Enemy density defaults (overridden by Difficulty when passed)
_DEFAULT_GUARDS      = 5
_DEFAULT_DRONES      = 3
_DEFAULT_CONTAINERS  = 3

# Tier-based enemy pool — keys are tier numbers (1=lowest, 3=highest).
# heat mechanic will raise tier_cap to unlock stronger enemies.
_ENEMY_POOL: dict[int, list[str]] = {
    1: ["guard", "drone", "dog"],
    2: ["heavy", "turret"],
    3: ["sniper_drone", "riot_guard"],
}


class DungeonGenerator:
    def __init__(self, seed: Optional[int] = None) -> None:
        self._rng = random.Random(seed)

    def generate(
        self,
        width: int,
        height: int,
        floor_depth: int = 1,
        guards: int = _DEFAULT_GUARDS,
        drones: int = _DEFAULT_DRONES,
        containers: int = _DEFAULT_CONTAINERS,
        tier_cap: int = 1,
        place_vault: bool = False,
    ) -> GenerationResult:
        dungeon_map = DungeonMap(width, height)
        root = BSPNode(0, 0, width, height)
        self._split(root, depth=0)
        rooms = self._carve_rooms(root, dungeon_map)
        self._carve_corridors(root, dungeon_map)

        spawns: list[SpawnDesc] = []

        # Player starts in first room
        start_room = rooms[0]
        px, py = start_room.cx, start_room.cy
        spawns.append(SpawnDesc("player", px, py))

        # Entry elevator in the start room wall (the elevator the player came from)
        entry_x, entry_y = self._find_elevator_wall(start_room, dungeon_map)
        dungeon_map.set_type(entry_x, entry_y, TileType.ELEVATOR_ENTRY)

        # Elevator in one of the N farthest rooms from the start room.
        # Placed on a wall tile that has exactly one cardinal floor neighbour
        # (so the player can only approach from one side).
        other_rooms = rooms[1:]
        other_rooms_sorted = sorted(
            other_rooms,
            key=lambda r: (r.cx - start_room.cx) ** 2 + (r.cy - start_room.cy) ** 2,
            reverse=True,
        )
        end_room = self._rng.choice(other_rooms_sorted[:STAIR_FARTHEST_CANDIDATES])
        sx, sy = self._find_elevator_wall(end_room, dungeon_map)
        dungeon_map.set_type(sx, sy, TileType.ELEVATOR_CLOSED)

        # Pre-compute room-interior tile set for entrance detection
        room_tile_set: set[tuple[int, int]] = set()
        for r in rooms:
            for ry in range(r.inner_y, r.inner_y + r.inner_h):
                for rx in range(r.inner_x, r.inner_x + r.inner_w):
                    room_tile_set.add((rx, ry))

        # Containers in random rooms — prefer wall-mounted placement.
        # Avoid elevator tiles and already-placed spawns.
        container_rooms = self._rng.choices(rooms, k=containers)
        blocked: set[tuple[int, int]] = {(sx, sy), (px, py), (entry_x, entry_y)}
        # Block the floor tile adjacent to the entry elevator so the player can exit
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            if dungeon_map.is_walkable(entry_x + dx, entry_y + dy):
                blocked.add((entry_x + dx, entry_y + dy))
                break
        for sp in spawns:
            blocked.add((sp.x, sp.y))

        # Track which floor tiles are already "interaction zones" of placed wall
        # entities (tiles the player must stand on to use them).  New wall entities
        # must not share an interaction zone with any existing one so that pressing
        # [E] from a single tile is never ambiguous.
        def _add_interaction_zone(wx: int, wy: int) -> None:
            for ddx, ddy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                fnx, fny = wx + ddx, wy + ddy
                if dungeon_map.is_walkable(fnx, fny):
                    interaction_zones.add((fnx, fny))

        interaction_zones: set[tuple[int, int]] = set()
        _add_interaction_zone(sx, sy)
        _add_interaction_zone(entry_x, entry_y)

        # Vault objective — placed before containers so its interaction zone is
        # respected by subsequent wall-entity placement.
        if place_vault:
            vp = self._find_vault_pos(
                end_room, rooms, dungeon_map, blocked, interaction_zones,
                room_tile_set, sx, sy,
            )
            if vp is not None:
                vx, vy = vp
                spawns.append(SpawnDesc("vault_objective", vx, vy))
                blocked.add((vx, vy))
                # Vault is a floor entity: block the vault tile itself AND
                # all adjacent floor tiles so no wall entity shares its zone.
                interaction_zones.add((vx, vy))
                _add_interaction_zone(vx, vy)

        for room in container_rooms:
            wall_pos = self._wall_container_pos(room, dungeon_map, blocked, interaction_zones)
            if wall_pos is None:
                continue  # no suitable wall in this room — skip container
            cx, cy = wall_pos
            spawns.append(SpawnDesc("container", cx, cy))
            blocked.add((cx, cy))
            _add_interaction_zone(cx, cy)

        # Recharge nodes — 1-2 per floor on wall tiles with one floor neighbour
        n_nodes = self._rng.randint(*_settings.RECHARGE_NODES_PER_FLOOR)
        node_rooms = self._rng.choices(rooms, k=n_nodes)
        for room in node_rooms:
            wall_pos = self._wall_container_pos(room, dungeon_map, blocked, interaction_zones)
            if wall_pos is None:
                continue
            nx, ny = wall_pos
            spawns.append(SpawnDesc("recharge_node", nx, ny))
            blocked.add((nx, ny))
            _add_interaction_zone(nx, ny)

        return GenerationResult(dungeon_map, rooms, spawns, (sx, sy), (entry_x, entry_y))

    # ------------------------------------------------------------------
    # BSP splitting
    # ------------------------------------------------------------------

    def _split(self, node: BSPNode, depth: int) -> None:
        if depth >= 6:
            return
        if node.w < MIN_LEAF_SIZE * 2 and node.h < MIN_LEAF_SIZE * 2:
            return

        # Decide split axis — prefer splitting along the longer side
        split_horizontal = node.h > node.w
        if node.w >= MIN_LEAF_SIZE * 2 and node.h >= MIN_LEAF_SIZE * 2:
            split_horizontal = self._rng.random() < 0.5

        if split_horizontal:
            if node.h < MIN_LEAF_SIZE * 2:
                return
            split_at = self._rng.randint(MIN_LEAF_SIZE, node.h - MIN_LEAF_SIZE)
            node.left  = BSPNode(node.x, node.y,              node.w, split_at)
            node.right = BSPNode(node.x, node.y + split_at,   node.w, node.h - split_at)
        else:
            if node.w < MIN_LEAF_SIZE * 2:
                return
            split_at = self._rng.randint(MIN_LEAF_SIZE, node.w - MIN_LEAF_SIZE)
            node.left  = BSPNode(node.x,             node.y, split_at,          node.h)
            node.right = BSPNode(node.x + split_at,  node.y, node.w - split_at, node.h)

        self._split(node.left, depth + 1)
        self._split(node.right, depth + 1)

    # ------------------------------------------------------------------
    # Room carving
    # ------------------------------------------------------------------

    def _carve_rooms(self, node: BSPNode, dungeon_map: DungeonMap) -> list[Room]:
        rooms: list[Room] = []
        self._carve_rooms_recursive(node, dungeon_map, rooms)
        return rooms

    def _carve_rooms_recursive(
        self, node: BSPNode, dungeon_map: DungeonMap, rooms: list[Room]
    ) -> None:
        if node.is_leaf:
            rw = self._rng.randint(MIN_ROOM_SIZE, min(MAX_ROOM_SIZE, node.w - 2))
            rh = self._rng.randint(MIN_ROOM_SIZE, min(MAX_ROOM_SIZE, node.h - 2))
            rx = node.x + self._rng.randint(1, node.w - rw - 1)
            ry = node.y + self._rng.randint(1, node.h - rh - 1)
            room = Room(rx, ry, rw, rh)
            # Carve floor inside room
            dungeon_map.fill_rect(
                room.inner_x, room.inner_y, room.inner_w, room.inner_h,
                TileType.FLOOR
            )
            node.room = room
            rooms.append(room)
        else:
            if node.left:
                self._carve_rooms_recursive(node.left, dungeon_map, rooms)
            if node.right:
                self._carve_rooms_recursive(node.right, dungeon_map, rooms)

    # ------------------------------------------------------------------
    # Corridor carving
    # ------------------------------------------------------------------

    def _carve_corridors(self, node: BSPNode, dungeon_map: DungeonMap) -> None:
        if node.is_leaf:
            return
        if node.left:
            self._carve_corridors(node.left, dungeon_map)
        if node.right:
            self._carve_corridors(node.right, dungeon_map)

        # Connect the two subtrees at their centres
        left_room  = node.left.get_room()  if node.left  else None
        right_room = node.right.get_room() if node.right else None
        if left_room and right_room:
            self._carve_L_corridor(
                left_room.cx, left_room.cy,
                right_room.cx, right_room.cy,
                dungeon_map,
            )

    def _carve_L_corridor(
        self, x1: int, y1: int, x2: int, y2: int, dungeon_map: DungeonMap
    ) -> None:
        """Carve an L-shaped (two-segment) corridor between two points."""
        if self._rng.random() < 0.5:
            # Horizontal then vertical
            self._hline(x1, x2, y1, dungeon_map)
            self._vline(y1, y2, x2, dungeon_map)
        else:
            # Vertical then horizontal
            self._vline(y1, y2, x1, dungeon_map)
            self._hline(x1, x2, y2, dungeon_map)

    def _hline(self, x1: int, x2: int, y: int, dungeon_map: DungeonMap) -> None:
        for x in range(min(x1, x2), max(x1, x2) + 1):
            dungeon_map.carve_floor(x, y)

    def _vline(self, y1: int, y2: int, x: int, dungeon_map: DungeonMap) -> None:
        for y in range(min(y1, y2), max(y1, y2) + 1):
            dungeon_map.carve_floor(x, y)

    # ------------------------------------------------------------------
    # Container placement helpers
    # ------------------------------------------------------------------

    def _safe_container_pos(
        self,
        room: Room,
        room_tile_set: set[tuple[int, int]],
        dungeon_map: DungeonMap,
        blocked: set[tuple[int, int]] | None = None,
        max_tries: int = 30,
    ) -> tuple[int, int]:
        """Return an inner tile not adjacent to a corridor entrance and not in *blocked*.

        Falls back to the room centre if every sampled tile is rejected
        (can happen in very small rooms with multiple corridors).
        """
        if blocked is None:
            blocked = set()
        for _ in range(max_tries):
            x, y = room.random_inner_point()
            if (x, y) not in blocked and not self._adjacent_to_corridor(x, y, room_tile_set, dungeon_map):
                return x, y
        # Fallback: pick room centre only if it isn't blocked
        cx, cy = room.cx, room.cy
        if (cx, cy) not in blocked:
            return cx, cy
        # Last resort: first unblocked inner tile
        for ry in range(room.inner_y, room.inner_y + room.inner_h):
            for rx in range(room.inner_x, room.inner_x + room.inner_w):
                if (rx, ry) not in blocked:
                    return rx, ry
        return cx, cy

    def _find_vault_pos(
        self,
        preferred_room: Room,
        all_rooms: list[Room],
        dungeon_map: DungeonMap,
        blocked: set[tuple[int, int]],
        interaction_zones: set[tuple[int, int]],
        room_tile_set: set[tuple[int, int]],
        elevator_x: int,
        elevator_y: int,
        min_dist: int = 3,
        min_candidates: int = 1,
    ) -> tuple[int, int] | None:
        """Return a safe floor tile for the vault objective container.

        Candidates must be room-interior, not corridor-adjacent, not in any
        existing interaction zone, and at least *min_dist* tiles from the
        elevator wall tile.  Tries the elevator's own room first; falls back
        to the largest other room if too few candidates are available.
        """
        def _candidates(room: Room) -> list[tuple[int, int]]:
            result = []
            for ty in range(room.inner_y, room.inner_y + room.inner_h):
                for tx in range(room.inner_x, room.inner_x + room.inner_w):
                    if not dungeon_map.is_walkable(tx, ty):
                        continue
                    if (tx, ty) in blocked:
                        continue
                    if (tx, ty) in interaction_zones:
                        continue
                    if self._adjacent_to_corridor(tx, ty, room_tile_set, dungeon_map):
                        continue
                    if abs(tx - elevator_x) + abs(ty - elevator_y) < min_dist:
                        continue
                    result.append((tx, ty))
            return result

        cands = _candidates(preferred_room)
        if len(cands) >= min_candidates:
            return self._rng.choice(cands)

        # Fallback: largest other rooms (by inner area)
        others = sorted(
            [r for r in all_rooms if r is not preferred_room],
            key=lambda r: r.inner_w * r.inner_h,
            reverse=True,
        )
        for room in others:
            cands = _candidates(room)
            if len(cands) >= min_candidates:
                return self._rng.choice(cands)
        return None

    def _wall_container_pos(
        self,
        room: Room,
        dungeon_map: DungeonMap,
        blocked: set[tuple[int, int]],
        interaction_zones: set[tuple[int, int]] | None = None,
    ) -> tuple[int, int] | None:
        """Find a perimeter wall tile for a wall-mounted entity.

        The tile must belong to a single room's wall — tiles with walkable floor
        on both north+south or both east+west are rejected (they separate two
        separate floor areas, i.e. sit between two rooms or a room and a corridor).
        Corner positions (floor on two adjacent sides) are allowed.

        If *interaction_zones* is given, candidates whose adjacent floor tiles
        overlap with it are rejected, preventing two interactables from sharing
        the same [E]-press tile.

        Returns None if no suitable position exists in this room.
        """
        candidates: list[tuple[int, int]] = []
        for x in range(room.inner_x, room.inner_x + room.inner_w):
            for y in (room.y, room.y + room.h - 1):
                if (x, y) not in blocked and dungeon_map.get_type(x, y) == TileType.WALL:
                    if self._single_side_floor(x, y, dungeon_map):
                        candidates.append((x, y))
        for y in range(room.inner_y, room.inner_y + room.inner_h):
            for x in (room.x, room.x + room.w - 1):
                if (x, y) not in blocked and dungeon_map.get_type(x, y) == TileType.WALL:
                    if self._single_side_floor(x, y, dungeon_map):
                        candidates.append((x, y))
        if interaction_zones:
            candidates = [
                (x, y) for (x, y) in candidates
                if not any(
                    (x + ddx, y + ddy) in interaction_zones
                    for ddx, ddy in ((0, 1), (0, -1), (1, 0), (-1, 0))
                    if dungeon_map.is_walkable(x + ddx, y + ddy)
                )
            ]
        if candidates:
            return self._rng.choice(candidates)
        return None

    @staticmethod
    def _single_side_floor(x: int, y: int, dungeon_map: DungeonMap) -> bool:
        """True when (x, y) has at least one walkable cardinal neighbour but NOT
        on both opposite axes (N+S or E+W) — i.e. not sandwiched between two
        separate floor areas."""
        n = dungeon_map.is_walkable(x,     y - 1)
        s = dungeon_map.is_walkable(x,     y + 1)
        e = dungeon_map.is_walkable(x + 1, y)
        w = dungeon_map.is_walkable(x - 1, y)
        if not (n or s or e or w):
            return False          # no floor neighbour at all
        if (n and s) or (e and w):
            return False          # sandwiched between two separate areas
        return True

    def _adjacent_to_corridor(
        self,
        x: int,
        y: int,
        room_tile_set: set[tuple[int, int]],
        dungeon_map: DungeonMap,
    ) -> bool:
        """True if (x, y) has a cardinal walkable neighbour outside any room interior."""
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, ny = x + dx, y + dy
            if dungeon_map.is_walkable(nx, ny) and (nx, ny) not in room_tile_set:
                return True
        return False

    # ------------------------------------------------------------------
    # Elevator placement
    # ------------------------------------------------------------------

    def _find_elevator_wall(
        self, room: Room, dungeon_map: DungeonMap
    ) -> tuple[int, int]:
        """Find a wall tile on the room perimeter with exactly one cardinal floor neighbour.

        This guarantees the elevator is embedded in a wall and accessible from
        only one side.  Falls back to room centre (as floor tile) if no suitable
        wall tile is found.
        """
        candidates: list[tuple[int, int]] = []
        # Scan the four walls of the room (one tile outside the inner area)
        for x in range(room.inner_x, room.inner_x + room.inner_w):
            for y in (room.y, room.y + room.h - 1):  # top and bottom walls
                if dungeon_map.get_type(x, y) == TileType.WALL:
                    if self._exactly_one_floor_neighbour(x, y, dungeon_map):
                        candidates.append((x, y))
        for y in range(room.inner_y, room.inner_y + room.inner_h):
            for x in (room.x, room.x + room.w - 1):  # left and right walls
                if dungeon_map.get_type(x, y) == TileType.WALL:
                    if self._exactly_one_floor_neighbour(x, y, dungeon_map):
                        candidates.append((x, y))
        if candidates:
            return self._rng.choice(candidates)
        # Fallback: place elevator at room centre as a FLOOR-like tile
        return room.cx, room.cy

    @staticmethod
    def _exactly_one_floor_neighbour(
        x: int, y: int, dungeon_map: DungeonMap
    ) -> bool:
        """True when (x, y) has exactly one cardinal neighbour that is walkable."""
        count = 0
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            if dungeon_map.is_walkable(x + dx, y + dy):
                count += 1
        return count == 1
