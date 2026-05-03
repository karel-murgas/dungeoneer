"""Tests for the Phase-1 perk-firing stub in GameScene._fire_perk.

These tests exercise the logic directly without a real display or floor.
"""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

from dungeoneer.meta.profile import Profile
from dungeoneer.entities.player import Player
from dungeoneer.core.difficulty import NORMAL
from dungeoneer.core.event_bus import bus, LogMessageEvent
from dungeoneer.perks import set_level


# ---------------------------------------------------------------------------
# Minimal stub for GameScene._fire_perk
# We avoid constructing a full GameScene (which needs a real App) by extracting
# the same logic into a standalone function that mirrors the method exactly.
# ---------------------------------------------------------------------------

def fire_perk(player: Player, profile: Profile, slot: int) -> bool:
    """Mirror of GameScene._fire_perk without the scene context."""
    from dungeoneer.core.i18n import t
    from dungeoneer.perks import CATALOG

    hotbar = profile.hotbar
    perk_id = hotbar[slot] if slot < len(hotbar) else None

    if not perk_id:
        bus.post(LogMessageEvent(t("log.perks.empty_slot"), (100, 100, 100)))
        return False

    if perk_id not in CATALOG:
        return False

    pdef = CATALOG[perk_id]

    if pdef.target_required:
        bus.post(LogMessageEvent(t("log.perks.target_required"), (180, 140, 60)))
        return False

    cost = pdef.ep_cost if pdef.ep_cost is not None else pdef.ep_per_turn
    if cost is not None:
        if not player.consume_energy(cost):
            bus.post(LogMessageEvent(t("log.perks.no_energy"), (200, 80, 80)))
            return False

    bus.post(LogMessageEvent(
        t("log.perks.fired").format(name=t(pdef.name_key)),
        (80, 200, 255),
    ))
    return True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_player(energy: int = 100) -> Player:
    p = Player(0, 0, NORMAL)
    p.energy = energy
    return p


def make_profile() -> Profile:
    return Profile(name="test")


class _LogCapture:
    """Subscribe to LogMessageEvent and capture posted messages."""

    def __init__(self):
        self.messages: list[str] = []
        bus.subscribe(LogMessageEvent, self._on)

    def _on(self, ev: LogMessageEvent) -> None:
        self.messages.append(ev.message)

    def detach(self):
        bus.unsubscribe(LogMessageEvent, self._on)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_fire_perk_deducts_energy_and_posts_log():
    player  = make_player(energy=20)
    profile = make_profile()
    profile.hotbar[0] = "scanner"   # scanner costs 8 EP

    cap = _LogCapture()
    try:
        result = fire_perk(player, profile, 0)
    finally:
        cap.detach()

    assert result is True
    assert player.energy == 12
    assert any("Activated" in m or "Sensitive scanner" in m for m in cap.messages), cap.messages


def test_fire_perk_insufficient_energy_does_not_deduct():
    player  = make_player(energy=5)
    profile = make_profile()
    profile.hotbar[0] = "scanner"   # scanner costs 8 EP

    cap = _LogCapture()
    try:
        result = fire_perk(player, profile, 0)
    finally:
        cap.detach()

    assert result is False
    assert player.energy == 5
    assert any("energy" in m.lower() or "energie" in m.lower() or "energ" in m.lower()
               for m in cap.messages), cap.messages


def test_fire_perk_empty_slot_posts_log_and_returns_false():
    player  = make_player(energy=100)
    profile = make_profile()
    # hotbar slot 3 is None (default)

    cap = _LogCapture()
    try:
        result = fire_perk(player, profile, 3)
    finally:
        cap.detach()

    assert result is False
    assert player.energy == 100
    assert len(cap.messages) == 1


def test_fire_perk_target_required_does_not_deduct_energy():
    """Perks with target_required should abort with a log, not consume EP."""
    player  = make_player(energy=100)
    profile = make_profile()
    profile.hotbar[0] = "trap"   # deferred=True, target_required=True, ep_cost=12

    cap = _LogCapture()
    try:
        result = fire_perk(player, profile, 0)
    finally:
        cap.detach()

    assert result is False
    assert player.energy == 100
