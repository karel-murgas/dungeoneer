"""Sanity checks for the perks catalog and state helpers."""
from __future__ import annotations

import pytest

from dungeoneer.perks import CATALOG, PerkType, get_perk, get_level, is_owned, set_level, total_cost_to
from dungeoneer.core.i18n import t
from dungeoneer.meta.profile import Profile


# ---------------------------------------------------------------------------
# Catalog structure
# ---------------------------------------------------------------------------

EXPECTED_IDS = {
    "smartlink", "muscle_implants", "skeleton", "lenses",
    "protocol_smg", "protocol_shotgun", "protocol_rifle", "protocol_sword",
    "network_scan", "mech_arm",
    "scanner", "reflex_fibres", "cloak", "recoil_comp", "nanobots",
    "neural_protection", "trap", "surge_contacts",
}

DEFERRED_IDS = {"neural_protection", "trap", "surge_contacts", "mech_arm"}


def test_catalog_has_all_expected_ids():
    assert EXPECTED_IDS == set(CATALOG.keys()), (
        f"Extra: {set(CATALOG) - EXPECTED_IDS}, Missing: {EXPECTED_IDS - set(CATALOG)}"
    )


def test_prices_length_matches_max_level():
    for perk in CATALOG.values():
        assert len(perk.prices) == perk.max_level, (
            f"{perk.id}: prices length {len(perk.prices)} != max_level {perk.max_level}"
        )


def test_active_perks_have_ep_cost_or_ep_per_turn():
    for perk in CATALOG.values():
        if perk.type == PerkType.ACTIVE:
            assert perk.ep_cost is not None or perk.ep_per_turn is not None, (
                f"Active perk {perk.id} has neither ep_cost nor ep_per_turn"
            )


def test_passive_perks_have_no_ep_cost():
    for perk in CATALOG.values():
        if perk.type == PerkType.PASSIVE:
            assert perk.ep_cost is None, (
                f"Passive perk {perk.id} has ep_cost={perk.ep_cost}, expected None"
            )
            assert perk.ep_per_turn is None, (
                f"Passive perk {perk.id} has ep_per_turn={perk.ep_per_turn}, expected None"
            )


def test_deferred_flag_matches_expected():
    for perk in CATALOG.values():
        expected = perk.id in DEFERRED_IDS
        assert perk.deferred == expected, (
            f"{perk.id}: deferred={perk.deferred}, expected={expected}"
        )


def test_i18n_keys_exist_for_every_perk():
    for perk in CATALOG.values():
        name_val = t(perk.name_key)
        desc_val = t(perk.desc_key)
        # t() falls back to raw key on miss — ensure it resolved to something different
        assert name_val != perk.name_key, f"Missing i18n for {perk.name_key}"
        assert desc_val != perk.desc_key, f"Missing i18n for {perk.desc_key}"


def test_get_perk_returns_correct_def():
    p = get_perk("smartlink")
    assert p.id == "smartlink"
    assert p.type == PerkType.PASSIVE


def test_get_perk_raises_on_unknown():
    with pytest.raises(KeyError):
        get_perk("does_not_exist")


# ---------------------------------------------------------------------------
# state.py helpers
# ---------------------------------------------------------------------------

def make_profile() -> Profile:
    return Profile(name="test")


def test_get_level_unowned():
    p = make_profile()
    assert get_level(p, "smartlink") == 0


def test_set_and_get_level():
    p = make_profile()
    set_level(p, "smartlink", 1)
    assert get_level(p, "smartlink") == 1


def test_is_owned_false_when_not_owned():
    p = make_profile()
    assert not is_owned(p, "smartlink")


def test_is_owned_true_when_owned():
    p = make_profile()
    set_level(p, "smartlink", 1)
    assert is_owned(p, "smartlink")


def test_is_owned_level_check():
    p = make_profile()
    set_level(p, "protocol_smg", 1)
    assert is_owned(p, "protocol_smg", level=1)
    assert not is_owned(p, "protocol_smg", level=2)


def test_set_level_zero_removes_entry():
    p = make_profile()
    set_level(p, "smartlink", 1)
    set_level(p, "smartlink", 0)
    assert get_level(p, "smartlink") == 0
    assert "smartlink" not in p.perks


def test_total_cost_unowned_to_l1():
    p = make_profile()
    cost = total_cost_to(p, "smartlink", 1)
    assert cost == 350


def test_total_cost_unowned_to_l2_multi():
    p = make_profile()
    # protocol_smg prices = (500, 1500, 3000)
    cost = total_cost_to(p, "protocol_smg", 2)
    assert cost == 500 + 1500


def test_total_cost_owned_l1_to_l2():
    p = make_profile()
    set_level(p, "protocol_smg", 1)
    cost = total_cost_to(p, "protocol_smg", 2)
    assert cost == 1500


def test_total_cost_already_at_target():
    p = make_profile()
    set_level(p, "smartlink", 1)
    assert total_cost_to(p, "smartlink", 1) == 0


def test_total_cost_beyond_max_level():
    p = make_profile()
    assert total_cost_to(p, "smartlink", 2) == 0  # max_level is 1


# ---------------------------------------------------------------------------
# Profile.hotbar round-trip
# ---------------------------------------------------------------------------

def test_hotbar_defaults_to_10_nones():
    p = make_profile()
    assert p.hotbar == [None] * 10


def test_hotbar_round_trips_via_dict():
    p = make_profile()
    p.hotbar[0] = "scanner"
    p.hotbar[3] = "nanobots"
    d = p.to_dict()
    p2 = Profile.from_dict(d)
    assert p2.hotbar[0] == "scanner"
    assert p2.hotbar[3] == "nanobots"
    assert p2.hotbar[1] is None


def test_hotbar_from_dict_normalises_short_list():
    d = Profile(name="x").to_dict()
    d["hotbar"] = ["scanner"]  # only 1 entry
    p = Profile.from_dict(d)
    assert len(p.hotbar) == 10
    assert p.hotbar[0] == "scanner"
    assert p.hotbar[1] is None
