"""Player entity."""
from __future__ import annotations

from typing import TYPE_CHECKING

from dungeoneer.core import settings
from dungeoneer.core.i18n import t
from dungeoneer.entities.actor import Actor
from dungeoneer.items.inventory import Inventory
from dungeoneer.items.weapon import Weapon, make_pistol, make_combat_knife
from dungeoneer.items.armor import Armor

if TYPE_CHECKING:
    from dungeoneer.core.difficulty import Difficulty


class Player(Actor):
    def __init__(self, x: int, y: int, difficulty: "Difficulty | None" = None) -> None:
        from dungeoneer.core.difficulty import NORMAL
        diff = difficulty or NORMAL
        super().__init__(
            x, y,
            name=t("entity.player.name"),
            render_colour=settings.COL_PLAYER,
            max_hp=diff.player_max_hp,
            attack=diff.player_attack,
            defence=diff.player_defence,
        )
        self.inventory:        Inventory      = Inventory()
        self.equipped_weapon:  Weapon | None  = make_pistol()
        self.equipped_armor:   Armor  | None  = None
        self.ammo_reserves:    dict[str, int] = dict(diff.starting_ammo)
        self.credits:          int            = 0
        self.floor_depth:      int            = 1
        self.inventory.add(make_combat_knife())

    @property
    def total_defence(self) -> int:
        bonus = self.equipped_armor.defense_bonus if self.equipped_armor else 0
        return self.defence + bonus

    # ------------------------------------------------------------------
    # Weapon helpers
    # ------------------------------------------------------------------

    def equip(self, weapon: Weapon) -> None:
        """Swap weapon from inventory into hand; old weapon goes to inventory."""
        self.inventory.remove(weapon)
        if self.equipped_weapon is not None:
            self.inventory.add(self.equipped_weapon)
        self.equipped_weapon = weapon

    def reload(self) -> bool:
        """Reload equipped ranged weapon from reserves. Returns True if reload happened."""
        from dungeoneer.items.item import RangeType
        w = self.equipped_weapon
        if w is None or w.range_type != RangeType.RANGED:
            return False
        if w.ammo_current >= w.ammo_capacity:
            return False
        available = self.ammo_reserves.get(w.ammo_type, 0)
        if available <= 0:
            return False
        needed = w.ammo_capacity - w.ammo_current
        use = min(needed, available)
        w.ammo_current += use
        self.ammo_reserves[w.ammo_type] -= use
        return True
