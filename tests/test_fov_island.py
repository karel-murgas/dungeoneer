"""Regression test for the FOV 'island' bug.

Bug: with `tcod.constants.FOV_SYMMETRIC_SHADOWCAST` + `light_walls=True`, walls
can be marked visible *beyond* an unexplored gap — producing a small visible
patch (enemy + adjacent walls) with unexplored floor between it and the player.

Fix: world/fov.py now calls tcod with `light_walls=False` and lights walls
manually, only where they are 8-neighbours of a visible transparent tile.
"""
from __future__ import annotations

import numpy as np

from dungeoneer.core.settings import FOV_RADIUS
from dungeoneer.world.fov import compute_fov
from dungeoneer.world.map import DungeonMap
from dungeoneer.world.tile import TileType


def _bresenham(x0, y0, x1, y1):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        yield x, y
        if x == x1 and y == y1:
            return
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


def _count_islands(dmap: DungeonMap, px: int, py: int) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """A visible tile is an "island" if the Bresenham line from the player
    crosses an unexplored *floor* tile to reach it.
    """
    islands = []
    for ty in range(dmap.height):
        for tx in range(dmap.width):
            if not dmap.visible[ty, tx]:
                continue
            for ix, iy in _bresenham(px, py, tx, ty):
                if (ix, iy) == (px, py) or (ix, iy) == (tx, ty):
                    continue
                if dmap.get_type(ix, iy) == TileType.FLOOR and not dmap.visible[iy, ix]:
                    islands.append(((tx, ty), (ix, iy)))
                    break
    return islands


def test_no_islands_in_corridor_bend() -> None:
    """Layout matching the screenshot: top room, south corridor, east bend, bottom room."""
    dmap = DungeonMap(16, 18)
    for y in range(2, 6):
        for x in range(2, 8):
            dmap.set_type(x, y, TileType.FLOOR)
    for y in range(6, 11):
        dmap.set_type(7, y, TileType.FLOOR)
    for x in range(7, 12):
        dmap.set_type(x, 10, TileType.FLOOR)
    for y in range(10, 14):
        for x in range(11, 15):
            dmap.set_type(x, y, TileType.FLOOR)

    px, py = 4, 3
    compute_fov(px, py, dmap)

    islands = _count_islands(dmap, px, py)
    assert not islands, "FOV islands found:\n  " + "\n  ".join(
        f"visible {far} reached past unexplored floor {mid}" for far, mid in islands
    )


def test_walls_bordering_visible_floor_are_lit() -> None:
    """The fix must not regress: walls of a room you stand in still get lit."""
    dmap = DungeonMap(12, 12)
    for y in range(2, 7):
        for x in range(2, 7):
            dmap.set_type(x, y, TileType.FLOOR)

    compute_fov(4, 4, dmap)

    # Every wall on the room's perimeter must be visible.
    for x in (1, 7):
        for y in range(1, 8):
            assert dmap.visible[y, x], f"perimeter wall ({x},{y}) not lit"
    for y in (1, 7):
        for x in range(1, 8):
            assert dmap.visible[y, x], f"perimeter wall ({x},{y}) not lit"


def test_wall_slab_blocks_fov() -> None:
    """A wall slab between player and the rest of the room blocks visibility behind it."""
    dmap = DungeonMap(20, 15)
    for y in range(1, 14):
        for x in range(1, 19):
            dmap.set_type(x, y, TileType.FLOOR)
    for y in range(4, 9):
        dmap.set_type(8, y, TileType.WALL)

    compute_fov(4, 6, dmap)

    # Tiles directly behind the slab on the player's row must be invisible.
    for tx in (9, 10, 11, 12):
        assert not dmap.visible[6, tx], f"slab leak at ({tx},6)"


def test_radius_metric_documentation() -> None:
    """tcod uses Euclidean distance with strict <, so FOV_RADIUS=10 reaches
    9 tiles cardinally and 7 tiles diagonally. This test pins that behaviour
    so future radius changes are intentional.
    """
    dmap = DungeonMap(25, 25)
    for y in range(1, 24):
        for x in range(1, 24):
            dmap.set_type(x, y, TileType.FLOOR)
    px, py = 12, 12
    compute_fov(px, py, dmap)

    assert dmap.visible[py, px + 9] and not dmap.visible[py, px + 10], "cardinal radius"
    assert dmap.visible[py + 7, px + 7] and not dmap.visible[py + 8, px + 8], "diagonal radius"
