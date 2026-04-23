"""Dynamic encounter spawning system.

Subscribes to RoomRevealedEvent and populates rooms with enemies using a
"pack vs elite" model parameterised by the current heat level.
Replaces the static enemy distribution that previously ran in dungeon_generator.
"""
from __future__ import annotations

import random
from typing import TYPE_CHECKING

from dungeoneer.core.event_bus import bus, RoomRevealedEvent
from dungeoneer.core import settings
from dungeoneer.world.dungeon_generator import _ENEMY_POOL
from dungeoneer.entities.enemy import (
    make_guard, make_drone, make_dog,
    make_heavy, make_turret, make_sniper_drone, make_riot_guard,
)
from dungeoneer.items.item import RangeType

if TYPE_CHECKING:
    from dungeoneer.world.floor import Floor
    from dungeoneer.world.room import Room
    from dungeoneer.systems.heat import HeatSystem
    from dungeoneer.core.difficulty import Difficulty
    from dungeoneer.combat.turn_manager import TurnManager
    from dungeoneer.entities.enemy import Enemy

_FACTORIES = {
    "guard":        make_guard,
    "drone":        make_drone,
    "dog":          make_dog,
    "heavy":        make_heavy,
    "turret":       make_turret,
    "sniper_drone": make_sniper_drone,
    "riot_guard":   make_riot_guard,
}

# Max enemy tier per heat level (mirrors systems/heat._TIER_CAP)
_TIER_CAP = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3}


