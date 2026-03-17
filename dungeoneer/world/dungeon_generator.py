"""BSP dungeon generator.

Produces a DungeonMap with connected rooms and an exit staircase.
Also returns spawn descriptors for the caller to instantiate as entities.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

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
    stair_pos: tuple[int, int]


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

        # Stairs in one of the N farthest rooms from the start room
        other_rooms = rooms[1:]
        other_rooms_sorted = sorted(
            other_rooms,
            key=lambda r: (r.cx - start_room.cx) ** 2 + (r.cy - start_room.cy) ** 2,
            reverse=True,
        )
        end_room = self._rng.choice(other_rooms_sorted[:STAIR_FARTHEST_CANDIDATES])
        sx, sy = end_room.cx, end_room.cy
        dungeon_map.set_type(sx, sy, TileType.STAIR_DOWN)

        # Distribute enemies in middle rooms (not start or end room)
        middle_rooms = [r for r in rooms if r is not start_room and r is not end_room]
        enemy_rooms = self._rng.sample(
            middle_rooms,
            min(guards + drones, len(middle_rooms)),
        )
        for i, room in enumerate(enemy_rooms):
            ex, ey = room.random_inner_point()
            if i < guards:
                spawns.append(SpawnDesc("guard", ex, ey))
            else:
                spawns.append(SpawnDesc("drone", ex, ey))

        # Pre-compute room-interior tile set for entrance detection
        room_tile_set: set[tuple[int, int]] = set()
        for r in rooms:
            for ry in range(r.inner_y, r.inner_y + r.inner_h):
                for rx in range(r.inner_x, r.inner_x + r.inner_w):
                    room_tile_set.add((rx, ry))

        # Containers in random rooms (any room, including start/end)
        # Avoid doorway tiles so the player can always pass through entrances.
        container_rooms = self._rng.choices(rooms, k=containers)
        for room in container_rooms:
            cx, cy = self._safe_container_pos(room, room_tile_set, dungeon_map)
            spawns.append(SpawnDesc("container", cx, cy))

        return GenerationResult(dungeon_map, rooms, spawns, (sx, sy))

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
        max_tries: int = 30,
    ) -> tuple[int, int]:
        """Return an inner tile not adjacent to a corridor entrance.

        Falls back to the room centre if every sampled tile is an entrance tile
        (can happen in very small rooms with multiple corridors).
        """
        for _ in range(max_tries):
            x, y = room.random_inner_point()
            if not self._adjacent_to_corridor(x, y, room_tile_set, dungeon_map):
                return x, y
        return room.cx, room.cy

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
