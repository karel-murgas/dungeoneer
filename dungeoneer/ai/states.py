"""AI behaviour states."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from dungeoneer.entities.actor import Actor
    from dungeoneer.world.floor import Floor
    from dungeoneer.combat.action import Action

log = logging.getLogger(__name__)

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
    def __init__(self) -> None:
        self._last_known: Optional[tuple[int, int]] = None
        self._prev_dist: int = 0

    def execute(self, owner: "Actor", floor: "Floor") -> Optional["Action"]:
        from dungeoneer.entities.player import Player
        from dungeoneer.combat.action import WaitAction
        from dungeoneer.core.settings import DRONE_PREFERRED_DIST

        log.debug("CombatState.execute  owner=%s at (%d,%d)", owner.name, owner.x, owner.y)
        player = next((a for a in floor.actors if isinstance(a, Player) and a.alive), None)
        if player is None:
            log.debug("  → no living player, IdleState")
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
        from dungeoneer.combat.action import MeleeAttackAction, WaitAction
        from dungeoneer.ai.perception import can_see

        visible = can_see(owner.x, owner.y, player.x, player.y, floor.dungeon_map)
        log.debug(
            "guard %s at (%d,%d) dist=%d to player(%d,%d) visible=%s last_known=%s",
            owner.name, owner.x, owner.y, dist, player.x, player.y, visible, self._last_known,
        )

        if visible:
            self._last_known = (player.x, player.y)
            if dist == 1:
                return MeleeAttackAction(player)
            step = self._step_toward(owner, player, floor)
            if step is not None:
                return step
            # Length-limited path failed (blocked by allies / detour too long).
            # Fall back to plain pathfind to player — don't just stop.
            step = self._step_toward_tile(owner, player.x, player.y, floor)
            if step is not None:
                log.debug("guard %s fell back to unconstrained path toward player", owner.name)
                return step
            log.debug("guard %s has no path to player — waiting", owner.name)
            return WaitAction()

        # Lost sight — investigate last known position.
        if self._last_known:
            log.debug("guard %s lost sight → SearchState(%s)", owner.name, self._last_known)
            owner.ai_brain.set_state(SearchState(*self._last_known))
            return owner.ai_brain.current_state.execute(owner, floor)
        log.debug("guard %s lost sight with no last_known → Idle", owner.name)
        owner.ai_brain.set_state(IdleState())
        return WaitAction()

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

        pf = Pathfinder()

        # Wall-only shortest path — baseline length ignoring entities.
        base_path = pf.find_path(
            (owner.x, owner.y), (player.x, player.y), floor.dungeon_map,
        )
        if not base_path:
            return None  # player is walled off entirely

        # Block containers and other alive actors (allies) so A* routes around them.
        blocked = [(c.x, c.y) for c in floor.containers if not c.opened]
        blocked += [
            (a.x, a.y) for a in floor.actors
            if a is not owner and a is not player and a.alive
        ]

        path = pf.find_path(
            (owner.x, owner.y), (player.x, player.y), floor.dungeon_map,
            extra_blocked=blocked,
        )
        if not path:
            return None

        # Reject paths that deviate too far from the wall-only baseline —
        # prevents enemies from doubling back through a long corridor just to
        # route around another actor, while still allowing corners and 1-tile gaps.
        if len(path) > len(base_path) + 3:
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

        log.debug(
            "SearchState.execute  owner=%s at (%d,%d) target=(%d,%d) turns_left=%d",
            owner.name, owner.x, owner.y, self.last_x, self.last_y, self._turns_left,
        )
        player = next((a for a in floor.actors if isinstance(a, Player) and a.alive), None)

        # Player spotted — switch to full combat
        if player and can_see(owner.x, owner.y, player.x, player.y, floor.dungeon_map):
            log.debug("  → spotted player, back to CombatState")
            owner.ai_brain.set_state(CombatState())
            return owner.ai_brain.current_state.execute(owner, floor)

        # Reached destination or ran out of time — give up
        self._turns_left -= 1
        if self._turns_left <= 0 or (owner.x == self.last_x and owner.y == self.last_y):
            log.debug("  → give up, IdleState")
            owner.ai_brain.set_state(IdleState())
            return WaitAction()

        # Move toward last known position
        step = CombatState()._step_toward_tile(owner, self.last_x, self.last_y, floor)
        if step is None:
            log.debug("  → no path to (%d,%d), waiting", self.last_x, self.last_y)
        return step or WaitAction()
