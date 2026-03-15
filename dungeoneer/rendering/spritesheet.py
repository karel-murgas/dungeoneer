"""SpriteSheet: loads a grid-based sprite sheet and exposes individual tiles."""
from __future__ import annotations

import pygame


class SpriteSheet:
    """Loads a grid sprite sheet and exposes tiles by 0-based index.

    Tiles are laid out left-to-right, top-to-bottom. Index 0 is top-left.
    """

    def __init__(self, path: str, tile_w: int, tile_h: int) -> None:
        self._sheet = pygame.image.load(path).convert_alpha()
        self._tw = tile_w
        self._th = tile_h
        self._cols = self._sheet.get_width() // tile_w

    def blit_tile(
        self,
        dest: pygame.Surface,
        index: int,
        dest_x: int,
        dest_y: int,
    ) -> None:
        """Blit the tile at *index* onto *dest* at (dest_x, dest_y)."""
        col = index % self._cols
        row = index // self._cols
        src_rect = pygame.Rect(col * self._tw, row * self._th, self._tw, self._th)
        dest.blit(self._sheet, (dest_x, dest_y), src_rect)

    def get_tile_surface(self, index: int) -> pygame.Surface:
        """Return a new RGBA Surface containing the tile at *index*."""
        surf = pygame.Surface((self._tw, self._th), pygame.SRCALPHA)
        self.blit_tile(surf, index, 0, 0)
        return surf
