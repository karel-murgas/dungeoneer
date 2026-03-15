"""FOV computation using tcod shadowcasting."""
from __future__ import annotations

import numpy as np
import tcod

from dungeoneer.core.settings import FOV_RADIUS


def compute_fov(x: int, y: int, dungeon_map: "DungeonMap") -> None:  # type: ignore[name-defined]
    """Recompute the visible array for dungeon_map centred on (x, y)."""
    dungeon_map.visible[:] = tcod.map.compute_fov(
        dungeon_map.transparent,
        (y, x),           # tcod uses (row, col)
        radius=FOV_RADIUS,
        light_walls=True,
        algorithm=tcod.constants.FOV_SYMMETRIC_SHADOWCAST,
    )
    # Anything visible is now also explored
    dungeon_map.explored |= dungeon_map.visible
