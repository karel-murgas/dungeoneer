"""Item base class and enums."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import auto, Enum


class ItemType(Enum):
    WEAPON     = auto()
    CONSUMABLE = auto()
    AMMO       = auto()
    ARMOR      = auto()
    CREDITS    = auto()


class RangeType(Enum):
    MELEE  = auto()
    RANGED = auto()


@dataclass
class Item:
    id:          str
    name:        str
    description: str
    item_type:   ItemType
