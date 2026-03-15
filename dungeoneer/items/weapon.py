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
    shots:         int       = 1    # rounds fired per attack action (burst fire)

    def stat_line(self) -> str:
        if self.range_type == RangeType.RANGED:
            burst = f"  ×{self.shots}" if self.shots > 1 else ""
            return f"{self.damage_min}–{self.damage_max} dmg{burst}  {self.ammo_current}/{self.ammo_capacity}  ~{self.range_tiles}t"
        return f"{self.damage_min}–{self.damage_max} dmg"


# ---------------------------------------------------------------------------
# Factory functions — always return a fresh copy
# ---------------------------------------------------------------------------

def make_pistol() -> Weapon:
    return Weapon(
        id="pistol", name="Pistol",
        description="Standard 9mm sidearm. Reliable backup.",
        item_type=ItemType.WEAPON,
        range_type=RangeType.RANGED,
        damage_min=3, damage_max=6,
        attack_bonus=0,
        ammo_capacity=10, ammo_current=10,
        range_tiles=8,
        ammo_type="9mm",
    )

def make_combat_knife() -> Weapon:
    return Weapon(
        id="combat_knife", name="Combat Knife",
        description="Lightweight blade. Fast and silent.",
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
        description="Devastating up close. Useless at range. 4 shells.",
        item_type=ItemType.WEAPON,
        range_type=RangeType.RANGED,
        damage_min=9, damage_max=16,
        attack_bonus=0,
        ammo_capacity=4, ammo_current=4,
        range_tiles=4,
        ammo_type="shell",
    )

def make_smg() -> Weapon:
    return Weapon(
        id="smg", name="SMG",
        description="Burst fire — 3 rounds per shot. Shreds at close range.",
        item_type=ItemType.WEAPON,
        range_type=RangeType.RANGED,
        damage_min=2, damage_max=4,
        attack_bonus=0,
        ammo_capacity=24, ammo_current=24,
        range_tiles=7,
        ammo_type="9mm",
        shots=3,
    )

def make_energy_sword() -> Weapon:
    return Weapon(
        id="energy_sword", name="Energy Sword",
        description="Military-grade energy blade. Cuts through armour.",
        item_type=ItemType.WEAPON,
        range_type=RangeType.MELEE,
        damage_min=5, damage_max=10,
        attack_bonus=2,
        ammo_capacity=0, ammo_current=0,
        range_tiles=1,
    )

def make_rifle() -> Weapon:
    return Weapon(
        id="rifle", name="Rifle",
        description="Long-range precision. Lower burst than shotgun. 6 rounds.",
        item_type=ItemType.WEAPON,
        range_type=RangeType.RANGED,
        damage_min=5, damage_max=10,
        attack_bonus=0,
        ammo_capacity=6, ammo_current=6,
        range_tiles=14,
        ammo_type="rifle",
    )
