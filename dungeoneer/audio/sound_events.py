"""Sound event identifiers."""
from enum import auto, Enum


class SoundEvent(Enum):
    FOOTSTEP     = auto()
    MELEE_HIT    = auto()
    PISTOL_SHOT  = auto()
    DRONE_SHOT   = auto()
    HIT_TAKEN    = auto()
    ENEMY_DEATH  = auto()
    PLAYER_DEATH = auto()
    STAIR        = auto()
    RELOAD       = auto()
    NO_AMMO      = auto()