class EncounterSystem:
    def __init__(
        self,
        floor: "Floor",
        heat_system: "HeatSystem",
        difficulty: "Difficulty",
        end_room: "Room | None",
        turn_manager: "TurnManager",
    ) -> None:
        self._floor        = floor
        self._heat_system  = heat_system
        self._difficulty   = difficulty
        self._end_room     = end_room
        self._turn_manager = turn_manager
        bus.subscribe(RoomRevealedEvent, self.on_room_revealed)

    def teardown(self) -> None:
        try:
            bus.unsubscribe(RoomRevealedEvent, self.on_room_revealed)
        except (KeyError, ValueError):
            pass

    # ------------------------------------------------------------------
    # Room reveal handler
    # ------------------------------------------------------------------

    def on_room_revealed(self, event: RoomRevealedEvent) -> None:
        room = event.room
        if room is self._end_room:
            self._spawn_encounter_in_room(room)
            return
        if room.inner_w * room.inner_h < settings.ENCOUNTER_MIN_ROOM_AREA:
            return
        if random.random() < self._difficulty.empty_room_chance:
            return
        self._spawn_encounter_in_room(room)

    def _spawn_encounter_in_room(self, room: "Room") -> None:
        from dungeoneer.ai.states import IdleState
        enemies = self._generate_encounter()
        if not enemies:
            return
        occupied: set[tuple[int, int]] = {(a.x, a.y) for a in self._floor.actors}
        for enemy in enemies:
            pos = self._pick_room_pos(room, occupied)
            if pos is None:
                continue
            enemy.x, enemy.y = pos
            occupied.add(pos)
            enemy.ai_brain.set_state(IdleState())
            self._floor.add_actor(enemy)
        self._turn_manager.build_queue(self._floor)

    def _pick_room_pos(
        self,
        room: "Room",
        occupied: set[tuple[int, int]],
        max_tries: int = 20,
    ) -> tuple[int, int] | None:
        for _ in range(max_tries):
            pos = room.random_inner_point()
            if pos not in occupied and self._floor.dungeon_map.is_walkable(*pos):
                return pos
        return None

    # ------------------------------------------------------------------
    # Patrol spawn (heat level-up)
    # ------------------------------------------------------------------

    def spawn_patrol(self, near_x: int, near_y: int) -> None:
        enemies = self._generate_encounter()
        for enemy in enemies:
            pos = self._find_patrol_pos(near_x, near_y)
            if pos is None:
                continue
            enemy.x, enemy.y = pos
            from dungeoneer.ai.states import CombatState
            enemy.ai_brain.set_state(CombatState())
            self._floor.add_actor(enemy)
        self._turn_manager.build_queue(self._floor)

    def _find_patrol_pos(
        self, near_x: int, near_y: int
    ) -> tuple[int, int] | None:
        from dungeoneer.combat.line_of_sight import has_los
        dm = self._floor.dungeon_map
        candidates: list[tuple[int, int]] = []
        for dy in range(-9, 10):
            for dx in range(-9, 10):
                tx, ty = near_x + dx, near_y + dy
                dist = abs(dx) + abs(dy)
                if dist < 4 or dist > 9:
                    continue
                if not dm.in_bounds(tx, ty) or not dm.is_walkable(tx, ty):
                    continue
                if self._floor.get_actor_at(tx, ty) is not None:
                    continue
                candidates.append((tx, ty))
        if not candidates:
            return None
        los_cands = [(x, y) for x, y in candidates if has_los(x, y, near_x, near_y, dm)]
        pool = los_cands if los_cands else candidates
        return random.choice(pool)

    # ------------------------------------------------------------------
    # Encounter generation — "pack vs elite" model
    # ------------------------------------------------------------------

    def _generate_encounter(self) -> list["Enemy"]:
        heat_level = self._heat_system.level
        max_tier   = self._compute_max_tier(heat_level)

        if max_tier == 1 or random.random() < settings.ENCOUNTER_PACK_CHANCE:
            enemies = self._make_pack(heat_level)
        else:
            enemies = self._make_elite(heat_level, max_tier)

        self._apply_ranged_cap(enemies)
        return enemies

    def _compute_max_tier(self, heat_level: int) -> int:
        base = _TIER_CAP[heat_level]
        if heat_level == 4 and random.random() < settings.ENCOUNTER_T3_CHANCE_AT_H4:
            return 3
        return base

    def _make_pack(self, heat_level: int) -> list["Enemy"]:
        if heat_level <= 1:
            size = 1
        elif heat_level == 2:
            size = random.randint(1, 2)
        elif heat_level == 3:
            size = random.randint(2, 3)
        elif heat_level == 4:
            size = 3
        else:
            size = random.randint(3, 4)
        return [self._make_enemy(1) for _ in range(size)]

    def _make_elite(self, heat_level: int, max_tier: int) -> list["Enemy"]:
        enemies = [self._make_enemy(max_tier)]
        if max_tier == 3:
            if heat_level >= 5 and random.random() < 0.5:
                enemies.append(self._make_enemy(1))
        else:  # max_tier == 2
            count = random.randint(1, 2) if heat_level >= 4 else random.randint(0, 1)
            enemies += [self._make_enemy(1) for _ in range(count)]
        return enemies

    def _make_enemy(self, tier: int) -> "Enemy":
        pool = _ENEMY_POOL.get(tier, _ENEMY_POOL[1])
        return _FACTORIES[random.choice(pool)](0, 0)

    def _apply_ranged_cap(self, enemies: list["Enemy"]) -> None:
        ranged_count = sum(
            1 for e in enemies
            if e.equipped_weapon and e.equipped_weapon.range_type == RangeType.RANGED
        )
        for i in range(len(enemies) - 1, -1, -1):
            if ranged_count <= 2:
                break
            e = enemies[i]
            if e.equipped_weapon and e.equipped_weapon.range_type == RangeType.RANGED:
                replacement = self._make_melee_enemy()
                enemies[i] = replacement
                ranged_count -= 1

    def _make_melee_enemy(self, max_tries: int = 20) -> "Enemy":
        for _ in range(max_tries):
            candidate = self._make_enemy(1)
            if not candidate.equipped_weapon or candidate.equipped_weapon.range_type != RangeType.RANGED:
                return candidate
        return _FACTORIES["guard"](0, 0)
