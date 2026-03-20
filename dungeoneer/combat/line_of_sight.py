"""Shadowcast line-of-sight check — consistent with player FOV."""
from __future__ import annotations

import tcod

from dungeoneer.world.map import DungeonMap


def has_los(x0: int, y0: int, x1: int, y1: int, dungeon_map: DungeonMap) -> bool:
    """Return True if (x1,y1) is visible from (x0,y0) using symmetric shadowcasting.

    Uses the same FOV_SYMMETRIC_SHADOWCAST algorithm as the player FOV so that
    'visible on screen' and 'valid LOS for shooting / enemy sight' are identical.
    radius=0 means unlimited range (range limits are enforced by callers).
    """
    visible = tcod.map.compute_fov(
        dungeon_map.transparent,
        (y0, x0),
        radius=0,
        light_walls=True,
        algorithm=tcod.constants.FOV_SYMMETRIC_SHADOWCAST,
    )
    return bool(visible[y1, x1])
