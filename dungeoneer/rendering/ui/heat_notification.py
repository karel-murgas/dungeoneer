"""Heat level-up notification — full-screen flash overlay shown on heat level-up."""
from __future__ import annotations

import pygame

from dungeoneer.core.i18n import t
from dungeoneer.systems.heat import LEVEL_NAMES, LEVEL_COLOURS

_DURATION = 5.0   # total seconds visible
_FADE_OUT = 0.55  # fade-out window at end


class HeatLevelUpNotification:
    def __init__(self) -> None:
        self._font_lg = pygame.font.SysFont("consolas", 36, bold=True)
        self._font_md = pygame.font.SysFont("consolas", 15)
        self._timer   = 0.0
        self._level   = 1
        self._color   = LEVEL_COLOURS[1]

    def trigger(self, level: int) -> None:
        self._timer = _DURATION
        self._level = level
        self._color = LEVEL_COLOURS[level]

    def update(self, dt: float) -> None:
        if self._timer > 0.0:
            self._timer = max(0.0, self._timer - dt)

    @property
    def active(self) -> bool:
        return self._timer > 0.0

    def draw(self, screen: pygame.Surface) -> None:
        if self._timer <= 0.0:
            return

        sw, sh = screen.get_size()
        color  = self._color
        level  = self._level
        name   = LEVEL_NAMES[level]

        fade = min(1.0, self._timer / _FADE_OUT) if self._timer < _FADE_OUT else 1.0

        # Edge vignette
        vig   = pygame.Surface((sw, sh), pygame.SRCALPHA)
        depth = 60
        for i in range(depth):
            a = round(fade * 90 * (1.0 - i / depth) ** 1.5)
            if a <= 0:
                continue
            pygame.draw.rect(vig, (*color, a), (i, i, sw - 2 * i, sh - 2 * i), 1)
        screen.blit(vig, (0, 0))

        # Central translucent banner
        panel_h = 80
        panel_y = sh // 2 - panel_h // 2
        banner  = pygame.Surface((sw, panel_h), pygame.SRCALPHA)
        banner.fill((*color, min(round(fade * 180), 32)))
        screen.blit(banner, (0, panel_y))
        line_surf = pygame.Surface((sw, 2), pygame.SRCALPHA)
        line_surf.fill((*color, round(fade * 180)))
        screen.blit(line_surf, (0, panel_y))
        screen.blit(line_surf, (0, panel_y + panel_h - 2))

        # Main text — level name
        main_col = tuple(round(c * fade + (1 - fade) * 30) for c in color)
        main_s = self._font_lg.render(name, True, main_col)
        screen.blit(main_s, (sw // 2 - main_s.get_width() // 2, panel_y + 10))

        # Sub text — level number + effects
        sub_key  = "heat.notify.sub_max" if level >= 5 else "heat.notify.sub"
        sub_text = t(sub_key).format(level=level)
        sub_col  = tuple(round(c * fade * 0.65) for c in color)
        sub_s    = self._font_md.render(sub_text, True, sub_col)
        screen.blit(sub_s, (sw // 2 - sub_s.get_width() // 2,
                            panel_y + 10 + main_s.get_height() + 4))
