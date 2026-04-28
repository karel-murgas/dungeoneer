"""Actor base class — any entity that participates in the turn system."""
from __future__ import annotations

from dungeoneer.entities.entity import Entity


class Actor(Entity):
    def __init__(
        self,
        x: int,
        y: int,
        name: str,
        render_colour: tuple,
        *,
        max_hp: int,
        attack: int,
        defence: int,
    ) -> None:
        super().__init__(x, y, name, render_colour)
        self.max_hp  = max_hp
        self.hp      = max_hp
        self.attack  = attack    # base damage modifier
        self.defence = defence   # damage reduction
        self.alive   = True

    @property
    def total_defence(self) -> int:
        """Effective defence including any equipped armor bonuses."""
        return self.defence

    def take_damage(self, amount: int) -> int:
        """Apply damage (after reduction). Returns actual damage dealt."""
        actual = max(1, amount - self.total_defence)
        self.hp -= actual
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        return actual

    def heal(self, amount: int) -> int:
        actual = min(amount, self.max_hp - self.hp)
        self.hp += actual
        if actual > 0:
            from dungeoneer.core.event_bus import bus, HealEvent
            bus.post(HealEvent(self, actual))
        return actual
