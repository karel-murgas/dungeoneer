"""Damage calculation — uses equipped weapon stats when available."""
from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class DamageResult:
    raw:     int
    actual:  int
    is_crit: bool = False


def _weapon_roll(weapon) -> tuple[int, bool]:
    """Roll damage for a weapon. Returns (total, is_crit)."""
    roll = random.randint(weapon.damage_min, weapon.damage_max)
    is_crit = roll == weapon.damage_max
    return roll, is_crit


def calc_melee(attacker: "Actor", target: "Actor") -> DamageResult:  # type: ignore[name-defined]
    from dungeoneer.items.item import RangeType

    weapon = getattr(attacker, "equipped_weapon", None)
    if weapon and weapon.range_type == RangeType.MELEE:
        roll, is_crit = _weapon_roll(weapon)
        raw = attacker.attack + weapon.attack_bonus + roll
    else:
        roll = random.randint(1, 4)
        is_crit = roll == 4
        raw = attacker.attack + roll

    actual = target.take_damage(raw)
    return DamageResult(raw, actual, is_crit)


def calc_ranged(attacker: "Actor", target: "Actor") -> DamageResult:  # type: ignore[name-defined]
    from dungeoneer.items.item import RangeType
    from dungeoneer.core.settings import BASE_RANGED_DAMAGE

    weapon = getattr(attacker, "equipped_weapon", None)
    if weapon and weapon.range_type == RangeType.RANGED:
        roll, is_crit = _weapon_roll(weapon)
        raw = weapon.attack_bonus + roll
    else:
        roll = random.randint(1, 6)
        is_crit = roll == 6
        raw = BASE_RANGED_DAMAGE + roll

    actual = target.take_damage(raw)
    return DamageResult(raw, actual, is_crit)
