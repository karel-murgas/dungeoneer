"""Difficulty presets — all tunable numbers in one place."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Difficulty:
    name: str

    # Enemies per floor
    guards_per_floor:     int = 5
    drones_per_floor:     int = 3

    # Containers per floor
    containers_per_floor: int = 3

    # Player starting stats
    player_max_hp:        int  = 30
    player_attack:        int  = 4
    player_defence:       int  = 0
    starting_ammo:        dict = field(default_factory=dict)   # empty = only what's in the gun

    # Credits reward for securing the mission objective (final floor)
    objective_credits:    int  = 150

    # Aiming minigame — needle speed multiplier (applied to AIM_START_SPEED + AIM_ACCEL)
    aim_needle_speed_mult: float = 1.0

    # Player aim_skill used by simulate_aim_enemy when aim minigame is OFF
    player_aim_skill: float = 2.5

    # Melee minigame — oscillation frequency multiplier
    melee_freq_mult: float = 1.0

    # Vault drain minigame — random cursor drift multiplier
    vault_drift_mult: float = 1.0

    # Fraction of non-end rooms that spawn no encounter (higher = more empty rooms)
    empty_room_chance: float = 0.25

    # Healing minigame — timing thresholds (ms).
    # Quality tier = first threshold the sum |press_off| + |release_off| falls below.
    # Tuple: (perfect_ms, great_ms, good_ms, poor_ms); anything ≥ poor_ms → miss.
    heal_timing_thresholds: tuple = (40, 80, 120, 160)   # default = hard


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------

EASY = Difficulty(
    name="Easy",
    guards_per_floor=3,
    drones_per_floor=2,
    containers_per_floor=5,
    player_max_hp=35,
    starting_ammo={"9mm": 8},   # one spare magazine
    objective_credits=400,
    aim_needle_speed_mult=0.65,
    player_aim_skill=4.0,   # mostly hits when minigame is OFF
    melee_freq_mult=0.75,
    heal_timing_thresholds=(100, 200, 300, 400),
    vault_drift_mult=0.7,
    empty_room_chance=0.35,
)

NORMAL = Difficulty(
    name="Normal",
    guards_per_floor=5,
    drones_per_floor=3,
    containers_per_floor=4,
    player_max_hp=30,
    # starting_ammo left empty — only what's already in the pistol
    objective_credits=500,
    heal_timing_thresholds=(70, 140, 210, 280),
)

HARD = Difficulty(
    name="Hard",
    guards_per_floor=7,
    drones_per_floor=4,
    containers_per_floor=3,
    player_max_hp=25,
    objective_credits=600,
    aim_needle_speed_mult=1.35,
    player_aim_skill=1.5,   # more misses when minigame is OFF
    melee_freq_mult=1.3,
    vault_drift_mult=1.3,
    empty_room_chance=0.15,
)
