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

    def take_damage(self, amount: int) -> int:
        """Apply damage (after reduction). Returns actual damage dealt."""
        actual = max(1, amount - self.defence)
        self.hp -= actual
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        return actual

    def heal(self, amount: int) -> int:
        actual = min(amount, self.max_hp - self.hp)
        self.hp += actual
        return actual
