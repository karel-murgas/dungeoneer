"""AIBrain — owns a BehaviorState and drives enemy turns."""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from dungeoneer.ai.states import BehaviorState, IdleState, CombatState

if TYPE_CHECKING:
    from dungeoneer.entities.actor import Actor
    from dungeoneer.world.floor import Floor
    from dungeoneer.combat.action import Action


class AIBrain:
    def __init__(self) -> None:
        self.current_state: BehaviorState = IdleState()

    def set_state(self, state: BehaviorState) -> None:
        self.current_state = state

    def take_turn(self, floor: "Floor") -> Optional["Action"]:
        # owner is set externally after construction
        return self.current_state.execute(self._owner, floor)

    def alert(self, last_known_x: int, last_known_y: int) -> None:
        """Alert this enemy to an attacker — enter combat immediately."""
        if not isinstance(self.current_state, CombatState):
            self.set_state(CombatState())

    def attach(self, owner: "Actor") -> None:
        self._owner = owner
