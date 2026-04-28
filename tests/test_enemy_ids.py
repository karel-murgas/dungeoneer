"""Session 0 verification: every enemy factory produces a stable enemy_id."""
from dungeoneer.entities.enemy import (
    make_guard, make_drone, make_dog,
    make_heavy, make_turret, make_sniper_drone, make_riot_guard,
)

_EXPECTED = [
    (make_guard,        "guard"),
    (make_drone,        "drone"),
    (make_dog,          "dog"),
    (make_heavy,        "heavy"),
    (make_turret,       "turret"),
    (make_sniper_drone, "sniper_drone"),
    (make_riot_guard,   "riot_guard"),
]


def test_all_factories_have_enemy_id():
    for factory, expected_id in _EXPECTED:
        enemy = factory(0, 0)
        assert hasattr(enemy, "enemy_id"), f"{factory.__name__} missing enemy_id"
        assert enemy.enemy_id == expected_id, (
            f"{factory.__name__}: expected {expected_id!r}, got {enemy.enemy_id!r}"
        )


def test_all_enemy_ids_are_unique():
    ids = [factory(0, 0).enemy_id for factory, _ in _EXPECTED]
    assert len(ids) == len(set(ids)), f"Duplicate enemy_ids: {ids}"


def test_enemy_id_matches_i18n_key_pattern():
    """enemy_id must match entity.<id>.name keys already in i18n."""
    from dungeoneer.core.i18n import t
    for factory, expected_id in _EXPECTED:
        key = f"entity.{expected_id}.name"
        resolved = t(key)
        assert resolved != key, (
            f"i18n key {key!r} missing — t() fell back to raw key"
        )
