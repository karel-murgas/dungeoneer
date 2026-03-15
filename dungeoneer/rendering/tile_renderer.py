"""TileRenderer: draws map tiles using Dithart sci-fi sprites with FOV shading.

Tile index mapping for tileset_for_free.png (8 cols × 15 rows, 32×32, 0-indexed).
Indices verified against the author's free_scifi_tileset_example.tmx (GID = index+1).

  FLOOR      → 112   (row 14 col 0)  plain sci-fi floor
  STAIR_DOWN → 47    (row  5 col 7)  hatch/stair
  DOOR       → 40    (row  5 col 0)  door

Wall autotile — 4-bit cardinal mask: N=bit0, S=bit1, W=bit2, E=bit3 (1 = floor neighbor)
─────────────────────────────────────────────────────────────────────────────────────────
  0b0001 (N)   → 42   north face       (floor to north = south wall of room shows tile 42)
  0b0010 (S)   → 88   south face       (floor to south = north wall shows tile 88)
  0b0100 (W)   → 20   left-side face   (floor to west)
  0b1000 (E)   → 16   right-side face  (floor to east)

  0b0101 (N+W) →  9   NW inner corner
  0b1001 (N+E) → 11   NE inner corner
  0b0110 (S+W) → 25   SW inner corner
  0b1010 (S+E) → 27   SE inner corner

When all 4 cardinal neighbours are walls (mask == 0), one diagonal neighbour
determines the outer-corner tile:
  SE floor →  1   outer top-left  (room extends SE of this tile)
  SW floor →  3   outer top-right (room extends SW)
  NE floor → 24   outer bot-left  (room extends NE)
  NW floor → 28   outer bot-right (room extends NW)
  none     →  0   true interior surface

Floor tile 112 is always rendered beneath wall face tiles because some face
tiles have transparent areas.

Shadows: visible floor tiles with a WALL to the north get a dark gradient
strip at the top edge; those with a wall to the west get one on the left edge.
"""
from __future__ import annotations

import os

import pygame

from dungeoneer.core import settings
from dungeoneer.world.tile import TileType
from dungeoneer.rendering.spritesheet import SpriteSheet
from dungeoneer.rendering import procedural_sprites

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")

# ---------------------------------------------------------------------------
# Non-wall tile indices
# ---------------------------------------------------------------------------
_TILE_INDEX: dict[TileType, int] = {
    TileType.FLOOR:      112,
    TileType.STAIR_DOWN:  47,
    TileType.DOOR:        40,
}

_RECT_COLOURS: dict[TileType, tuple] = {
    TileType.WALL:       (settings.COL_WALL,  settings.COL_WALL_DARK),
    TileType.FLOOR:      (settings.COL_FLOOR, settings.COL_FLOOR_DARK),
    TileType.STAIR_DOWN: (settings.COL_STAIR, settings.COL_STAIR_DARK),
    TileType.DOOR:       (settings.COL_FLOOR, settings.COL_FLOOR_DARK),
}

# ---------------------------------------------------------------------------
# Wall autotile table  (mask bits: N=0, S=1, W=2, E=3; set = floor neighbor)
# ---------------------------------------------------------------------------
_WALL_AUTOTILE: dict[int, int] = {
    # Single exposed face
    0b0001: 42,   # N floor → tile 42
    0b0010: 88,   # S floor → tile 88
    0b0100: 20,   # W floor → left-side face
    0b1000: 16,   # E floor → right-side face

    # Two adjacent faces — inner corners
    0b0101: 27,   # N+W
    0b1001: 25,   # N+E
    0b0110: 11,   # S+W
    0b1010:  9,   # S+E

    # Two opposite faces
    0b0011:  6,   # N+S
    0b1100: 23,   # E+W

    # T-junctions / wall end caps
    0b0111:  5,   # N+S+W → W cap (wall to E only)
    0b1011:  7,   # N+S+E → E cap (wall to W only)
    0b1101: 15,   # N+E+W → N cap (wall to S only)
    0b1110: 31,   # S+E+W → S cap (wall to N only)

    # Isolated wall pillar (floor on all four sides)
    0b1111: 21,
}


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _floor_at(dungeon_map: "DungeonMap", x: int, y: int) -> bool:  # type: ignore[name-defined]
    """True when (x, y) is in-bounds and is not a WALL tile."""
    if x < 0 or y < 0 or x >= dungeon_map.width or y >= dungeon_map.height:
        return False
    return dungeon_map.get_type(x, y) != TileType.WALL


def _autotile_index(dungeon_map: "DungeonMap", x: int, y: int) -> int:  # type: ignore[name-defined]
    """Return the spritesheet index for the wall tile at (x, y).

    Uses the 4-bit cardinal mask first.  When all four cardinal neighbours
    are also walls (mask == 0) the tile sits at an outer corner of a room;
    a diagonal check selects the matching corner piece so it blends with the
    face tiles bordering it.
    """
    n = _floor_at(dungeon_map, x,     y - 1)
    s = _floor_at(dungeon_map, x,     y + 1)
    w = _floor_at(dungeon_map, x - 1, y    )
    e = _floor_at(dungeon_map, x + 1, y    )
    mask = n | (s << 1) | (w << 2) | (e << 3)

    if mask != 0:
        return _WALL_AUTOTILE.get(mask, 0)

    # All cardinal neighbours are walls — check diagonals for outer corners.
    # Diagonal order matters: check the most visually prominent direction first.
    if _floor_at(dungeon_map, x + 1, y + 1):   # SE floor → outer top-left corner
        return 1
    if _floor_at(dungeon_map, x - 1, y + 1):   # SW floor → outer top-right corner
        return 3
    if _floor_at(dungeon_map, x + 1, y - 1):   # NE floor → outer bottom-left corner
        return 24
    if _floor_at(dungeon_map, x - 1, y - 1):   # NW floor → outer bottom-right corner
        return 28
    return 0   # true interior — no adjacent room in any direction


