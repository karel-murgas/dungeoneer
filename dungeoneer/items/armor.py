"""Armor item — wearable protection that reduces incoming damage."""
from __future__ import annotations
from dataclasses import dataclass

from dungeoneer.items.item import Item, ItemType
from dungeoneer.core.i18n import t


@dataclass
class Armor(Item):
    defense_bonus: int = 1  # added to actor.defence when equipped

    def stat_line(self) -> str:
        return f"-{self.defense_bonus} dmg"


def make_basic_armor() -> Armor:
    return Armor(
        id="basic_armor",
        name=t("item.basic_armor.name"),
        description=t("item.basic_armor.desc"),
        item_type=ItemType.ARMOR,
        defense_bonus=1,
    )
