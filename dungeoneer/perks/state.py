"""Pure helpers operating on profile.perks dict.

Canonical profile.perks shape: {perk_id: {"level": int}}
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dungeoneer.meta.profile import Profile

from dungeoneer.perks.catalog import CATALOG


def get_level(profile: "Profile", perk_id: str) -> int:
    """Return owned level for perk_id (0 = not owned)."""
    entry = profile.perks.get(perk_id)
    if entry is None:
        return 0
    return entry.get("level", 0)


def is_owned(profile: "Profile", perk_id: str, level: int = 1) -> bool:
    """Return True if profile owns perk_id at >= level."""
    return get_level(profile, perk_id) >= level


def set_level(profile: "Profile", perk_id: str, level: int) -> None:
    """Set perk level in profile.perks. level=0 removes the entry."""
    if level <= 0:
        profile.perks.pop(perk_id, None)
    else:
        profile.perks[perk_id] = {"level": level}


def total_cost_to(profile: "Profile", perk_id: str, target_level: int) -> int:
    """Credit cost to go from current owned level to target_level.

    Returns 0 if already at or above target_level.
    Raises KeyError for unknown perk_id.
    """
    perk = CATALOG[perk_id]
    current = get_level(profile, perk_id)
    if target_level <= current or target_level > perk.max_level:
        return 0
    return sum(perk.prices[lvl] for lvl in range(current, target_level))
