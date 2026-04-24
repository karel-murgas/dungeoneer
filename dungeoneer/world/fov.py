"""FOV computation using tcod shadowcasting."""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import tcod

from dungeoneer.core.settings import FOV_RADIUS

if TYPE_CHECKING:
    from dungeoneer.world.room import Room


def compute_fov(
    x: int,
    y: int,
    dungeon_map: "DungeonMap",  # type: ignore[name-defined]
    rooms: "list[Room] | None" = None,
) -> None:
    """Recompute the visible array for dungeon_map centred on (x, y).

    If *rooms* is provided, any room whose inner tiles are newly visible fires
    a RoomRevealedEvent and is marked room.revealed = True.
    """
    dungeon_map.visible[:] = tcod.map.compute_fov(
        dungeon_map.transparent,
        (y, x),           # tcod uses (row, col)
        radius=FOV_RADIUS,
        light_walls=True,
        algorithm=tcod.constants.FOV_SYMMETRIC_SHADOWCAST,
    )
    # Anything visible is now also explored
    dungeon_map.explored |= dungeon_map.visible

    if rooms:
        from dungeoneer.core.event_bus import bus, RoomRevealedEvent
        for room in rooms:
            if room.revealed:
                continue
            iy, ih = room.inner_y, room.inner_h
            ix, iw = room.inner_x, room.inner_w
            if dungeon_map.visible[iy:iy + ih, ix:ix + iw].any():
                room.revealed = True
                bus.post(RoomRevealedEvent(room))
