"""Floating damage numbers — pop up above a target and drift upward."""
from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from dungeoneer.core import settings

_LIFETIME = 0.90   # seconds until fully faded


@dataclass
class _Entry:
    world_x: int
    world_y: int
    text:    str
    colour:  tuple
    age:     float = 0.0


class FloatingNumbers:
    def __init__(self) -> None:
        self._font    = pygame.font.SysFont("consolas", 15, bold=True)
        self._entries: list[_Entry] = []

    def add(self, wx: int, wy: int, amount: int, *, is_crit: bool = False) -> None:
        if is_crit:
            text   = f"*{amount}*"
            colour = (255, 220, 40)     # bright yellow for crits
        else:
            text   = str(amount)
            colour = (255, 110, 70)     # orange-red for normal hits
        self._entries.append(_Entry(wx, wy, text, colour))

    def add_miss(self, wx: int, wy: int) -> None:
        self._entries.append(_Entry(wx, wy, "MISS", (140, 140, 155)))

    def update(self, dt: float) -> None:
        for e in self._entries:
            e.age += dt
        self._entries = [e for e in self._entries if e.age < _LIFETIME]

    def draw(self, screen: pygame.Surface, camera: "Camera") -> None:  # type: ignore[name-defined]
        ts = settings.TILE_SIZE
        for e in self._entries:
            progress = e.age / _LIFETIME
            # Ease-out: fast at start, slow at end
            alpha   = round(255 * (1.0 - progress ** 1.4))
            rise_px = round(progress ** 0.6 * ts * 2.0)

            sx, sy = camera.world_to_screen(e.world_x, e.world_y)
            sx += ts // 2
            sy  = sy - rise_px - 6   # start just above entity top

            surf = self._font.render(e.text, True, e.colour)
            surf.set_alpha(alpha)
            screen.blit(surf, (sx - surf.get_width() // 2, sy))
