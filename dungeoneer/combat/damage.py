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
        raw = roll
    else:
        roll = random.randint(1, 4)
        is_crit = roll == 4
        raw = roll

    actual = target.take_damage(raw)
    return DamageResult(raw, actual, is_crit)


def calc_ranged_aimed(
    attacker: "Actor",  # type: ignore[name-defined]
    target: "Actor",    # type: ignore[name-defined]
    accuracy: float,
) -> DamageResult:
    """Damage from the aiming minigame. accuracy=-1.0 = miss, 0.0–1.0 = hit."""
    from dungeoneer.core.settings import AIM_CRIT_THRESHOLD

    if accuracy < 0.0:
        return DamageResult(raw=0, actual=0, is_crit=False)

    weapon = getattr(attacker, "equipped_weapon", None)
    if weapon is not None:
        dmg_range = weapon.damage_max - weapon.damage_min
        raw = weapon.damage_min + round(accuracy * dmg_range)
    else:
        from dungeoneer.core.settings import BASE_RANGED_DAMAGE
        raw = round(BASE_RANGED_DAMAGE * (0.5 + accuracy * 0.5))

    is_crit = accuracy >= AIM_CRIT_THRESHOLD
    actual = target.take_damage(raw)
    return DamageResult(raw, actual, is_crit)


def simulate_aim(weapon, distance: int) -> float:
    """Zone-based accuracy simulation — used when the player has minigame OFF.

    Returns accuracy in [0.0, 1.0] on hit, or -1.0 on miss.
    """
    from dungeoneer.core.settings import AIM_ARC_DEGREES, AIM_MIN_ZONE

    zone = max(AIM_MIN_ZONE, weapon.aim_zone_base - distance * weapon.aim_zone_penalty)
    hit_chance = min(1.0, zone / AIM_ARC_DEGREES)
    if random.random() >= hit_chance:
        return -1.0
    return random.random()


def simulate_aim_enemy(distance: int, aim_skill: float) -> float:
    """Normal-distribution accuracy simulation for enemies.

    aim_skill controls sigma (spread of the distribution):
        higher aim_skill → lower sigma → tighter grouping → more consistent hits.

    Typical values:
        Guard  aim_skill=2.5  → sigma≈0.40  → ~5% miss at d=1, ~23% miss at d=8
        Drone  aim_skill=4.5  → sigma≈0.22  → <1% miss at d=1, ~7% miss at d=8

    Returns accuracy in [0.0, 1.0] on hit, or -1.0 on miss.
    """
    from dungeoneer.core.settings import AIM_SIM_MEAN_BASE, AIM_SIM_MEAN_SLOPE

    mean  = max(0.0, AIM_SIM_MEAN_BASE - distance * AIM_SIM_MEAN_SLOPE)
    sigma = 1.0 / max(0.1, aim_skill)
    value = random.gauss(mean, sigma)
    if value < 0.0:
        return -1.0
    return min(1.0, value)


def calc_ranged(attacker: "Actor", target: "Actor") -> DamageResult:  # type: ignore[name-defined]
    from dungeoneer.items.item import RangeType
    from dungeoneer.core.settings import BASE_RANGED_DAMAGE

    weapon = getattr(attacker, "equipped_weapon", None)
    if weapon and weapon.range_type == RangeType.RANGED:
        roll, is_crit = _weapon_roll(weapon)
        raw = roll
    else:
        roll = random.randint(1, 6)
        is_crit = roll == 6
        raw = BASE_RANGED_DAMAGE + roll

    actual = target.take_damage(raw)
    return DamageResult(raw, actual, is_crit)
