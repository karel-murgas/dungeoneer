"""CombatLog — scrolling message panel at the bottom-left."""
from __future__ import annotations

import time
from collections import deque

import pygame

from dungeoneer.core import settings
from dungeoneer.core.event_bus import bus, LogMessageEvent


_MAX_MESSAGES = 8
_FADE_SECONDS = 6.0


class CombatLog:
    def __init__(self) -> None:
        self._font = pygame.font.SysFont("consolas", 15)
        # Each entry: (text, colour, timestamp)
        self._messages: deque[tuple[str, tuple, float]] = deque(maxlen=_MAX_MESSAGES)
        bus.subscribe(LogMessageEvent, self._on_log)

    def _on_log(self, event: LogMessageEvent) -> None:
        self._messages.appendleft((event.message, event.colour, time.monotonic()))

    def close(self) -> None:
        bus.unsubscribe(LogMessageEvent, self._on_log)

    def add(self, message: str, colour: tuple = (200, 200, 200)) -> None:
        self._messages.appendleft((message, colour, time.monotonic()))

    def draw(self, screen: pygame.Surface) -> None:
        now = time.monotonic()
        # Right half of the bottom HUD band, beside the hotbar.
        # Align top with hotbar (same vertical centering formula).
        _SLOT_H   = 28
        x         = 610
        band_top  = settings.SCREEN_HEIGHT - settings.VIEWPORT_Y_BOTTOM
        y         = band_top + (settings.VIEWPORT_Y_BOTTOM - _SLOT_H) // 2
        max_y     = settings.SCREEN_HEIGHT - 6

        for text, colour, ts in self._messages:
            if y >= max_y:
                break
            age = now - ts
            if age > _FADE_SECONDS:
                y += 20
                continue
            # Fade alpha: full for first 4 s, then fade out
            fade = max(0.0, 1.0 - (age - (_FADE_SECONDS - 2)) / 2.0)
            alpha = round(255 * min(1.0, fade))
            r, g, b = colour[:3]
            surf = self._font.render(text, True, (r, g, b))
            surf.set_alpha(alpha)
            screen.blit(surf, (x, y))
            y += 20
