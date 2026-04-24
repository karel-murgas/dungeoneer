"""Shared enumerations for the hacking minigame."""
from __future__ import annotations

from enum import auto, Enum


class LootKind(Enum):
    AMMO         = auto()
    RIFLE_AMMO   = auto()
    SHOTGUN_AMMO = auto()
    HEAL         = auto()
    MEDKIT       = auto()
    WEAPON       = auto()
    CREDITS      = auto()
    BONUS_TIME   = auto()
    ARMOR        = auto()
    COOLANT      = auto()   # purges trace — reduces player heat at hack end
    MYSTERY      = auto()   # resolves to a random non-mystery kind on collection


class SecurityKind(Enum):
    TIME_PENALTY = auto()
    DESTROY_LOOT = auto()
    BLOCKED      = auto()
