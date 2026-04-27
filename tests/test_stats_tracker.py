"""Tests for StatsTracker and merge_run_into_lifetime."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from dungeoneer.core.event_bus import (
    bus,
    DeathEvent,
    DamageEvent,
    HealEvent,
    BulletFiredEvent,
    ContainerLootedEvent,
    HackNodesCollectedEvent,
)
from dungeoneer.core.stats import RunStats, merge_run_into_lifetime
from dungeoneer.meta.profile import LifetimeStats
from dungeoneer.systems.stats_tracker import StatsTracker


# ---------------------------------------------------------------------------
# Helpers — lightweight stubs that avoid pygame / full game init
# ---------------------------------------------------------------------------

def _player_mock():
    from dungeoneer.entities import player as pm
    p = MagicMock(spec=pm.Player)
    p.__class__ = pm.Player
    p.credits = 0
    return p


def _enemy_mock(enemy_id: str = "guard"):
    from dungeoneer.entities import enemy as em
    e = MagicMock(spec=em.Enemy)
    e.__class__ = em.Enemy
    e.enemy_id = enemy_id
    return e


@pytest.fixture()
def tracker():
    """A fresh StatsTracker subscribed to the real bus; unsubscribes after test."""
    player = _player_mock()
    t = StatsTracker(player, credit_baseline=0)
    t.subscribe()
    yield t
    t.unsubscribe()


# ---------------------------------------------------------------------------
# RunStats basic checks
# ---------------------------------------------------------------------------

def test_runstats_defaults():
    r = RunStats()
    assert r.kills_total == 0
    assert r.deaths_total == 0
    assert r.crits_total == 0
    assert r.bullets_shot == 0
    assert r.credits_earned == 0


# ---------------------------------------------------------------------------
# merge_run_into_lifetime
# ---------------------------------------------------------------------------

def test_merge_scalars():
    run = RunStats(kills_total=5, deaths_total=1, hp_healed=20,
                   bullets_shot=30, crits_total=3,
                   containers_hacked=2, nodes_hacked=4,
                   containers_fully_hacked=2, containers_failed=1,
                   credits_earned=100)
    lts = LifetimeStats(kills_total=10, runs_won=2)
    merge_run_into_lifetime(run, lts, victory=True)

    assert lts.kills_total == 15
    assert lts.deaths_total == 1
    assert lts.hp_healed == 20
    assert lts.bullets_shot == 30
    assert lts.crits_total == 3
    assert lts.containers_hacked == 2
    assert lts.nodes_hacked == 4
    assert lts.containers_fully_hacked == 2
    assert lts.containers_failed == 1
    assert lts.credits_lifetime == 100
    assert lts.runs_won == 3  # victory=True increments


def test_merge_no_runs_won_on_death():
    run = RunStats()
    lts = LifetimeStats(runs_won=5)
    merge_run_into_lifetime(run, lts, victory=False)
    assert lts.runs_won == 5


def test_merge_dict_buckets():
    run = RunStats(
        kills_by_enemy={"guard": 3, "drone": 1},
        kills_by_weapon={"pistol": 2, "combat_knife": 2},
        deaths_by_killer={"guard": 1},
    )
    lts = LifetimeStats(
        kills_by_enemy={"guard": 5},
        kills_by_weapon={"pistol": 10},
    )
    merge_run_into_lifetime(run, lts, victory=False)

    assert lts.kills_by_enemy == {"guard": 8, "drone": 1}
    assert lts.kills_by_weapon == {"pistol": 12, "combat_knife": 2}
    assert lts.deaths_by_killer == {"guard": 1}


# ---------------------------------------------------------------------------
# StatsTracker event handling
# ---------------------------------------------------------------------------

def test_player_kill_increments_counters(tracker):
    player = tracker._player
    enemy = _enemy_mock("drone")
    bus.post(DeathEvent(entity=enemy, killer=player, weapon_id="pistol"))

    assert tracker.run.kills_total == 1
    assert tracker.run.kills_by_enemy == {"drone": 1}
    assert tracker.run.kills_by_weapon == {"pistol": 1}
    assert tracker.run.deaths_total == 0


def test_player_death_buckets_killer(tracker):
    player = tracker._player
    killer = _enemy_mock("heavy")
    bus.post(DeathEvent(entity=player, killer=killer, weapon_id=None))

    assert tracker.run.deaths_total == 1
    assert tracker.run.deaths_by_killer == {"heavy": 1}
    assert tracker.run.kills_total == 0


def test_enemy_vs_enemy_death_ignored(tracker):
    enemy_a = _enemy_mock("guard")
    enemy_b = _enemy_mock("drone")
    bus.post(DeathEvent(entity=enemy_b, killer=enemy_a, weapon_id="pistol"))

    assert tracker.run.kills_total == 0
    assert tracker.run.deaths_total == 0


def test_kills_by_weapon_skip_when_no_weapon_id(tracker):
    player = tracker._player
    enemy = _enemy_mock("guard")
    bus.post(DeathEvent(entity=enemy, killer=player, weapon_id=None))

    assert tracker.run.kills_total == 1
    assert tracker.run.kills_by_weapon == {}


def test_kill_and_death_buckets_accumulate(tracker):
    player = tracker._player
    guard = _enemy_mock("guard")
    drone = _enemy_mock("drone")
    bus.post(DeathEvent(entity=guard, killer=player, weapon_id="pistol"))
    bus.post(DeathEvent(entity=guard, killer=player, weapon_id="pistol"))
    bus.post(DeathEvent(entity=drone, killer=player, weapon_id="combat_knife"))

    assert tracker.run.kills_total == 3
    assert tracker.run.kills_by_enemy == {"guard": 2, "drone": 1}
    assert tracker.run.kills_by_weapon == {"pistol": 2, "combat_knife": 1}


def test_heal_counts_only_player(tracker):
    player = tracker._player
    enemy = _enemy_mock()
    bus.post(HealEvent(actor=player, amount=15))
    bus.post(HealEvent(actor=enemy, amount=10))

    assert tracker.run.hp_healed == 15


def test_bullet_counts_only_player(tracker):
    player = tracker._player
    enemy = _enemy_mock()
    bus.post(BulletFiredEvent(shooter=player, weapon_id="pistol"))
    bus.post(BulletFiredEvent(shooter=player, weapon_id="pistol"))
    bus.post(BulletFiredEvent(shooter=enemy, weapon_id="pistol"))

    assert tracker.run.bullets_shot == 2


def test_crit_tracking(tracker):
    player = tracker._player
    enemy = _enemy_mock()
    bus.post(DamageEvent(attacker=player, target=enemy, amount=10, is_crit=True))
    bus.post(DamageEvent(attacker=player, target=enemy, amount=5, is_crit=False))
    bus.post(DamageEvent(attacker=enemy, target=player, amount=3, is_crit=True))

    assert tracker.run.crits_total == 1  # only player crits


def test_container_hacked_success(tracker):
    container = MagicMock()
    bus.post(ContainerLootedEvent(container=container, success=True, was_hacked=True))
    bus.post(ContainerLootedEvent(container=container, success=False, was_hacked=True))
    bus.post(ContainerLootedEvent(container=container, success=True, was_hacked=False))

    assert tracker.run.containers_hacked == 1
    assert tracker.run.containers_failed == 1


def test_containers_fully_hacked_only_on_all_nodes_cleared(tracker):
    bus.post(HackNodesCollectedEvent(nodes_collected=5, success=True, coolant_reduction=0, all_nodes_cleared=True))
    bus.post(HackNodesCollectedEvent(nodes_collected=3, success=True, coolant_reduction=0, all_nodes_cleared=False))
    bus.post(HackNodesCollectedEvent(nodes_collected=0, success=False, coolant_reduction=0, all_nodes_cleared=False))

    assert tracker.run.containers_fully_hacked == 1
    assert tracker.run.nodes_hacked == 8


def test_hack_nodes_collected(tracker):
    bus.post(HackNodesCollectedEvent(nodes_collected=5, success=True, coolant_reduction=0, all_nodes_cleared=True))
    bus.post(HackNodesCollectedEvent(nodes_collected=2, success=False, coolant_reduction=0, all_nodes_cleared=False))

    assert tracker.run.nodes_hacked == 7


def test_finalize_credits():
    player = _player_mock()
    player.credits = 130
    t = StatsTracker(player, credit_baseline=50)
    t.subscribe()
    try:
        run = t.finalize()
        assert run.credits_earned == 80
    finally:
        t.unsubscribe()


def test_finalize_credits_no_negative():
    player = _player_mock()
    player.credits = 80
    t = StatsTracker(player, credit_baseline=100)
    t.subscribe()
    try:
        run = t.finalize()
        assert run.credits_earned == 0
    finally:
        t.unsubscribe()
