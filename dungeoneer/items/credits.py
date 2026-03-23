"""Credit pickup item — dropped by enemies, collected on walk-over."""
from __future__ import annotations

from dungeoneer.core.i18n import t
from dungeoneer.items.item import Item, ItemType


class CreditPickup(Item):
    def __init__(self, amount: int) -> None:
        super().__init__(
            id="credits",
            name=t("item.credits.name").format(n=amount),
            description=t("item.credits.desc"),
            item_type=ItemType.CREDITS,
        )
        self.amount = amount


def make_credits(amount: int) -> CreditPickup:
    return CreditPickup(amount)
