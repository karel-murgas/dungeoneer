"""Tests for CyberwareShopOverlay purchase logic (no pygame display required)."""
from __future__ import annotations

import os
import sys

import pytest

# Stub out pygame display before importing any game module that imports pygame
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

from dungeoneer.meta.profile import Profile
from dungeoneer.perks import get_level, set_level, total_cost_to, CATALOG
from dungeoneer.rendering.ui.cyberware_shop_overlay import CyberwareShopOverlay


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_profile(credits: int = 1000) -> Profile:
    p = Profile(name="test")
    p.credits = credits
    return p


def make_overlay(profile: Profile):
    purchased: list[Profile] = []
    closed: list[bool] = []

    overlay = CyberwareShopOverlay(
        profile=profile,
        on_close=lambda: closed.append(True),
        on_purchase=lambda p: purchased.append(p),
    )
    return overlay, purchased, closed


# ---------------------------------------------------------------------------
# Purchase logic tests (bypass UI — call _do_purchase directly)
# ---------------------------------------------------------------------------

def test_buy_smartlink_deducts_credits_and_sets_level():
    p = make_profile(1000)
    overlay, purchased, _ = make_overlay(p)

    overlay._selected_perk_id = "smartlink"
    overlay._do_purchase("smartlink")   # smartlink costs 350

    assert p.credits == 650
    assert get_level(p, "smartlink") == 1
    assert len(purchased) == 1


def test_buy_protocol_smg_l1_then_upgrade_to_l2():
    p = make_profile(5000)
    overlay, _, _ = make_overlay(p)

    # Buy L1 (500 CR)
    overlay._do_purchase("protocol_smg")
    assert get_level(p, "protocol_smg") == 1
    assert p.credits == 4500

    # Upgrade to L2 (1500 CR)
    overlay._do_purchase("protocol_smg")
    assert get_level(p, "protocol_smg") == 2
    assert p.credits == 3000


def test_insufficient_credits_does_not_change_profile():
    p = make_profile(100)   # smartlink costs 350
    overlay, purchased, _ = make_overlay(p)

    overlay._do_purchase("smartlink")

    assert p.credits == 100
    assert get_level(p, "smartlink") == 0
    assert len(purchased) == 0


def test_deferred_perk_cannot_be_purchased():
    p = make_profile(9999)
    overlay, purchased, _ = make_overlay(p)

    overlay._do_purchase("mech_arm")   # deferred perk

    assert get_level(p, "mech_arm") == 0
    assert len(purchased) == 0
    assert p.credits == 9999


def test_already_max_level_does_not_change_profile():
    p = make_profile(5000)
    set_level(p, "smartlink", 1)   # already at max (max_level=1)
    overlay, purchased, _ = make_overlay(p)

    overlay._do_purchase("smartlink")

    assert get_level(p, "smartlink") == 1
    assert p.credits == 5000
    assert len(purchased) == 0


def test_on_purchase_callback_called_with_profile():
    p = make_profile(1000)
    received: list[Profile] = []
    overlay = CyberwareShopOverlay(
        profile=p,
        on_close=lambda: None,
        on_purchase=lambda prof: received.append(prof),
    )
    overlay._do_purchase("smartlink")

    assert len(received) == 1
    assert received[0] is p


def test_try_buy_selected_opens_confirm_when_affordable():
    p = make_profile(1000)
    overlay, _, _ = make_overlay(p)
    overlay._selected_perk_id = "smartlink"

    overlay._try_buy_selected()

    assert overlay._confirm_dialog is not None
    assert overlay._confirm_perk_id == "smartlink"


def test_try_buy_selected_does_not_open_confirm_when_broke():
    p = make_profile(10)   # not enough for smartlink (350)
    overlay, _, _ = make_overlay(p)
    overlay._selected_perk_id = "smartlink"

    overlay._try_buy_selected()

    assert overlay._confirm_dialog is None


def test_try_buy_selected_does_not_open_confirm_for_deferred():
    p = make_profile(9999)
    overlay, _, _ = make_overlay(p)
    overlay._selected_perk_id = "mech_arm"

    overlay._try_buy_selected()

    assert overlay._confirm_dialog is None
