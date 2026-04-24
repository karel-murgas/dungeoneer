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
    # The observer's own tile is forced transparent so that actors standing on
    # an opaque-but-walkable tile (e.g. a door) can still see out. Shadowcast
    # cannot propagate FOV from an opaque origin, which would otherwise leave
    # the observer blind to everything including adjacent tiles.
    transparent = dungeon_map.transparent
    if not transparent[y0, x0]:
        transparent = transparent.copy()
        transparent[y0, x0] = True
    visible = tcod.map.compute_fov(
        transparent,
        (y0, x0),
        radius=0,
        light_walls=True,
        algorithm=tcod.constants.FOV_SYMMETRIC_SHADOWCAST,
    )
    return bool(visible[y1, x1])