def _make_shadow(ts: int, horizontal: bool) -> pygame.Surface:
    """Gradient strip for wall-cast shadows on adjacent floor tiles.

    horizontal=True  → dark at top, fades down   (wall to north)
    horizontal=False → dark at left, fades right  (wall to west)
    """
    surf = pygame.Surface((ts, ts), pygame.SRCALPHA)
    depth = 10
    for i in range(depth):
        alpha = int(85 * (1 - i / depth))
        if horizontal:
            surf.fill((0, 0, 0, alpha), (0, i, ts, 1))
        else:
            surf.fill((0, 0, 0, alpha), (i, 0, 1, ts))
    return surf


# ---------------------------------------------------------------------------
# TileRenderer
# ---------------------------------------------------------------------------

class TileRenderer:
    def __init__(self) -> None:
        self._sheet: SpriteSheet | None = None
        self._dark_overlay: pygame.Surface | None = None
        self._shadow_n: pygame.Surface | None = None
        self._shadow_w: pygame.Surface | None = None
        self._initialized = False

    def _init(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        ts = settings.TILE_SIZE

        self._dark_overlay = pygame.Surface((ts, ts), pygame.SRCALPHA)
        self._dark_overlay.fill((0, 0, 0, 170))

        self._shadow_n = _make_shadow(ts, horizontal=True)
        self._shadow_w = _make_shadow(ts, horizontal=False)

        path = os.path.join(_ASSETS_DIR, "tiles", "dithart_scifi.png")
        if os.path.exists(path):
            self._sheet = SpriteSheet(path, 32, 32)

    # ------------------------------------------------------------------
    # Public draw entry point
    # ------------------------------------------------------------------

    def draw(
        self,
        screen: pygame.Surface,
        dungeon_map: "DungeonMap",  # type: ignore[name-defined]
        camera: "Camera",           # type: ignore[name-defined]
    ) -> None:
        self._init()
        ts = settings.TILE_SIZE

        for y in range(dungeon_map.height):
            for x in range(dungeon_map.width):
                if not dungeon_map.explored[y, x]:
                    continue

                sx, sy = camera.world_to_screen(x, y)
                if sx > settings.SCREEN_WIDTH or sy > settings.SCREEN_HEIGHT:
                    continue
                if sx + ts < 0 or sy + ts < 0:
                    continue

                tile_type = dungeon_map.get_type(x, y)
                visible   = dungeon_map.visible[y, x]

                if tile_type == TileType.WALL:
                    self._draw_wall(screen, dungeon_map, x, y, sx, sy, visible)
                else:
                    self._draw_floor_tile(screen, dungeon_map, x, y, sx, sy,
                                          tile_type, visible)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _draw_wall(
        self,
        screen: pygame.Surface,
        dungeon_map: "DungeonMap",  # type: ignore[name-defined]
        x: int, y: int,
        sx: int, sy: int,
        visible: bool,
    ) -> None:
        if self._sheet is not None:
            # Floor underneath first — wall face tiles may have transparent areas
            self._sheet.blit_tile(screen, _TILE_INDEX[TileType.FLOOR], sx, sy)
            idx = _autotile_index(dungeon_map, x, y)
            self._sheet.blit_tile(screen, idx, sx, sy)
            if not visible:
                screen.blit(self._dark_overlay, (sx, sy))
        else:
            key = "wall" if visible else "wall_dark"
            screen.blit(procedural_sprites.get(key), (sx, sy))

    def _draw_floor_tile(
        self,
        screen: pygame.Surface,
        dungeon_map: "DungeonMap",  # type: ignore[name-defined]
        x: int, y: int,
        sx: int, sy: int,
        tile_type: TileType,
        visible: bool,
    ) -> None:
        tile_idx = _TILE_INDEX.get(tile_type)

        if tile_idx is not None and self._sheet is not None:
            self._sheet.blit_tile(screen, tile_idx, sx, sy)
            if not visible:
                screen.blit(self._dark_overlay, (sx, sy))
            else:
                self._blit_shadows(screen, dungeon_map, x, y, sx, sy)
        else:
            vis_col, drk_col = _RECT_COLOURS.get(
                tile_type, (settings.COL_FLOOR, settings.COL_FLOOR_DARK)
            )
            pygame.draw.rect(
                screen, vis_col if visible else drk_col,
                (sx, sy, settings.TILE_SIZE, settings.TILE_SIZE),
            )

    def _blit_shadows(
        self,
        screen: pygame.Surface,
        dungeon_map: "DungeonMap",  # type: ignore[name-defined]
        x: int, y: int,
        sx: int, sy: int,
    ) -> None:
        """Overlay wall-cast shadow gradients on a visible floor tile."""
        if y > 0 and dungeon_map.get_type(x, y - 1) == TileType.WALL:
            screen.blit(self._shadow_n, (sx, sy))
        if x > 0 and dungeon_map.get_type(x - 1, y) == TileType.WALL:
            screen.blit(self._shadow_w, (sx, sy))
