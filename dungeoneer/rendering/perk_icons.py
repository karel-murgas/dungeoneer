"""Lazy-loading cache for perk icon surfaces.

Icons live in assets/ui/ as perk_<id>.png (32×32).
Returns None for any perk that has no icon file.
"""
from __future__ import annotations

import os

import pygame

_ASSET_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "ui")
_cache: dict[str, "pygame.Surface | None"] = {}


def get_icon(perk_id: str, size: int = 20) -> "pygame.Surface | None":
    """Return a scaled Surface for the perk icon, or None if not found."""
    key = f"{perk_id}_{size}"
    if key in _cache:
        return _cache[key]

    path = os.path.normpath(os.path.join(_ASSET_DIR, f"perk_{perk_id}.png"))
    if os.path.exists(path):
        try:
            raw = pygame.image.load(path).convert_alpha()
            _cache[key] = pygame.transform.smoothscale(raw, (size, size))
        except Exception:
            _cache[key] = None
    else:
        _cache[key] = None

    return _cache[key]


def clear_cache() -> None:
    _cache.clear()
