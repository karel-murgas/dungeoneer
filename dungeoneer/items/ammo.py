"""Ammo pickup — auto-consumed on floor pickup, adds to player reserves."""
from __future__ import annotations

from dataclasses import dataclass

from dungeoneer.items.item import Item, ItemType
from dungeoneer.core.i18n import t


@dataclass
class AmmoPickup(Item):
    ammo_type:  str = "9mm"
    ammo_count: int = 5


def make_9mm_ammo(count: int = 5) -> AmmoPickup:
    return AmmoPickup(
        id="ammo_9mm",
        name=t("item.ammo_9mm.name").format(n=count),
        description=t("item.ammo_9mm.desc").format(n=count),
        item_type=ItemType.AMMO,
        ammo_type="9mm",
        ammo_count=count,
    )


def make_rifle_ammo(count: int = 3) -> AmmoPickup:
    return AmmoPickup(
        id="ammo_rifle",
        name=t("item.ammo_rifle.name").format(n=count),
        description=t("item.ammo_rifle.desc").format(n=count),
        item_type=ItemType.AMMO,
        ammo_type="rifle",
        ammo_count=count,
    )


def make_shotgun_ammo(count: int = 4) -> AmmoPickup:
    return AmmoPickup(
        id="ammo_shell",
        name=t("item.ammo_shell.name").format(n=count),
        description=t("item.ammo_shell.desc").format(n=count),
        item_type=ItemType.AMMO,
        ammo_type="shell",
        ammo_count=count,
    )
