"""Global constants for Dungeoneer."""

# Localisation — change via dungeoneer.core.i18n.set_language()
# Supported: "en", "cs", "es"
LANGUAGE = "en"

# Display
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "Dungeoneer"

# Tiles
TILE_SIZE = 32          # pixels per tile
MAP_WIDTH = 50          # tiles wide
MAP_HEIGHT = 50         # tiles tall

# Dungeon generation
STAIR_FARTHEST_CANDIDATES = 5   # stairs/vault placed in one of N farthest rooms from start

# Map size presets  ("large" = current default, "small" = compact ~60 % area)
MAP_WIDTH_SMALL  = 32
MAP_HEIGHT_SMALL = 32

# Audio volumes (0.0 – 1.0); adjusted from settings overlay
MASTER_VOLUME: float = 1.0    # overall multiplier applied to all audio
MUSIC_VOLUME:  float = 0.30   # max volume for music tracks
SFX_VOLUME:    float = 1.0    # max volume for SFX

# Colours (fallback placeholder rendering)
COL_BLACK       = (0,   0,   0)
COL_WHITE       = (255, 255, 255)
COL_WALL        = (40,  40,  55)
COL_WALL_DARK   = (20,  20,  28)
COL_FLOOR       = (60,  55,  70)
COL_FLOOR_DARK  = (25,  22,  30)
COL_STAIR       = (80,  200, 180)
COL_STAIR_DARK  = (30,  80,  70)
COL_PLAYER      = (0,   220, 180)   # cyan-green
COL_GUARD       = (220, 60,  60)    # red
COL_DRONE       = (220, 160, 40)    # amber
COL_DOG         = (200, 80,  40)    # dark orange
COL_HEAVY       = (140, 80,  220)   # violet
COL_TURRET      = (80,  100, 200)   # steel blue
COL_SNIPER      = (180, 220, 40)    # yellow-green
COL_RIOT_GUARD  = (220, 80,  40)    # orange-red
COL_ITEM        = (240, 220, 80)    # yellow
COL_HP_FULL     = (60,  200, 80)
COL_HP_LOW      = (220, 60,  60)

# FOV
FOV_RADIUS = 10

# Combat
BASE_MELEE_DAMAGE   = 4
BASE_RANGED_DAMAGE  = 5
DRONE_PREFERRED_DIST = 4    # tiles drone tries to stay away

# Aiming minigame
AIM_ARC_DEGREES:    float = 90.0   # arc span in degrees — adjust for different "feel"
AIM_MIN_ZONE:       float = 5.0    # minimum hit zone size (floor) in degrees
AIM_START_SPEED:       float = 78.4   # °/s at start
AIM_BOUNCE_SPEED_BOOST: float = 0.50  # fraction of start_speed added on each bounce off arc end
AIM_CRIT_THRESHOLD: float = 0.95   # accuracy >= this value = critical hit
AIM_RESULT_PAUSE:   float = 0.3    # seconds to display shot result
AIM_RADIUS_PX:      int   = 64     # arc radius in pixels (~2 tiles)

# Enemy aim simulation — normal distribution model
# mean = max(0, AIM_SIM_MEAN_BASE - distance * AIM_SIM_MEAN_SLOPE)
# sigma = 1.0 / enemy.aim_skill   (higher skill = lower sigma = tighter grouping)
AIM_SIM_MEAN_BASE:  float = 0.70   # mean accuracy at distance 0
AIM_SIM_MEAN_SLOPE: float = 0.05   # mean accuracy reduction per tile of distance

# Healing rhythm minigame
HEAL_MIN_CYCLE_MS:    int   = 550   # fastest heartbeat (ms between beat starts)
HEAL_MAX_CYCLE_MS:    int   = 950   # slowest heartbeat
HEAL_MIN_DU_GAP_MS:   int   = 140   # shortest DU→DUM gap (ms)
HEAL_MAX_DU_GAP_MS:   int   = 280   # longest DU→DUM gap (ms)
HEAL_BEAT_FLASH_MS:   int   = 110   # visual flash duration (ms)
HEAL_ACCURACY_WINDOW: float = 0.25  # ±window in seconds (full accuracy at 0, none at ±window/2)
HEAL_RESULT_PAUSE:    float = 0.9   # seconds to show result before closing
HEAL_RANGE:           float = 0.20  # ±20% modifier range (0.8× to 1.2× base)

