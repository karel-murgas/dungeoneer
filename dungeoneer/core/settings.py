"""Global constants for Dungeoneer."""

# Localisation — change via dungeoneer.core.i18n.set_language()
# Supported: "en", "cs"
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
COL_ITEM        = (240, 220, 80)    # yellow
COL_HP_FULL     = (60,  200, 80)
COL_HP_LOW      = (220, 60,  60)
COL_LOG_BG      = (10,  10,  18,  200)  # semi-transparent

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
MELEE_FREQ_ACCEL:     float = 0.0    # Hz/s — kept for compatibility; oscillation no longer accelerates
MELEE_TIMEOUT:        float = 3.0    # seconds before auto-release
MELEE_CRIT_THRESHOLD: float = 0.92   # power >= this = critical hit
MELEE_RESULT_PAUSE:   float = 0.35   # seconds to display result
MELEE_BAR_W:          int   = 120    # power bar width in pixels
MELEE_BAR_H:          int   = 12     # power bar height in pixels
