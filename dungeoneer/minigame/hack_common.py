"""Shared constants and helpers for hacking minigame scenes."""
from __future__ import annotations

import random
from typing import Optional, TYPE_CHECKING

import pygame

from dungeoneer.minigame.hack_node import LootKind

if TYPE_CHECKING:
    from dungeoneer.items.item import Item


# ---------------------------------------------------------------------------
# Colour palette — neon cyberpunk (shared between classic and grid variants)
# ---------------------------------------------------------------------------
BG            = (4,    8,  18)
GRID_DOT      = (14,  26,  42)
PANEL_BG      = (6,   12,  22)

NEON_CYAN     = (0,   230, 220)
NEON_GREEN    = (0,   220,  80)
NEON_RED      = (220,  40,  80)
NEON_ORANGE   = (220, 140,   0)
NEON_YELLOW   = (200, 220,  60)
NEON_MAGENTA  = (190,  40, 170)

TEXT          = (160, 220, 200)
TEXT_DIM      = (60,  100,  80)
TEXT_GOOD     = NEON_GREEN
TEXT_WARN     = NEON_ORANGE

COL_TIMER_HI  = NEON_GREEN
COL_TIMER_MID = NEON_ORANGE
COL_TIMER_LO  = NEON_RED

BORDER         = NEON_CYAN

# Layout
HEADER_H  = 64
FOOTER_H  = 76


# ---------------------------------------------------------------------------
# Shared drawing helpers
# ---------------------------------------------------------------------------

def draw_corner_bracket(
    screen: pygame.Surface,
    x: int, y: int,
    arm: int, thickness: int,
    color: tuple,
    width: int,
    flip_x: bool = False,
    flip_y: bool = False,
) -> None:
    """Draw an L-shaped corner bracket at (x, y)."""
    dx = -1 if flip_x else 1
    dy = -1 if flip_y else 1
    pygame.draw.line(screen, color, (x, y), (x + dx * arm, y), width)
    pygame.draw.line(screen, color, (x, y), (x, y + dy * thickness), width)


def draw_glow_circle(
    screen: pygame.Surface,
    color: tuple,
    cx: int, cy: int,
    radius: int,
    layers: int = 3,
    max_alpha: int = 80,
) -> None:
    """Draw a soft glow circle (used by grid variant)."""
    size   = (radius + layers * 8) * 2
    surf   = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    for i in range(layers, 0, -1):
        r     = radius + i * 8
        alpha = max_alpha * i // layers
        pygame.draw.circle(surf, (*color, alpha), (center, center), r)
    screen.blit(surf, (cx - center, cy - center))


# ---------------------------------------------------------------------------
# Shared loot factory
# ---------------------------------------------------------------------------

def make_loot_item(kind: LootKind) -> Optional["Item"]:
    """Create a loot item from a LootKind enum value."""
    from dungeoneer.items.ammo import make_9mm_ammo, make_rifle_ammo, make_shotgun_ammo
    from dungeoneer.items.consumable import make_stim_pack, make_medkit
    from dungeoneer.items.weapon import make_shotgun, make_rifle, make_smg
    from dungeoneer.items.armor import make_basic_armor

    if kind == LootKind.AMMO:         return make_9mm_ammo(8)
    if kind == LootKind.RIFLE_AMMO:   return make_rifle_ammo(3)
    if kind == LootKind.SHOTGUN_AMMO: return make_shotgun_ammo(4)
    if kind == LootKind.HEAL:         return make_stim_pack()
    if kind == LootKind.MEDKIT:       return make_medkit()
    if kind == LootKind.WEAPON:       return random.choice([make_shotgun, make_rifle, make_smg])()
    if kind == LootKind.ARMOR:        return make_basic_armor()
    return None
