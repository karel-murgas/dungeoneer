"""Ammo pickup — auto-consumed on floor pickup, adds to player reserves."""
from __future__ import annotations

from dataclasses import dataclass

from dungeoneer.items.item import Item, ItemType


@dataclass
class AmmoPickup(Item):
    ammo_type:  str = "9mm"
    ammo_count: int = 5


def make_9mm_ammo(count: int = 5) -> AmmoPickup:
    return AmmoPickup(
        id="ammo_9mm",
        name=f"9mm Ammo ×{count}",
        description=f"{count} rounds of 9mm ammunition.",
        item_type=ItemType.AMMO,
        ammo_type="9mm",
        ammo_count=count,
    )


def make_rifle_ammo(count: int = 3) -> AmmoPickup:
    return AmmoPickup(
        id="ammo_rifle",
        name=f"Rifle Ammo ×{count}",
        description=f"{count} high-calibre rifle rounds.",
        item_type=ItemType.AMMO,
        ammo_type="rifle",
        ammo_count=count,
    )


def make_shotgun_ammo(count: int = 4) -> AmmoPickup:
    return AmmoPickup(
        id="ammo_shell",
        name=f"Shells ×{count}",
        description=f"{count} shotgun shells.",
        item_type=ItemType.AMMO,
        ammo_type="shell",
        ammo_count=count,
    )
