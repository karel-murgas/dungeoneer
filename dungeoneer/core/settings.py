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
