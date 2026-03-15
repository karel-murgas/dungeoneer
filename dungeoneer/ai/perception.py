"""Perception helpers — can an actor see/hear another?"""
from __future__ import annotations

from dungeoneer.combat.line_of_sight import has_los
from dungeoneer.world.map import DungeonMap


def can_see(
    observer_x: int, observer_y: int,
    target_x: int, target_y: int,
    dungeon_map: DungeonMap,
    radius: int = 12,
) -> bool:
    dist = abs(observer_x - target_x) + abs(observer_y - target_y)
    if dist > radius:
        return False
    return has_los(observer_x, observer_y, target_x, target_y, dungeon_map)
