"""Consumable items."""
from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

from dungeoneer.items.item import Item, ItemType
from dungeoneer.core.i18n import t

if TYPE_CHECKING:
    from dungeoneer.entities.actor import Actor


@dataclass
class Consumable(Item):
    heal_amount:    int = 0
    defence_bonus:  int = 0   # temporary — placeholder for Phase 3 status effects
    count:          int = 1   # stack size

    def stat_line(self) -> str:
        parts = []
        if self.heal_amount:
            parts.append(f"+{self.heal_amount} HP")
        if self.defence_bonus:
            parts.append(f"+{self.defence_bonus} def")
        base = "  ".join(parts) or "?"
        return f"{base}  ×{self.count}" if self.count > 1 else base

    def use(self, actor: "Actor") -> str:
        """Apply effect, return result message."""
        msgs = []
        if self.heal_amount:
            actual = actor.heal(self.heal_amount)
            msgs.append(t("log.heal_restored").format(n=actual))
        return t("log.item_used").format(name=self.name) + " " + " ".join(msgs)


# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------

def make_stim_pack() -> Consumable:
    return Consumable(
        id="stim_pack", name=t("item.stim_pack.name"),
        description=t("item.stim_pack.desc"),
        item_type=ItemType.CONSUMABLE,
        heal_amount=10,
    )

def make_medkit() -> Consumable:
    return Consumable(
        id="medkit", name=t("item.medkit.name"),
        description=t("item.medkit.desc"),
        item_type=ItemType.CONSUMABLE,
        heal_amount=20,
    )
