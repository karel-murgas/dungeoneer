"""TileRenderer: draws map tiles using Dithart sci-fi sprites with FOV shading.

Tile index mapping for dithart_scifi.png (8 cols × 15 rows, 32×32 each, 0-indexed):
  FLOOR      → 112  (row 14, col 0)  — main sci-fi floor
  STAIR_DOWN → 47   (row  5, col 7)  — hatch / stair tile
  DOOR       → 40   (row  5, col 0)  — door tile
  WALL       → None (colored rect fallback — no solid block sprite in this set)

Adjust the indices above if you want to swap tiles after inspecting the sheet.
"""
from __future__ import annotations

import os

import pygame

from dungeoneer.core import settings
from dungeoneer.world.tile import TileType
from dungeoneer.rendering.spritesheet import SpriteSheet
from dungeoneer.rendering import procedural_sprites

# ---------------------------------------------------------------------------
# Tile index map: TileType → index in dithart_scifi.png (None = proc. sprite)
# ---------------------------------------------------------------------------
_TILE_INDEX: dict[TileType, int | None] = {
    TileType.WALL:       None,   # procedural metal-panel sprite
    TileType.FLOOR:      112,    # row 14, col 0
    TileType.STAIR_DOWN: 47,     # row  5, col 7
    TileType.DOOR:       40,     # row  5, col 0
}

# Rect-colour fallback used only when the spritesheet itself is missing
_RECT_COLOURS: dict[TileType, tuple[tuple, tuple]] = {
    TileType.WALL:       (settings.COL_WALL,  settings.COL_WALL_DARK),
    TileType.FLOOR:      (settings.COL_FLOOR, settings.COL_FLOOR_DARK),
    TileType.STAIR_DOWN: (settings.COL_STAIR, settings.COL_STAIR_DARK),
    TileType.DOOR:       (settings.COL_FLOOR, settings.COL_FLOOR_DARK),
}

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")


class TileRenderer:
    def __init__(self) -> None:
        self._sheet: SpriteSheet | None = None
        self._dark_overlay: pygame.Surface | None = None
        self._initialized = False

    def _init(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        # Dark overlay for explored-but-not-visible tiles
        ts = settings.TILE_SIZE
        self._dark_overlay = pygame.Surface((ts, ts), pygame.SRCALPHA)
        self._dark_overlay.fill((0, 0, 0, 170))
        # Sprite sheet (optional — graceful fallback if file missing)
        path = os.path.join(_ASSETS_DIR, "tiles", "dithart_scifi.png")
        if os.path.exists(path):
            self._sheet = SpriteSheet(path, 32, 32)

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
                visible = dungeon_map.visible[y, x]
                tile_index = _TILE_INDEX.get(tile_type)

                if tile_index is not None and self._sheet is not None:
                    # Dithart sprite sheet tile
                    self._sheet.blit_tile(screen, tile_index, sx, sy)
                    if not visible:
                        screen.blit(self._dark_overlay, (sx, sy))
                elif tile_type == TileType.WALL:
                    # Procedural metal-panel wall sprite
                    key = "wall" if visible else "wall_dark"
                    screen.blit(procedural_sprites.get(key), (sx, sy))
                else:
                    # Pure rect fallback (only if spritesheet file is missing)
                    vis_col, dark_col = _RECT_COLOURS.get(
                        tile_type, (settings.COL_FLOOR, settings.COL_FLOOR_DARK)
                    )
                    colour = vis_col if visible else dark_col
                    pygame.draw.rect(screen, colour, (sx, sy, ts, ts))
