"""AI behaviour states."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from dungeoneer.entities.actor import Actor
    from dungeoneer.world.floor import Floor
    from dungeoneer.combat.action import Action


class BehaviorState(ABC):
    @abstractmethod
    def execute(self, owner: "Actor", floor: "Floor") -> Optional["Action"]: ...


# ---------------------------------------------------------------------------
# Idle — stands still, reacts if player enters perception range
# ---------------------------------------------------------------------------

class IdleState(BehaviorState):
    def execute(self, owner: "Actor", floor: "Floor") -> Optional["Action"]:
        from dungeoneer.ai.perception import can_see
        from dungeoneer.entities.player import Player
        from dungeoneer.combat.action import WaitAction

        player = next((a for a in floor.actors if isinstance(a, Player)), None)
        if player and can_see(owner.x, owner.y, player.x, player.y, floor.dungeon_map):
            owner.ai_brain.set_state(CombatState())
            return owner.ai_brain.current_state.execute(owner, floor)

        return WaitAction()


# ---------------------------------------------------------------------------
# Combat — chase and attack the player
# ---------------------------------------------------------------------------

class CombatState(BehaviorState):
    def execute(self, owner: "Actor", floor: "Floor") -> Optional["Action"]:
        from dungeoneer.entities.player import Player
        from dungeoneer.combat.action import (
            MoveAction, MeleeAttackAction, RangedAttackAction, WaitAction
        )
        from dungeoneer.core.settings import DRONE_PREFERRED_DIST

        player = next((a for a in floor.actors if isinstance(a, Player) and a.alive), None)
        if player is None:
            owner.ai_brain.set_state(IdleState())
            return WaitAction()

        dist = abs(owner.x - player.x) + abs(owner.y - player.y)
        is_drone = getattr(owner, "is_drone", False)

        if is_drone:
            return self._drone_action(owner, player, floor, dist, DRONE_PREFERRED_DIST)
        else:
            return self._guard_action(owner, player, floor, dist)

    def _guard_action(self, owner, player, floor, dist) -> "Action":
        from dungeoneer.combat.action import MoveAction, MeleeAttackAction, WaitAction

        # Adjacent — attack
        if dist == 1 or (abs(owner.x - player.x) <= 1 and abs(owner.y - player.y) <= 1 and dist > 0):
            return MeleeAttackAction(player)

        # Path toward player
        return self._step_toward(owner, player, floor) or WaitAction()

    def _drone_action(self, owner, player, floor, dist, preferred_dist) -> "Action":
        from dungeoneer.combat.action import (
            MoveAction, RangedAttackAction, WaitAction
        )
        from dungeoneer.combat.line_of_sight import has_los

        has_line = has_los(owner.x, owner.y, player.x, player.y, floor.dungeon_map)

        if has_line and dist <= 8:
            if dist < preferred_dist:
                # Too close — try to back away
                step = self._step_away(owner, player, floor)
                if step:
                    return step
            return RangedAttackAction(player, max_range=8)

        # No LOS or out of range — move toward player
        return self._step_toward(owner, player, floor) or WaitAction()

    def _step_toward(self, owner, player, floor) -> Optional["Action"]:
        from dungeoneer.ai.pathfinder import Pathfinder
        from dungeoneer.combat.action import MoveAction

        path = Pathfinder().find_path(
            (owner.x, owner.y), (player.x, player.y), floor.dungeon_map
        )
        if not path:
            return None
        nx, ny = path[0]
        if floor.get_actor_at(nx, ny) is None and floor.get_container_at(nx, ny) is None:
            return MoveAction(nx - owner.x, ny - owner.y)
        return None

    def _step_away(self, owner, player, floor) -> Optional["Action"]:
        from dungeoneer.combat.action import MoveAction

        dx = owner.x - player.x
        dy = owner.y - player.y
        # Normalise
        sdx = (1 if dx > 0 else -1) if dx != 0 else 0
        sdy = (1 if dy > 0 else -1) if dy != 0 else 0
        for ddx, ddy in [(sdx, sdy), (sdx, 0), (0, sdy)]:
            if ddx == 0 and ddy == 0:
                continue
            nx, ny = owner.x + ddx, owner.y + ddy
            if (floor.dungeon_map.is_walkable(nx, ny)
                    and floor.get_actor_at(nx, ny) is None
                    and floor.get_container_at(nx, ny) is None):
                return MoveAction(ddx, ddy)
        return None
