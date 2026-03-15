"""Bresenham line-of-sight check."""
from __future__ import annotations

from dungeoneer.world.map import DungeonMap


def has_los(x0: int, y0: int, x1: int, y1: int, dungeon_map: DungeonMap) -> bool:
    """Return True if there is unobstructed LOS from (x0,y0) to (x1,y1).

    Uses Bresenham's line algorithm, checking transparency of intermediate tiles.
    """
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    cx, cy = x0, y0

    while True:
        if cx == x1 and cy == y1:
            return True
        # Block LOS on non-transparent tiles (except origin)
        if (cx != x0 or cy != y0) and not dungeon_map.is_transparent(cx, cy):
            return False
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            cx += sx
        if e2 < dx:
            err += dx
            cy += sy
