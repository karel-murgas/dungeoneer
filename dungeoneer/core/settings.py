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
MAP_WIDTH = 60          # tiles wide
MAP_HEIGHT = 40         # tiles tall

# Dungeon generation
STAIR_FARTHEST_CANDIDATES = 5   # stairs/vault placed in one of N farthest rooms from start

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
