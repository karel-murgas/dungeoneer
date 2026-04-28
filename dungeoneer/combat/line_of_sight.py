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
    # light_walls=False — we only need to know whether the *target* tile is
    # reachable; lighting walls along the shadowcast ray would mark distant
    # walls visible beyond unexplored space (the FOV "island" bug fixed in
    # world/fov.py). For has_los the target's transparency does not matter:
    # if the target is opaque (e.g. an enemy on a closed door), tcod still
    # returns True for the target tile when the line is clear up to it.
    visible = tcod.map.compute_fov(
        transparent,
        (y0, x0),
        radius=0,
        light_walls=False,
        algorithm=tcod.constants.FOV_SYMMETRIC_SHADOWCAST,
    )
    if visible[y1, x1]:
        return True
    # Target may be an opaque tile that light_walls would have lit; explicitly
    # check if any 8-neighbour visible transparent tile borders it.
    if not transparent[y1, x1]:
        for ny in (y1 - 1, y1, y1 + 1):
            for nx in (x1 - 1, x1, x1 + 1):
                if (nx, ny) == (x1, y1):
                    continue
                if 0 <= ny < visible.shape[0] and 0 <= nx < visible.shape[1]:
                    if visible[ny, nx] and transparent[ny, nx]:
                        return True
    return False
