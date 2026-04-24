"""Procedurally-generated placeholder sprites.

All surfaces are 32×32 RGBA and cached after first creation so they are only
built once per pygame session.  Call get(key) to retrieve a surface; valid
keys are defined in _BUILDERS at the bottom of this module.
"""
from __future__ import annotations

import math
import pygame

_CACHE: dict[str, pygame.Surface] = {}
_TS = 32  # tile / sprite size


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def _make_wall_tile(dark: bool = False) -> pygame.Surface:
    """Sci-fi metal panel wall tile.

    Two shades: normal (visible) and dark (explored-but-foggy). The panel has
    a recessed inner face, corner bolts, a horizontal seam, and a top-left
    highlight to suggest depth — all consistent with the Dithart colour range.
    """
    surf = pygame.Surface((_TS, _TS))

    base  = (22, 20, 30) if dark else (32, 29, 42)
    panel = (28, 25, 37) if dark else (40, 37, 52)
    bolt  = (40, 37, 55) if dark else (62, 58, 78)
    hi    = (42, 39, 56) if dark else (68, 64, 88)

    surf.fill(base)
    # Recessed inner panel
    pygame.draw.rect(surf, panel, (2, 2, _TS - 4, _TS - 4))
    # Horizontal seam at midpoint
    pygame.draw.line(surf, base, (3, _TS // 2), (_TS - 4, _TS // 2))
    # Corner bolts (2×2)
    for bx, by in [(3, 3), (_TS - 5, 3), (3, _TS - 5), (_TS - 5, _TS - 5)]:
        pygame.draw.rect(surf, bolt, (bx, by, 2, 2))
    # Top/left edge highlight
    pygame.draw.line(surf, hi, (1, 1), (_TS - 2, 1))
    pygame.draw.line(surf, hi, (1, 1), (1, _TS - 2))

    return surf


def _make_actor_sprite(body_col: tuple, accent_col: tuple) -> pygame.Surface:
    """Generic top-down humanoid sprite: dark armoured body with colour accents.

    Structure (top-down view):
      • Faint glow halo in the accent colour
      • Dark disc body with a 1-px accent rim
      • Bright accent visor/head dot (with white highlight)
      • Two shoulder accent bars
    """
    surf = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    cx = cy = _TS // 2

    # Glow halo
    glow = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    r, g, b = accent_col[:3]
    pygame.draw.circle(glow, (r, g, b, 35), (cx, cy), 13)
    surf.blit(glow, (0, 0))

    # Armoured body disc
    pygame.draw.circle(surf, (20, 18, 28), (cx, cy), 10)
    pygame.draw.circle(surf, body_col, (cx, cy), 10, 1)

    # Visor / helmet (bright dot slightly above centre)
    pygame.draw.circle(surf, accent_col, (cx, cy - 3), 4)
    pygame.draw.circle(surf, (220, 240, 255), (cx - 1, cy - 4), 1)  # specular

    # Shoulder pauldrons
    pygame.draw.rect(surf, body_col, (cx - 8, cy + 3, 4, 3))
    pygame.draw.rect(surf, body_col, (cx + 4, cy + 3, 4, 3))

    return surf


def _make_player_sprite() -> pygame.Surface:
    """Diver — cyan-green hacker aesthetic."""
    return _make_actor_sprite(
        body_col=(0, 155, 135),
        accent_col=(0, 220, 180),
    )


def _make_guard_sprite() -> pygame.Surface:
    """Corp Guard — armoured in corporate red."""
    return _make_actor_sprite(
        body_col=(175, 38, 38),
        accent_col=(220, 60, 60),
    )


def _make_dog_sprite() -> pygame.Surface:
    """K9 Unit — low quadruped silhouette, orange-brown, fast and scrappy."""
    surf = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    cx, cy = _TS // 2, _TS // 2

    # Glow halo — warm orange
    glow = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    pygame.draw.circle(glow, (200, 80, 40, 35), (cx, cy), 11)
    surf.blit(glow, (0, 0))

    # Body — low oval (wider than tall = crouched quadruped)
    pygame.draw.ellipse(surf, (20, 15, 10), (cx - 9, cy - 5, 18, 11))
    pygame.draw.ellipse(surf, (200, 80, 40), (cx - 9, cy - 5, 18, 11), 1)

    # Head — small circle front-left
    pygame.draw.circle(surf, (22, 16, 10), (cx - 5, cy - 4), 4)
    pygame.draw.circle(surf, (200, 80, 40), (cx - 5, cy - 4), 4, 1)

    # Eyes — two bright orange dots
    pygame.draw.circle(surf, (255, 140, 30), (cx - 7, cy - 5), 1)
    pygame.draw.circle(surf, (255, 140, 30), (cx - 4, cy - 5), 1)

    # Legs — four short rects
    for lx in (cx - 8, cx - 4, cx + 1, cx + 5):
        pygame.draw.rect(surf, (160, 65, 30), (lx, cy + 5, 2, 4))

    # Tail — short line at rear
    pygame.draw.line(surf, (200, 80, 40), (cx + 8, cy - 3), (cx + 11, cy - 6), 2)

    return surf


def _make_heavy_sprite() -> pygame.Surface:
    """Heavy Enforcer — bulky armoured ranged unit, violet with silver plating."""
    surf = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    cx, cy = _TS // 2, _TS // 2

    # Glow halo — violet
    glow = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    pygame.draw.circle(glow, (140, 80, 220, 35), (cx, cy), 13)
    surf.blit(glow, (0, 0))

    # Larger armoured body (12 r instead of 10)
    pygame.draw.circle(surf, (20, 15, 30), (cx, cy), 12)
    pygame.draw.circle(surf, (140, 80, 220), (cx, cy), 12, 2)

    # Chest plate (rectangular, silver)
    pygame.draw.rect(surf, (55, 48, 72), (cx - 5, cy - 2, 10, 8))
    pygame.draw.rect(surf, (175, 165, 200), (cx - 5, cy - 2, 10, 8), 1)

    # Visor — violet, wider than guard
    pygame.draw.ellipse(surf, (140, 80, 220), (cx - 4, cy - 6, 8, 4))
    pygame.draw.circle(surf, (210, 180, 255), (cx - 1, cy - 5), 1)  # specular

    # Heavy pauldrons — wider shoulder bars
    pygame.draw.rect(surf, (100, 80, 140), (cx - 11, cy + 2, 5, 4))
    pygame.draw.rect(surf, (100, 80, 140), (cx + 6,  cy + 2, 5, 4))

    return surf


def _make_turret_sprite() -> pygame.Surface:
    """Auto-Turret — immobile weapon mount, steel blue, barrel pointing right."""
    surf = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    cx, cy = _TS // 2, _TS // 2

    # Glow halo — steel blue
    glow = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    pygame.draw.circle(glow, (80, 100, 200, 40), (cx, cy), 12)
    surf.blit(glow, (0, 0))

    # Base mount — dark octagon-ish (use polygon)
    pygame.draw.circle(surf, (18, 22, 42), (cx, cy), 10)
    pygame.draw.circle(surf, (80, 100, 200), (cx, cy), 10, 2)

    # Rotating turret head — slightly smaller inner disc
    pygame.draw.circle(surf, (28, 34, 62), (cx, cy), 6)
    pygame.draw.circle(surf, (110, 135, 220), (cx, cy), 6, 1)

    # Barrel — pointing right
    pygame.draw.rect(surf, (60, 75, 140), (cx + 5, cy - 2, 9, 4))
    pygame.draw.rect(surf, (130, 155, 230), (cx + 5, cy - 2, 9, 4), 1)

    # Muzzle tip — bright dot
    pygame.draw.circle(surf, (200, 220, 255), (cx + 13, cy), 1)

    # Side vents (left side)
    for vy in (cy - 3, cy, cy + 3):
        pygame.draw.line(surf, (70, 90, 165), (cx - 10, vy), (cx - 7, vy), 1)

    return surf


def _make_sniper_drone_sprite() -> pygame.Surface:
    """Sniper Drone — elongated body with rifle barrel, yellow-green glow."""
    surf = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    cx, cy = _TS // 2, _TS // 2

    # Glow halo — yellow-green
    glow = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    pygame.draw.circle(glow, (180, 220, 40, 38), (cx, cy), 12)
    surf.blit(glow, (0, 0))

    # Elongated drone body (horizontal ellipse)
    pygame.draw.ellipse(surf, (20, 25, 10), (cx - 9, cy - 5, 18, 10))
    pygame.draw.ellipse(surf, (180, 220, 40), (cx - 9, cy - 5, 18, 10), 1)

    # Sensor eye — centre, bright lime
    pygame.draw.circle(surf, (180, 220, 40), (cx, cy), 3)
    pygame.draw.circle(surf, (230, 255, 100), (cx - 1, cy - 1), 1)  # specular

    # Long rifle barrel extending right
    pygame.draw.rect(surf, (40, 50, 20), (cx + 8, cy - 1, 11, 3))
    pygame.draw.rect(surf, (180, 220, 40), (cx + 8, cy - 1, 11, 3), 1)

    # Stabiliser fins — top and bottom
    pygame.draw.line(surf, (140, 180, 30), (cx - 4, cy - 5), (cx - 1, cy - 8), 2)
    pygame.draw.line(surf, (140, 180, 30), (cx - 4, cy + 4), (cx - 1, cy + 7), 2)

    return surf


def _make_riot_guard_sprite() -> pygame.Surface:
    """Riot Guard — heavily armoured melee, orange-red with thick shield plating."""
    surf = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    cx, cy = _TS // 2, _TS // 2

    # Glow halo — orange-red
    glow = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    pygame.draw.circle(glow, (220, 80, 40, 38), (cx, cy), 13)
    surf.blit(glow, (0, 0))

    # Heavy body disc
    pygame.draw.circle(surf, (22, 12, 8), (cx, cy), 12)
    pygame.draw.circle(surf, (220, 80, 40), (cx, cy), 12, 2)

    # Large shield panel (left side — rectangular)
    pygame.draw.rect(surf, (40, 22, 14), (cx - 13, cy - 7, 7, 14))
    pygame.draw.rect(surf, (220, 80, 40), (cx - 13, cy - 7, 7, 14), 1)
    # Shield highlight
    pygame.draw.line(surf, (255, 140, 80), (cx - 12, cy - 5), (cx - 12, cy + 4), 1)

    # Riot visor — full-width dark slit
    pygame.draw.rect(surf, (12, 8, 4), (cx - 6, cy - 5, 12, 3))
    pygame.draw.rect(surf, (220, 80, 40), (cx - 6, cy - 5, 12, 3), 1)
    # Visor red glow slit
    pygame.draw.line(surf, (255, 100, 50), (cx - 5, cy - 4), (cx + 4, cy - 4), 1)

    # Right pauldron (weapon arm side)
    pygame.draw.rect(surf, (160, 55, 28), (cx + 7, cy + 2, 5, 4))

    return surf


def _make_container_closed() -> pygame.Surface:
    """Wall-mounted supply locker — locked, cyan LED indicator."""
    surf = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    T = _TS  # 32

    # Subtle cyan glow
    glow = pygame.Surface((T, T), pygame.SRCALPHA)
    pygame.draw.rect(glow, (0, 190, 190, 22), (2, 3, T - 4, T - 5))
    surf.blit(glow, (0, 0))

    # Top face (viewed slightly from above — lighter strip)
    pygame.draw.rect(surf, (35, 70, 70), (2, 3, T - 4, 6))
    # Main body
    pygame.draw.rect(surf, (26, 53, 53), (2, 8, T - 4, T - 11))
    # Outer border — bright cyan
    pygame.draw.rect(surf, (0, 200, 200), (2, 3, T - 4, T - 6), 1)
    # Seam between top face and door
    pygame.draw.line(surf, (0, 200, 200), (2, 9), (T - 3, 9))

    # Lock panel (centre of door)
    cx = T // 2
    pygame.draw.rect(surf, (15, 35, 35), (cx - 5, 14, 10, 8))
    pygame.draw.rect(surf, (0, 130, 130), (cx - 5, 14, 10, 8), 1)

    # LED dot — bright cyan = locked
    pygame.draw.rect(surf, (0, 232, 232), (cx - 1, 17, 3, 3))
    glow2 = pygame.Surface((7, 7), pygame.SRCALPHA)
    pygame.draw.rect(glow2, (0, 220, 220, 40), (0, 0, 7, 7))
    surf.blit(glow2, (cx - 3, 15))

    return surf


def _make_container_open() -> pygame.Surface:
    """Wall-mounted supply locker — opened / looted, dim."""
    surf = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    T = _TS

    pygame.draw.rect(surf, (18, 36, 36), (2, 3, T - 4, 6))
    pygame.draw.rect(surf, (14, 28, 28), (2, 8, T - 4, T - 11))
    pygame.draw.rect(surf, (0, 70, 70), (2, 3, T - 4, T - 6), 1)
    pygame.draw.line(surf, (0, 70, 70), (2, 9), (T - 3, 9))

    cx = T // 2
    pygame.draw.rect(surf, (10, 22, 22), (cx - 5, 14, 10, 8))
    pygame.draw.rect(surf, (0, 50, 50), (cx - 5, 14, 10, 8), 1)
    # LED off
    pygame.draw.rect(surf, (0, 40, 40), (cx - 1, 17, 3, 3))

    return surf


def _make_item_loot() -> pygame.Surface:
    """Item on the floor — glowing amber diamond (generic fallback)."""
    surf = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    cx, cy = _TS // 2, _TS // 2

    # Outer glow
    glow = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    pygame.draw.polygon(glow, (240, 215, 55, 45), [
        (cx, cy - 11), (cx + 11, cy), (cx, cy + 11), (cx - 11, cy),
    ])
    surf.blit(glow, (0, 0))

    # Diamond fill
    pygame.draw.polygon(surf, (195, 160, 38), [
        (cx, cy - 7), (cx + 7, cy), (cx, cy + 7), (cx - 7, cy),
    ])
    # Diamond border
    pygame.draw.polygon(surf, (255, 230, 80), [
        (cx, cy - 7), (cx + 7, cy), (cx, cy + 7), (cx - 7, cy),
    ], 1)
    # Specular highlight
    pygame.draw.circle(surf, (255, 248, 180), (cx - 1, cy - 2), 2)

    return surf


def _make_item_loot_melee() -> pygame.Surface:
    """Melee weapon on the floor — diagonal knife, silver blade, blue glow."""
    surf = pygame.Surface((_TS, _TS), pygame.SRCALPHA)

    glow = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    pygame.draw.circle(glow, (100, 180, 255, 38), (16, 16), 11)
    surf.blit(glow, (0, 0))

    # Blade: wide diamond-tipped polygon from top-left to centre
    blade_pts = [(7, 9), (9, 7), (21, 17), (21, 19), (19, 21), (17, 21)]
    pygame.draw.polygon(surf, (175, 188, 210), blade_pts)
    pygame.draw.polygon(surf, (225, 238, 255), blade_pts, 1)
    # Edge highlight along the top face
    pygame.draw.line(surf, (255, 255, 255), (9, 8), (19, 18), 1)

    # Guard (cross-piece)
    pygame.draw.rect(surf, (120, 110, 90), (17, 17, 5, 5))
    pygame.draw.rect(surf, (155, 145, 120), (17, 17, 5, 5), 1)

    # Handle
    handle_pts = [(21, 21), (23, 19), (27, 25), (25, 27)]
    pygame.draw.polygon(surf, (65, 50, 35), handle_pts)
    pygame.draw.line(surf, (105, 80, 55), (22, 21), (25, 26), 1)

    return surf


def _make_item_loot_ranged() -> pygame.Surface:
    """Ranged weapon on the floor — top-down gun silhouette, cyan glow."""
    surf = pygame.Surface((_TS, _TS), pygame.SRCALPHA)

    glow = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    pygame.draw.circle(glow, (0, 220, 180, 35), (16, 16), 11)
    surf.blit(glow, (0, 0))

    # Barrel (horizontal)
    pygame.draw.rect(surf, (55, 55, 70), (6, 13, 17, 5))
    pygame.draw.rect(surf, (85, 85, 105), (6, 13, 17, 5), 1)
    # Receiver / slide (slightly taller block)
    pygame.draw.rect(surf, (68, 68, 84), (14, 11, 9, 9))
    pygame.draw.rect(surf, (95, 95, 115), (14, 11, 9, 9), 1)
    # Grip (angled down from receiver)
    pygame.draw.rect(surf, (50, 50, 65), (17, 19, 5, 7))
    pygame.draw.rect(surf, (78, 78, 98), (17, 19, 5, 7), 1)
    # Muzzle flash hint
    pygame.draw.line(surf, (120, 210, 255), (6, 14), (6, 17), 1)
    # Sight dot (cyan)
    pygame.draw.rect(surf, (0, 220, 180), (20, 12, 2, 2))

    return surf


def _make_item_loot_ammo() -> pygame.Surface:
    """Ammo on the floor — three brass bullet casings."""
    surf = pygame.Surface((_TS, _TS), pygame.SRCALPHA)

    glow = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    pygame.draw.circle(glow, (215, 155, 25, 38), (16, 16), 10)
    surf.blit(glow, (0, 0))

    for bx in (9, 16, 23):
        # Casing
        pygame.draw.ellipse(surf, (155, 95, 28), (bx - 2, 13, 5, 9))
        pygame.draw.ellipse(surf, (195, 140, 50), (bx - 2, 13, 5, 9), 1)
        # Bullet tip (brass-yellow cap)
        pygame.draw.ellipse(surf, (215, 185, 55), (bx - 1, 11, 3, 5))
        # Rim (base)
        pygame.draw.line(surf, (220, 170, 60), (bx - 2, 22), (bx + 2, 22), 1)

    return surf


def _make_vault_closed() -> pygame.Surface:
    """Corp Vault — objective container. Heavy blue-steel safe with pulsing cyan glow."""
    surf = pygame.Surface((_TS, _TS), pygame.SRCALPHA)

    # Wide outer glow
    glow = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    pygame.draw.rect(glow, (30, 160, 255, 45), (1, 2, _TS - 2, _TS - 4))
    surf.blit(glow, (0, 0))

    # Safe body — dark steel blue
    pygame.draw.rect(surf, (18, 28, 52), (3, 4, _TS - 6, _TS - 8))
    # Body border — bright cyan
    pygame.draw.rect(surf, (40, 190, 255), (3, 4, _TS - 6, _TS - 8), 1)

    # Corner reinforcement brackets
    for bx, by, dx, dy in [
        (3, 4, 1, 1), (_TS - 6, 4, -1, 1),
        (3, _TS - 8, 1, -1), (_TS - 6, _TS - 8, -1, -1),
    ]:
        pygame.draw.line(surf, (100, 220, 255), (bx, by), (bx + dx * 4, by), 2)
        pygame.draw.line(surf, (100, 220, 255), (bx, by), (bx, by + dy * 4), 2)

    # Central vault wheel (concentric circles)
    cx, cy = _TS // 2, _TS // 2 + 1
    pygame.draw.circle(surf, (25, 80, 150), (cx, cy), 6)
    pygame.draw.circle(surf, (40, 190, 255), (cx, cy), 6, 1)
    pygame.draw.circle(surf, (40, 190, 255), (cx, cy), 3, 1)
    # Spokes (4-way)
    for dx2, dy2 in [(0, -6), (0, 6), (-6, 0), (6, 0)]:
        pygame.draw.line(surf, (40, 190, 255), (cx, cy), (cx + dx2, cy + dy2), 1)

    # Top label bar
    pygame.draw.rect(surf, (22, 55, 105), (5, 5, _TS - 10, 4))
    pygame.draw.line(surf, (60, 140, 220), (6, 7), (_TS - 7, 7), 1)

    return surf


def _make_vault_open() -> pygame.Surface:
    """Corp Vault — looted/opened. Door ajar, dim glow, contents gone."""
    surf = pygame.Surface((_TS, _TS), pygame.SRCALPHA)

    # Dim glow
    glow = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    pygame.draw.rect(glow, (20, 80, 140, 25), (1, 2, _TS - 2, _TS - 4))
    surf.blit(glow, (0, 0))

    # Body — very dark
    pygame.draw.rect(surf, (10, 16, 30), (3, 4, _TS - 6, _TS - 8))
    pygame.draw.rect(surf, (30, 70, 120), (3, 4, _TS - 6, _TS - 8), 1)

    # Open door panel (rotated out to the left side)
    pygame.draw.rect(surf, (18, 35, 65), (3, 4, 5, _TS - 8))
    pygame.draw.rect(surf, (35, 90, 150), (3, 4, 5, _TS - 8), 1)

    # Dark interior
    pygame.draw.rect(surf, (6, 10, 20), (8, 5, _TS - 11, _TS - 10))

    # Dim wheel remains
    cx, cy = _TS // 2 + 1, _TS // 2 + 1
    pygame.draw.circle(surf, (20, 50, 90), (cx, cy), 5, 1)
    pygame.draw.circle(surf, (20, 50, 90), (cx, cy), 2, 1)

    return surf


def _make_item_loot_armor() -> pygame.Surface:
    """Armor on the floor — top-down tactical vest, olive-green with plate detail."""
    surf = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    cx, cy = _TS // 2, _TS // 2

    # Subtle green glow
    glow = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    pygame.draw.circle(glow, (80, 160, 60, 38), (cx, cy), 11)
    surf.blit(glow, (0, 0))

    # Main vest body (trapezoid-ish, top-down view)
    body_pts = [(cx - 7, cy - 5), (cx + 7, cy - 5),
                (cx + 9, cy + 6), (cx - 9, cy + 6)]
    pygame.draw.polygon(surf, (52, 72, 38), body_pts)
    pygame.draw.polygon(surf, (90, 120, 60), body_pts, 1)

    # Chest plate (central rectangle — slightly lighter)
    pygame.draw.rect(surf, (68, 95, 48), (cx - 4, cy - 3, 8, 7))
    pygame.draw.rect(surf, (105, 145, 70), (cx - 4, cy - 3, 8, 7), 1)

    # Shoulder straps
    pygame.draw.rect(surf, (42, 60, 28), (cx - 9, cy - 7, 4, 4))
    pygame.draw.rect(surf, (42, 60, 28), (cx + 5, cy - 7, 4, 4))
    pygame.draw.rect(surf, (75, 105, 50), (cx - 9, cy - 7, 4, 4), 1)
    pygame.draw.rect(surf, (75, 105, 50), (cx + 5, cy - 7, 4, 4), 1)

    # Central clasp dot
    pygame.draw.circle(surf, (140, 190, 90), (cx, cy + 1), 2)

    return surf


def _make_item_loot_consumable() -> pygame.Surface:
    """Consumable on the floor — green medkit cross with glow."""
    surf = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    cx, cy = _TS // 2, _TS // 2

    glow = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    pygame.draw.circle(glow, (0, 200, 80, 42), (cx, cy), 11)
    surf.blit(glow, (0, 0))

    # Dark background tile
    pygame.draw.rect(surf, (16, 38, 22), (cx - 7, cy - 7, 14, 14))
    pygame.draw.rect(surf, (0, 145, 58), (cx - 7, cy - 7, 14, 14), 1)

    # Cross arms
    pygame.draw.rect(surf, (0, 200, 80), (cx - 5, cy - 2, 10, 4))   # horizontal
    pygame.draw.rect(surf, (0, 200, 80), (cx - 2, cy - 5, 4, 10))   # vertical

    # Highlight on cross
    pygame.draw.line(surf, (140, 255, 170), (cx - 4, cy - 1), (cx + 3, cy - 1), 1)

    return surf


# ---------------------------------------------------------------------------
def _make_item_hack_credits() -> pygame.Surface:
    """Hack loot: credits — gold glow disc with ¥ character centered."""
    surf = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    cx, cy = _TS // 2, _TS // 2

    glow = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    pygame.draw.circle(glow, (220, 180, 20, 45), (cx, cy), 12)
    surf.blit(glow, (0, 0))

    pygame.draw.circle(surf, (35, 28, 6), (cx, cy), 9)
    pygame.draw.circle(surf, (200, 160, 25), (cx, cy), 9, 2)

    font = pygame.font.SysFont("consolas", 13, bold=True)
    sym = font.render("\u00a5", True, (255, 215, 50))
    surf.blit(sym, (cx - sym.get_width() // 2, cy - sym.get_height() // 2 + 2))

    return surf


def _make_item_hack_bonus_time() -> pygame.Surface:
    """Hack loot: bonus time — cyan clock face with hour and minute hands."""
    surf = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    cx, cy = _TS // 2, _TS // 2

    glow = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    pygame.draw.circle(glow, (50, 170, 255, 45), (cx, cy), 12)
    surf.blit(glow, (0, 0))

    pygame.draw.circle(surf, (8, 20, 40), (cx, cy), 8)
    pygame.draw.circle(surf, (60, 155, 255), (cx, cy), 8, 2)

    col = (140, 210, 255)
    # Hour hand pointing toward 12 (straight up)
    pygame.draw.line(surf, col, (cx, cy), (cx, cy - 5), 2)
    # Minute hand pointing toward 3 (right)
    pygame.draw.line(surf, col, (cx, cy), (cx + 5, cy), 1)
    pygame.draw.circle(surf, (255, 255, 255), (cx, cy), 1)

    return surf


def _make_item_hack_coolant() -> pygame.Surface:
    """Hack loot: coolant / trace purge — teal hexagon with downward-sweep arrow."""
    surf = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    cx, cy = _TS // 2, _TS // 2
    _TEAL = (0, 210, 200)
    _TEAL_DIM = (0, 100, 100)
    _TEAL_GLOW = (0, 210, 200, 40)

    # Glow halo
    glow = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    pygame.draw.circle(glow, _TEAL_GLOW, (cx, cy), 13)
    surf.blit(glow, (0, 0))

    # Hexagon outline (flat-top, 6 vertices)
    r = 9
    pts = [(cx + round(r * math.cos(math.radians(60 * i - 30))),
            cy + round(r * math.sin(math.radians(60 * i - 30))))
           for i in range(6)]
    pygame.draw.polygon(surf, (8, 30, 32), pts)     # dark fill
    pygame.draw.polygon(surf, _TEAL, pts, 2)         # teal border

    # Downward sweep arrow (↓ with tail)
    ax, ay = cx, cy - 4
    pygame.draw.line(surf, _TEAL, (ax, ay), (ax, ay + 8), 2)          # shaft
    pygame.draw.line(surf, _TEAL, (ax, ay + 8), (ax - 3, ay + 5), 2)  # left head
    pygame.draw.line(surf, _TEAL, (ax, ay + 8), (ax + 3, ay + 5), 2)  # right head

    # Small horizontal "wipe" line above arrow
    pygame.draw.line(surf, _TEAL_DIM, (ax - 4, ay - 1), (ax + 4, ay - 1), 1)

    return surf


def _make_item_hack_mystery() -> pygame.Surface:
    """Hack loot: mystery — purple glow disc with ? character centered."""
    surf = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    cx, cy = _TS // 2, _TS // 2

    glow = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    pygame.draw.circle(glow, (160, 80, 220, 45), (cx, cy), 12)
    surf.blit(glow, (0, 0))

    pygame.draw.circle(surf, (18, 8, 35), (cx, cy), 9)
    pygame.draw.circle(surf, (160, 80, 220), (cx, cy), 9, 2)

    font = pygame.font.SysFont("consolas", 13, bold=True)
    sym = font.render("?", True, (210, 155, 255))
    surf.blit(sym, (cx - sym.get_width() // 2, cy - sym.get_height() // 2 + 2))

    return surf


# Public API
# ---------------------------------------------------------------------------

_BUILDERS: dict[str, object] = {
    "wall":                  lambda: _make_wall_tile(dark=False),
    "wall_dark":             lambda: _make_wall_tile(dark=True),
    "player":                _make_player_sprite,
    "guard":                 _make_guard_sprite,
    "dog":                   _make_dog_sprite,
    "heavy":                 _make_heavy_sprite,
    "turret":                _make_turret_sprite,
    "sniper_drone":          _make_sniper_drone_sprite,
    "riot_guard":            _make_riot_guard_sprite,
    "container_closed":      _make_container_closed,
    "container_open":        _make_container_open,
    "vault_closed":          _make_vault_closed,
    "vault_open":            _make_vault_open,
    "item_loot":             _make_item_loot,
    "item_loot_melee":       _make_item_loot_melee,
    "item_loot_ranged":      _make_item_loot_ranged,
    "item_loot_ammo":        _make_item_loot_ammo,
    "item_loot_armor":       _make_item_loot_armor,
    "item_loot_consumable":  _make_item_loot_consumable,
    "item_hack_credits":     _make_item_hack_credits,
    "item_hack_bonus_time":  _make_item_hack_bonus_time,
    "item_hack_coolant":     _make_item_hack_coolant,
    "item_hack_mystery":     _make_item_hack_mystery,
}


def get(key: str) -> pygame.Surface:
    """Return the cached surface for *key*, building it on first access."""
    if key not in _CACHE:
        builder = _BUILDERS.get(key)
        if builder is None:
            raise KeyError(f"Unknown sprite key: {key!r}")
        _CACHE[key] = builder()  # type: ignore[operator]
    return _CACHE[key]
