"""TileRenderer: draws map tiles using Dithart sci-fi sprites with FOV shading.

Tile index mapping for tileset_for_free.png (8 cols × 15 rows, 32×32, 0-indexed).
Indices verified by pixel-matching against godot_minimal_3x3_autotile.png.

  FLOOR      → 112   (row 14 col 0)  plain sci-fi floor
  STAIR_DOWN → 47    (row  5 col 7)  hatch/stair
  DOOR       → 40    (row  5 col 0)  door

Wall autotile — 8-bit neighbour mask:
  bit0=N  bit1=S  bit2=W  bit3=E  bit4=NW  bit5=NE  bit6=SW  bit7=SE
  Value 1 = floor neighbour, 0 = wall neighbour.

The primary lookup table (_WALL_AUTOTILE_8BIT) covers all 47 autotile positions
from the Godot minimal-3×3 template (pixel-matched against the tileset).
Diagonal context distinguishes variants of the same cardinal face — e.g. a
south-face wall (N floor) looks different when another room also touches the
SW or SE diagonal.

For rare 8-bit masks not in the table the code falls back to the 15-entry
4-bit cardinal table (_WALL_AUTOTILE), which is always a reasonable approximation.

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
# Wall autotile — 8-bit full-neighbour table
# Derived by pixel-matching godot_minimal_3x3_autotile.png against tileset.
# bit0=N, bit1=S, bit2=W, bit3=E, bit4=NW, bit5=NE, bit6=SW, bit7=SE (1=floor)
# ---------------------------------------------------------------------------
_WALL_AUTOTILE_8BIT: dict[int, int] = {
    # ── No cardinal floor (outer corners / true interior) ──────────────────
    0b00000000:  0,  # all walls — true interior block
    0b00010000: 28,  # NW floor only
    0b00100000: 24,  # NE floor only
    0b01000000:  3,  # SW floor only
    0b10000000:  1,  # SE floor only
    0b00110000: 30,  # NW+NE
    0b01010000: 14,  # NW+SW
    0b10010000: 71,  # NW+SE
    0b01100000: 63,  # NE+SW
    0b10100000: 13,  # NE+SE
    0b11000000: 22,  # SW+SE
    0b01110000: 70,  # NW+NE+SW
    0b10110000: 67,  # NW+NE+SE
    0b11010000: 60,  # NW+SW+SE
    0b11100000: 59,  # NE+SW+SE
    0b11110000:  4,  # all 4 diagonals

    # ── N floor only ────────────────────────────────────────────────────────
    0b00110001: 42,  # + NW+NE          (standard south-face wall)
    0b01110001: 51,  # + NW+NE+SW
    0b10110001: 52,  # + NW+NE+SE
    0b11110001: 48,  # + all diagonals

    # ── S floor only ────────────────────────────────────────────────────────
    0b11000010: 88,  # + SW+SE          (standard north-face wall)
    0b11010010: 68,  # + NW+SW+SE
    0b11100010: 69,  # + NE+SW+SE
    0b11110010: 65,  # + all diagonals

    # ── W floor only ────────────────────────────────────────────────────────
    0b01010100: 20,  # + NW+SW          (standard east-face wall)
    0b01110100: 57,  # + NW+NE+SW
    0b11010100: 50,  # + NW+SW+SE
    0b11110100: 56,  # + all diagonals

    # ── E floor only ────────────────────────────────────────────────────────
    0b10101000: 16,  # + NE+SE          (standard west-face wall)
    0b10111000: 58,  # + NW+NE+SE
    0b11101000: 49,  # + NE+SW+SE
    0b11111000: 55,  # + all diagonals

    # ── N+W floor ───────────────────────────────────────────────────────────
    0b01110101: 27,  # + NW+NE+SW  (SE=wall — classic inner NW corner)
    0b11110101: 53,  # + all diagonals

    # ── N+E floor ───────────────────────────────────────────────────────────
    0b10111001: 25,  # + NW+NE+SE  (SW=wall — classic inner NE corner)
    0b11111001: 54,  # + all diagonals

    # ── S+W floor ───────────────────────────────────────────────────────────
    0b11010110: 11,  # + NW+SW+SE  (NE=wall — classic inner SW corner)
    0b11110110: 64,  # + all diagonals

    # ── S+E floor ───────────────────────────────────────────────────────────
    0b11101010:  9,  # + NE+SW+SE  (NW=wall — classic inner SE corner)
    0b11111010: 66,  # + all diagonals

    # ── Opposite-face corridors ──────────────────────────────────────────────
    0b11110011:  6,  # N+S + all diagonals  (EW corridor)
    0b11111100: 23,  # W+E + all diagonals  (NS corridor)

    # ── T-junctions / end caps ──────────────────────────────────────────────
    0b11110111:  5,  # N+S+W + all diagonals  (W cap)
    0b11111011:  7,  # N+S+E + all diagonals  (E cap)
    0b11111101: 15,  # N+W+E + all diagonals  (N cap)
    0b11111110: 31,  # S+W+E + all diagonals  (S cap)

    # ── Isolated pillar ─────────────────────────────────────────────────────
    0b11111111: 21,  # all floor neighbours
}

# Fallback: 4-bit cardinal mask for 8-bit masks not listed above.
# bit0=N, bit1=S, bit2=W, bit3=E  (1 = floor neighbour)
_WALL_AUTOTILE: dict[int, int] = {
    0b0001: 42,   # N
    0b0010: 88,   # S
    0b0100: 20,   # W
    0b1000: 16,   # E
    0b0101: 27,   # N+W
    0b1001: 25,   # N+E
    0b0110: 11,   # S+W
    0b1010:  9,   # S+E
    0b0011:  6,   # N+S
    0b1100: 23,   # E+W
    0b0111:  5,   # N+S+W
    0b1011:  7,   # N+S+E
    0b1101: 15,   # N+W+E
    0b1110: 31,   # S+W+E
    0b1111: 21,   # all cardinals
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

    Computes an 8-bit neighbour mask (cardinals + diagonals) and looks it up
    in _WALL_AUTOTILE_8BIT.  Falls back to the 4-bit cardinal table for any
    mask not explicitly listed.
    """
    n  = _floor_at(dungeon_map, x,     y - 1)
    s  = _floor_at(dungeon_map, x,     y + 1)
    w  = _floor_at(dungeon_map, x - 1, y    )
    e  = _floor_at(dungeon_map, x + 1, y    )
    nw = _floor_at(dungeon_map, x - 1, y - 1)
    ne = _floor_at(dungeon_map, x + 1, y - 1)
    sw = _floor_at(dungeon_map, x - 1, y + 1)
    se = _floor_at(dungeon_map, x + 1, y + 1)

    mask8 = (n       | (s  << 1) | (w  << 2) | (e  << 3)
             | (nw << 4) | (ne << 5) | (sw << 6) | (se << 7))

    if mask8 in _WALL_AUTOTILE_8BIT:
        return _WALL_AUTOTILE_8BIT[mask8]

    # Fallback for unlisted diagonal combinations — use cardinal bits only.
    return _WALL_AUTOTILE.get(n | (s << 1) | (w << 2) | (e << 3), 0)


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
