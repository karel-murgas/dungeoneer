"""Per-run stat counters and merge helper for lifetime stats."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RunStats:
    """Counters for one run. Mirrors LifetimeStats minus runs_won."""
    kills_total: int = 0
    kills_by_enemy: dict[str, int] = field(default_factory=dict)
    kills_by_weapon: dict[str, int] = field(default_factory=dict)
    deaths_total: int = 0
    deaths_by_killer: dict[str, int] = field(default_factory=dict)
    hp_healed: int = 0
    bullets_shot: int = 0
    crits_total: int = 0
    containers_hacked: int = 0
    nodes_hacked: int = 0
    containers_fully_hacked: int = 0
    containers_failed: int = 0
    credits_earned: int = 0


def merge_run_into_lifetime(
    run: "RunStats",
    lifetime: "LifetimeStats",  # type: ignore[name-defined]
    victory: bool,
) -> None:
    """Merge run counters into lifetime stats in-place."""
    from dungeoneer.meta.profile import LifetimeStats  # noqa: F401 (type check above)

    lifetime.kills_total += run.kills_total
    lifetime.deaths_total += run.deaths_total
    lifetime.hp_healed += run.hp_healed
    lifetime.bullets_shot += run.bullets_shot
    lifetime.crits_total += run.crits_total
    lifetime.containers_hacked += run.containers_hacked
    lifetime.nodes_hacked += run.nodes_hacked
    lifetime.containers_fully_hacked += run.containers_fully_hacked
    lifetime.containers_failed += run.containers_failed
    lifetime.credits_lifetime += run.credits_earned

    for enemy_id, count in run.kills_by_enemy.items():
        lifetime.kills_by_enemy[enemy_id] = lifetime.kills_by_enemy.get(enemy_id, 0) + count

    for weapon_id, count in run.kills_by_weapon.items():
        lifetime.kills_by_weapon[weapon_id] = lifetime.kills_by_weapon.get(weapon_id, 0) + count

    for killer_id, count in run.deaths_by_killer.items():
        lifetime.deaths_by_killer[killer_id] = lifetime.deaths_by_killer.get(killer_id, 0) + count

    if victory:
        lifetime.runs_won += 1