# Melee power-charge minigame
MELEE_FREQ1:          float = 1.1    # Hz — primary oscillation frequency
MELEE_FREQ2:          float = 0.7    # Hz — secondary frequency (creates beating pattern)
MELEE_TIMEOUT:        float = 3.0    # seconds before auto-release
MELEE_CRIT_THRESHOLD: float = 0.92   # power >= this = critical hit
MELEE_RESULT_PAUSE:   float = 0.35   # seconds to display result
MELEE_BAR_W:          int   = 120    # power bar width in pixels
MELEE_BAR_H:          int   = 12     # power bar height in pixels

# Visual experiment — press P in hack minigame to toggle all custom PNG icons at once
HACK_WEAPON_USE_PNG: bool = False   # True = custom PNGs for weapon + ammo nodes; False = procedural

# Heat mechanic
HEAT_PER_LEVEL:        int   = 100   # points to fill one heat level bar (levels 1–5)
HEAT_MAX_LEVEL:        int   = 5
HEAT_COMBAT_ROUND:     int   = 1     # heat gained per combat round (TurnEndEvent)
HEAT_HACK_NODE:        int   = 2     # heat per hacked loot node (applied at hack end)
HEAT_HACK_FAIL:        int   = 10    # heat on failed hack (applied at hack end)
HEAT_COOLANT_REDUCE:   int   = 12    # heat removed by a COOLANT node (applied at hack end)
HEAT_HACK_TIME_OFFSET: float = 2.0   # seconds added at level 1; formula: (2 − level) seconds
HEAT_HACK_TIME_FLOOR:  float = 4.0   # minimum time_limit (hard + high heat)
HEAT_PATROL_COUNT:     tuple = (1, 2) # (min, max) enemies in a heat-triggered patrol

# Vault drain minigame
VAULT_CHECK_INTERVAL:    float = 1.0    # seconds between position checks
VAULT_IMPULSE:           float = 3.0    # velocity added per frame while key held (strong push, needs dosing)
VAULT_DAMPING:           float = 0.960  # velocity damping per frame — low = momentum/overshoot
VAULT_DRIFT_SIGMA:       float = 0.3    # base random drift (frame noise, cancels out quickly)
VAULT_DRIFT_HEAT_SCALE:  float = 0.35   # drift+spring increase per heat level above 1
VAULT_DRIFT_FINALE_MULT: float = 1.0    # disabled — heat scaling handles late-game difficulty naturally
VAULT_OUTWARD_BIAS:      float = 1.2    # anti-spring: pushes cursor away from centre (sqrt-scaled, main force)
VAULT_DRIFT_SPEED_VARY:  float = 0.60   # amplitude of oscillating drift-speed multiplier (0 = constant)
VAULT_DRIFT_SPEED_FREQ:  float = 0.45   # Hz of drift-speed oscillation cycle
VAULT_WIND_SIGMA:        float = 1.5    # how fast the persistent wind changes each frame
VAULT_WIND_DAMPING:      float = 0.990  # wind persistence per frame
VAULT_ZONE_PERFECT:      float = 0.06   # |pos-0.5| threshold for Perfect (tight)
VAULT_ZONE_GOOD:         float = 0.15   # |pos-0.5| threshold for Good
VAULT_ZONE_BAD:          float = 0.30   # |pos-0.5| threshold for Bad
VAULT_DRAIN_SECONDS:     float = 30.0   # base time for full drain at 1.0x mult
VAULT_MULT_MIN:          float = 0.   # minimum drain multiplier
VAULT_MULT_MAX:          float = 2.0    # maximum — perfect play sustains full speed, bad slows down
VAULT_FULL_DRAIN_BONUS:  float = 0.25   # +25% credits for draining everything
VAULT_RESULT_PAUSE:      float = 0.8    # seconds to show result before closing

# Heat per vault check by zone
VAULT_HEAT_PERFECT:      int = 6
VAULT_HEAT_GOOD:         int = 7
VAULT_HEAT_BAD:          int = 9
VAULT_HEAT_FAIL:         int = 12

# Multiplier changes per vault check by zone
VAULT_MULT_PERFECT:      float =  0.15
VAULT_MULT_GOOD:         float =  0.00
VAULT_MULT_BAD:          float = -0.15
VAULT_MULT_FAIL:         float = -0.30

# Encounter system (dynamic room-reveal spawning)
ENCOUNTER_MIN_ROOM_AREA:   int   = 9     # inner tiles below this → no encounter
ENCOUNTER_PACK_CHANCE:     float = 0.40  # probability of pack branch at heat 3+
ENCOUNTER_T3_CHANCE_AT_H4: float = 0.10  # chance to unlock tier 3 at heat 4
