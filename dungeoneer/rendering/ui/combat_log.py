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
        x = 12
        y = settings.SCREEN_HEIGHT - 20

        for text, colour, ts in self._messages:
            age = now - ts
            if age > _FADE_SECONDS:
                continue
            # Fade alpha: full for first 4 s, then fade out
            fade = max(0.0, 1.0 - (age - (_FADE_SECONDS - 2)) / 2.0)
            alpha = int(255 * min(1.0, fade))
            r, g, b = colour[:3]
            surf = self._font.render(text, True, (r, g, b))
            surf.set_alpha(alpha)
            screen.blit(surf, (x, y))
            y -= 20
