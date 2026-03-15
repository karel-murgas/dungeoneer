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
    """Item on the floor — glowing amber diamond."""
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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_BUILDERS: dict[str, object] = {
    "wall":             lambda: _make_wall_tile(dark=False),
    "wall_dark":        lambda: _make_wall_tile(dark=True),
    "player":           _make_player_sprite,
    "guard":            _make_guard_sprite,
    "container_closed": _make_container_closed,
    "container_open":   _make_container_open,
    "item_loot":        _make_item_loot,
}


def get(key: str) -> pygame.Surface:
    """Return the cached surface for *key*, building it on first access."""
    if key not in _CACHE:
        builder = _BUILDERS.get(key)
        if builder is None:
            raise KeyError(f"Unknown sprite key: {key!r}")
        _CACHE[key] = builder()  # type: ignore[operator]
    return _CACHE[key]
