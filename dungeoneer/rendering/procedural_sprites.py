"""Procedurally-generated placeholder sprites.

All surfaces are 32×32 RGBA and cached after first creation so they are only
built once per pygame session.  Call get(key) to retrieve a surface; valid
keys are defined in _BUILDERS at the bottom of this module.
"""
from __future__ import annotations

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


def _make_container_closed() -> pygame.Surface:
    """Locked loot crate — amber glow, lock clasp."""
    surf = pygame.Surface((_TS, _TS), pygame.SRCALPHA)

    # Subtle glow behind the crate
    glow = pygame.Surface((_TS, _TS), pygame.SRCALPHA)
    pygame.draw.rect(glow, (200, 155, 35, 28), (3, 4, _TS - 6, _TS - 7))
    surf.blit(glow, (0, 0))

    # Crate body
    pygame.draw.rect(surf, (55, 40, 16), (3, 10, _TS - 6, _TS - 14))
    # Lid
    pygame.draw.rect(surf, (72, 54, 20), (3, 5, _TS - 6, 7))
    # Outer border
    pygame.draw.rect(surf, (185, 145, 48), (3, 5, _TS - 6, _TS - 8), 1)
    # Horizontal strap
    pygame.draw.line(surf, (185, 145, 48), (3, _TS // 2), (_TS - 4, _TS // 2))
    # Lock clasp
    cx = _TS // 2
    ly = _TS // 2 - 1
    pygame.draw.rect(surf, (220, 185, 65), (cx - 3, ly, 6, 5))  # body
    pygame.draw.circle(surf, (220, 185, 65), (cx, ly - 1), 3, 1)  # arch

    return surf


def _make_container_open() -> pygame.Surface:
    """Opened / looted crate — dim, no glow."""
    surf = pygame.Surface((_TS, _TS), pygame.SRCALPHA)

    pygame.draw.rect(surf, (30, 22, 8), (3, 10, _TS - 6, _TS - 14))
    pygame.draw.rect(surf, (40, 30, 11), (3, 5, _TS - 6, 7))
    pygame.draw.rect(surf, (85, 66, 22), (3, 5, _TS - 6, _TS - 8), 1)
    pygame.draw.line(surf, (85, 66, 22), (3, _TS // 2), (_TS - 4, _TS // 2))

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
# Public API
# ---------------------------------------------------------------------------

_BUILDERS: dict[str, object] = {
    "wall":                  lambda: _make_wall_tile(dark=False),
    "wall_dark":             lambda: _make_wall_tile(dark=True),
    "player":                _make_player_sprite,
    "guard":                 _make_guard_sprite,
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
}


def get(key: str) -> pygame.Surface:
    """Return the cached surface for *key*, building it on first access."""
    if key not in _CACHE:
        builder = _BUILDERS.get(key)
        if builder is None:
            raise KeyError(f"Unknown sprite key: {key!r}")
        _CACHE[key] = builder()  # type: ignore[operator]
    return _CACHE[key]
