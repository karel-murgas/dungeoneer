"""Round-trip tests for dungeoneer.meta persistence layer."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import dungeoneer.meta.storage as storage
from dungeoneer.meta.global_config import GlobalConfig
from dungeoneer.meta.profile import GameplayFlags, LifetimeStats, Profile
from dungeoneer.meta.storage import (
    delete_profile,
    list_profiles,
    load_global,
    load_profile,
    profile_exists,
    sanitize_name,
    save_global,
    save_profile,
)


@pytest.fixture(autouse=True)
def isolated_save_dir(tmp_path, monkeypatch):
    """Redirect all storage operations to a temporary directory."""
    monkeypatch.setattr(storage, "_SAVE_DIR_OVERRIDE", tmp_path)
    yield tmp_path


# ---------------------------------------------------------------------------
# sanitize_name
# ---------------------------------------------------------------------------

def test_sanitize_name_strips_whitespace():
    assert sanitize_name("  Karel  ") == "Karel"


def test_sanitize_name_removes_illegal_chars():
    assert sanitize_name("Ka!@#rel") == "Karel"


def test_sanitize_name_trims_to_24():
    long = "A" * 30
    assert sanitize_name(long) == "A" * 24


def test_sanitize_name_empty_raises():
    with pytest.raises(ValueError):
        sanitize_name("   ")


def test_sanitize_name_all_illegal_raises():
    with pytest.raises(ValueError):
        sanitize_name("!@#$%^")


def test_sanitize_name_allows_allowed_chars():
    assert sanitize_name("Karel_Murgas-99") == "Karel_Murgas-99"


# ---------------------------------------------------------------------------
# Profile round-trip
# ---------------------------------------------------------------------------

def _make_profile(name="TestUser") -> Profile:
    return Profile(name=name, language="cs", difficulty="hard", tutorial_enabled=True)


def test_save_and_load_profile_round_trip():
    p = _make_profile()
    save_profile(p)
    loaded = load_profile("TestUser")
    assert loaded is not None
    assert loaded.name == "TestUser"
    assert loaded.language == "cs"
    assert loaded.difficulty == "hard"
    assert loaded.tutorial_enabled is True


def test_load_profile_returns_none_for_missing():
    assert load_profile("NoSuchProfile") is None


def test_profile_exists_true_after_save():
    p = _make_profile()
    save_profile(p)
    assert profile_exists("TestUser") is True


def test_profile_exists_false_before_save():
    assert profile_exists("Ghost") is False


def test_delete_profile_returns_true_and_file_gone():
    p = _make_profile()
    save_profile(p)
    result = delete_profile("TestUser")
    assert result is True
    assert not profile_exists("TestUser")


def test_delete_profile_returns_false_if_missing():
    assert delete_profile("Nobody") is False


# ---------------------------------------------------------------------------
# list_profiles ordering
# ---------------------------------------------------------------------------

def test_list_profiles_sorted_by_updated_at_desc():
    p1 = Profile(name="Alice")
    p1.updated_at = "2024-01-01T00:00:00+00:00"
    p2 = Profile(name="Bob")
    p2.updated_at = "2025-06-01T00:00:00+00:00"
    save_profile(p1)
    save_profile(p2)
    names = list_profiles()
    assert names[0] == "Bob"
    assert names[1] == "Alice"


def test_list_profiles_empty_when_no_profiles():
    assert list_profiles() == []


# ---------------------------------------------------------------------------
# Missing-key tolerance (forward compat)
# ---------------------------------------------------------------------------

def test_load_profile_tolerates_missing_keys(tmp_path):
    # Write a minimal profile JSON missing most fields
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    minimal = {"name": "Minimal"}
    (profiles_dir / "Minimal.json").write_text(json.dumps(minimal), encoding="utf-8")
    p = load_profile("Minimal")
    assert p is not None
    assert p.name == "Minimal"
    assert p.language == "en"
    assert p.difficulty == "normal"
    assert p.stats.kills_total == 0


def test_load_profile_tolerates_missing_stats_fields(tmp_path):
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    partial = {"name": "Partial", "stats": {"kills_total": 5}}
    (profiles_dir / "Partial.json").write_text(json.dumps(partial), encoding="utf-8")
    p = load_profile("Partial")
    assert p is not None
    assert p.stats.kills_total == 5
    assert p.stats.deaths_total == 0


# ---------------------------------------------------------------------------
# LifetimeStats and GameplayFlags round-trip
# ---------------------------------------------------------------------------

def test_lifetime_stats_round_trip():
    s = LifetimeStats(kills_total=7, kills_by_enemy={"guard": 5, "drone": 2})
    restored = LifetimeStats.from_dict(s.to_dict())
    assert restored.kills_total == 7
    assert restored.kills_by_enemy == {"guard": 5, "drone": 2}


def test_gameplay_flags_round_trip():
    f = GameplayFlags(use_minigame=False, heal_threshold_pct=50)
    restored = GameplayFlags.from_dict(f.to_dict())
    assert restored.use_minigame is False
    assert restored.heal_threshold_pct == 50


# ---------------------------------------------------------------------------
# GlobalConfig round-trip
# ---------------------------------------------------------------------------

def test_save_and_load_global_round_trip():
    cfg = GlobalConfig(master_volume=0.8, last_active_profile="Karel")
    save_global(cfg)
    loaded = load_global()
    assert loaded.master_volume == pytest.approx(0.8)
    assert loaded.last_active_profile == "Karel"


def test_load_global_returns_defaults_if_missing():
    cfg = load_global()
    assert cfg.master_volume == pytest.approx(1.0)
    assert cfg.last_active_profile is None


def test_load_global_tolerates_missing_keys(tmp_path):
    (tmp_path / "global.json").write_text(json.dumps({"sfx_volume": 0.5}), encoding="utf-8")
    cfg = load_global()
    assert cfg.sfx_volume == pytest.approx(0.5)
    assert cfg.master_volume == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Invalid name rejection
# ---------------------------------------------------------------------------

def test_save_profile_raises_on_invalid_name():
    p = Profile(name="!@#")
    with pytest.raises(ValueError):
        save_profile(p)
