"""Weapon item — melee and ranged."""
from __future__ import annotations
import copy
from dataclasses import dataclass, field

from dungeoneer.items.item import Item, ItemType, RangeType


@dataclass
class Weapon(Item):
    range_type:    RangeType = RangeType.MELEE
    damage_min:    int       = 1
    damage_max:    int       = 4
    attack_bonus:  int       = 0    # added on top of actor.attack
    ammo_capacity: int       = 0    # 0 = unlimited/melee
    ammo_current:  int       = 0
    range_tiles:   int       = 1    # max attack range in tiles
    ammo_type:     str       = ""   # "9mm", "rifle", "shell", "" = melee

    def stat_line(self) -> str:
        if self.range_type == RangeType.RANGED:
            return f"{self.damage_min}–{self.damage_max} dmg  {self.ammo_current}/{self.ammo_capacity}  ~{self.range_tiles}t"
        return f"{self.damage_min}–{self.damage_max} dmg"


# ---------------------------------------------------------------------------
# Factory functions — always return a fresh copy
# ---------------------------------------------------------------------------

def make_pistol() -> Weapon:
    return Weapon(
        id="pistol", name="Pistol",
        description="Standard 9mm sidearm.",
        item_type=ItemType.WEAPON,
        range_type=RangeType.RANGED,
        damage_min=3, damage_max=7,
        attack_bonus=0,
        ammo_capacity=8, ammo_current=8,
        range_tiles=8,
        ammo_type="9mm",
    )

def make_combat_knife() -> Weapon:
    return Weapon(
        id="combat_knife", name="Combat Knife",
        description="Lightweight blade. Silent kills.",
        item_type=ItemType.WEAPON,
        range_type=RangeType.MELEE,
        damage_min=2, damage_max=5,
        attack_bonus=1,
        ammo_capacity=0, ammo_current=0,
        range_tiles=1,
    )

def make_shotgun() -> Weapon:
    return Weapon(
        id="shotgun", name="Shotgun",
        description="Devastating at close range. 4 shells.",
        item_type=ItemType.WEAPON,
        range_type=RangeType.RANGED,
        damage_min=7, damage_max=14,
        attack_bonus=0,
        ammo_capacity=4, ammo_current=4,
        range_tiles=5,
        ammo_type="shell",
    )

def make_smg() -> Weapon:
    return Weapon(
        id="smg", name="SMG",
        description="High fire rate, modest damage. 20 rounds.",
        item_type=ItemType.WEAPON,
        range_type=RangeType.RANGED,
        damage_min=2, damage_max=5,
        attack_bonus=0,
        ammo_capacity=20, ammo_current=20,
        range_tiles=7,
        ammo_type="9mm",
    )

def make_heavy_baton() -> Weapon:
    return Weapon(
        id="heavy_baton", name="Heavy Baton",
        description="Corporate riot control. Hits hard.",
        item_type=ItemType.WEAPON,
        range_type=RangeType.MELEE,
        damage_min=3, damage_max=7,
        attack_bonus=2,
        ammo_capacity=0, ammo_current=0,
        range_tiles=1,
    )

def make_rifle() -> Weapon:
    return Weapon(
        id="rifle", name="Rifle",
        description="High-powered marksman rifle. 5 rounds.",
        item_type=ItemType.WEAPON,
        range_type=RangeType.RANGED,
        damage_min=8, damage_max=15,
        attack_bonus=0,
        ammo_capacity=5, ammo_current=5,
        range_tiles=12,
        ammo_type="rifle",
    )
