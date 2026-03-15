"""Camera: world-to-screen coordinate transform."""
from __future__ import annotations

from dungeoneer.core import settings


class Camera:
    def __init__(self) -> None:
        self.offset_x = 0  # pixels
        self.offset_y = 0

    def center_on(self, wx: int, wy: int, map_width: int, map_height: int) -> None:
        """Snap camera so (wx, wy) is centred on screen."""
        ts = settings.TILE_SIZE
        target_x = wx * ts - settings.SCREEN_WIDTH  // 2
        target_y = wy * ts - settings.SCREEN_HEIGHT // 2
        max_x = map_width  * ts - settings.SCREEN_WIDTH
        max_y = map_height * ts - settings.SCREEN_HEIGHT
        self.offset_x = max(0, min(target_x, max_x))
        self.offset_y = max(0, min(target_y, max_y))

    def world_to_screen(self, wx: int, wy: int) -> tuple[int, int]:
        ts = settings.TILE_SIZE
        return (wx * ts - self.offset_x, wy * ts - self.offset_y)

    def screen_to_world(self, sx: int, sy: int) -> tuple[int, int]:
        ts = settings.TILE_SIZE
        return ((sx + self.offset_x) // ts, (sy + self.offset_y) // ts)

    def is_on_screen(self, wx: int, wy: int) -> bool:
        sx, sy = self.world_to_screen(wx, wy)
        ts = settings.TILE_SIZE
        return (
            -ts < sx < settings.SCREEN_WIDTH + ts
            and -ts < sy < settings.SCREEN_HEIGHT + ts
        )
