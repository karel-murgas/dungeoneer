"""AI behaviour states."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from dungeoneer.entities.actor import Actor
    from dungeoneer.world.floor import Floor
    from dungeoneer.combat.action import Action

_SEARCH_MAX_TURNS = 8  # turns before giving up and returning to Idle


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
        from dungeoneer.combat.action import WaitAction
        from dungeoneer.core.settings import DRONE_PREFERRED_DIST

        player = next((a for a in floor.actors if isinstance(a, Player) and a.alive), None)
        if player is None:
            owner.ai_brain.set_state(IdleState())
            return WaitAction()

        dist = abs(owner.x - player.x) + abs(owner.y - player.y)

        can_move = getattr(owner, "can_move", True)
        if not can_move:
            return self._turret_action(owner, player, floor, dist)

        is_drone = getattr(owner, "is_drone", False)
        if is_drone:
            raw_pref = getattr(owner, "preferred_dist", 0)
            preferred_dist = raw_pref if raw_pref > 0 else DRONE_PREFERRED_DIST
            return self._drone_action(owner, player, floor, dist, preferred_dist)
        else:
            return self._guard_action(owner, player, floor, dist)

    def _guard_action(self, owner, player, floor, dist) -> "Action":
        from dungeoneer.combat.action import MoveAction, MeleeAttackAction, WaitAction

        # Adjacent — attack
        if dist == 1:
            return MeleeAttackAction(player)

        # Path toward player
        return self._step_toward(owner, player, floor) or WaitAction()

    def _turret_action(self, owner, player, floor, dist) -> "Action":
        from dungeoneer.combat.action import RangedAttackAction, WaitAction
        from dungeoneer.combat.line_of_sight import has_los

        weapon_range = getattr(getattr(owner, 'equipped_weapon', None), 'range_tiles', 8)
        has_line = has_los(owner.x, owner.y, player.x, player.y, floor.dungeon_map)
        if has_line and dist <= weapon_range:
            return RangedAttackAction(player, max_range=weapon_range)
        # Lost sight — return to idle (turrets don't pursue)
        owner.ai_brain.set_state(IdleState())
        return WaitAction()

    def _drone_action(self, owner, player, floor, dist, preferred_dist) -> "Action":
        from dungeoneer.combat.action import RangedAttackAction, WaitAction
        from dungeoneer.combat.line_of_sight import has_los

        weapon_range = getattr(getattr(owner, 'equipped_weapon', None), 'range_tiles', 8)
        always_retreat     = getattr(owner, 'always_retreat', False)
        retreat_when_close = getattr(owner, 'retreat_when_close', True)

        # Read and clear the "was shot at" flag set by ActionResolver.
        was_shot_at = getattr(owner, 'was_shot_at', False)
        owner.was_shot_at = False

        # Only flee when the player is actively closing in (for normal drones).
        prev_dist = getattr(self, '_prev_dist', dist)
        self._prev_dist = dist
        player_approaching = dist < prev_dist

        has_line = has_los(owner.x, owner.y, player.x, player.y, floor.dungeon_map)

        if has_line and dist <= weapon_range:
            retreat = (
                dist < preferred_dist
                and (always_retreat or (retreat_when_close and not was_shot_at and player_approaching))
            )
            if retreat:
                step = self._step_away(owner, player, floor)
                if step:
                    return step
            return RangedAttackAction(player, max_range=weapon_range)

        # No LOS or out of range — move toward player
        return self._step_toward(owner, player, floor) or WaitAction()

    def _step_toward(self, owner, player, floor) -> Optional["Action"]:
        from dungeoneer.ai.pathfinder import Pathfinder
        from dungeoneer.combat.action import MoveAction

        blocked = [(c.x, c.y) for c in floor.containers if not c.opened]
        path = Pathfinder().find_path(
            (owner.x, owner.y), (player.x, player.y), floor.dungeon_map,
            extra_blocked=blocked,
        )
        if not path:
            return None
        nx, ny = path[0]
        if floor.get_actor_at(nx, ny) is None:
            return MoveAction(nx - owner.x, ny - owner.y)
        return None

    def _step_toward_tile(self, owner, tx: int, ty: int, floor) -> Optional["Action"]:
        """Pathfind toward an arbitrary tile (not necessarily the player)."""
        from dungeoneer.ai.pathfinder import Pathfinder
        from dungeoneer.combat.action import MoveAction

        blocked = [(c.x, c.y) for c in floor.containers if not c.opened]
        path = Pathfinder().find_path(
            (owner.x, owner.y), (tx, ty), floor.dungeon_map,
            extra_blocked=blocked,
        )
        if not path:
            return None
        nx, ny = path[0]
        if floor.get_actor_at(nx, ny) is None:
            return MoveAction(nx - owner.x, ny - owner.y)
        return None

    def _step_away(self, owner, player, floor) -> Optional["Action"]:
        from dungeoneer.combat.action import MoveAction

        dx = owner.x - player.x
        dy = owner.y - player.y
        # Normalise
        sdx = (1 if dx > 0 else -1) if dx != 0 else 0
        sdy = (1 if dy > 0 else -1) if dy != 0 else 0
        for ddx, ddy in [(sdx, 0), (0, sdy)]:
            if ddx == 0 and ddy == 0:
                continue
            nx, ny = owner.x + ddx, owner.y + ddy
            if (floor.dungeon_map.is_walkable(nx, ny)
                    and floor.get_actor_at(nx, ny) is None
                    and floor.get_container_at(nx, ny) is None):
                return MoveAction(ddx, ddy)
        return None


# ---------------------------------------------------------------------------
# Search — enemy was hit but couldn't see attacker; investigates last known pos
# ---------------------------------------------------------------------------

class SearchState(BehaviorState):
    def __init__(self, last_x: int, last_y: int) -> None:
        self.last_x = last_x
        self.last_y = last_y
        self._turns_left = _SEARCH_MAX_TURNS

    def execute(self, owner: "Actor", floor: "Floor") -> Optional["Action"]:
        from dungeoneer.ai.perception import can_see
        from dungeoneer.entities.player import Player
        from dungeoneer.combat.action import WaitAction

        player = next((a for a in floor.actors if isinstance(a, Player) and a.alive), None)

        # Player spotted — switch to full combat
        if player and can_see(owner.x, owner.y, player.x, player.y, floor.dungeon_map):
            owner.ai_brain.set_state(CombatState())
            return owner.ai_brain.current_state.execute(owner, floor)

        # Reached destination or ran out of time — give up
        self._turns_left -= 1
        if self._turns_left <= 0 or (owner.x == self.last_x and owner.y == self.last_y):
            owner.ai_brain.set_state(IdleState())
            return WaitAction()

        # Move toward last known position
        step = CombatState()._step_toward_tile(owner, self.last_x, self.last_y, floor)
        return step or WaitAction()
