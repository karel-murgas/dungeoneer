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

    Implementation note — *no light_walls*. tcod's `light_walls=True` combined
    with FOV_SYMMETRIC_SHADOWCAST lights walls along the algorithm's internal
    shadow-ray, which can mark walls visible *beyond* an unexplored gap (the
    "island" bug — a visible enemy/wall patch with unexplored floor between).
    We therefore compute the FOV against transparent tiles only, and then light
    walls ourselves *only* where they are 4-/8-neighbours of a visible floor.
    """
    floor_visible = tcod.map.compute_fov(
        dungeon_map.transparent,
        (y, x),           # tcod uses (row, col)
        radius=FOV_RADIUS,
        light_walls=False,
        algorithm=tcod.constants.FOV_SYMMETRIC_SHADOWCAST,
    )

    # Light opaque tiles (walls, closed doors, closed elevators) that border a
    # visible transparent tile, so the player can see the inside faces of the
    # rooms / corridors they are standing in.
    opaque = ~dungeon_map.transparent
    border = np.zeros_like(floor_visible)
    border[1:,  :] |= floor_visible[:-1, :]   # tile above is visible
    border[:-1, :] |= floor_visible[1:,  :]   # below
    border[:,  1:] |= floor_visible[:, :-1]   # left
    border[:, :-1] |= floor_visible[:, 1:]    # right
    border[1:,  1:] |= floor_visible[:-1, :-1]
    border[1:, :-1] |= floor_visible[:-1, 1:]
    border[:-1, 1:] |= floor_visible[1:,  :-1]
    border[:-1,:-1] |= floor_visible[1:,  1:]

    dungeon_map.visible[:] = floor_visible | (opaque & border)
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
