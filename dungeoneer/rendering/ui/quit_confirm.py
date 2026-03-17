"""Quit-confirmation overlay shown when the player presses Esc during a run."""
from __future__ import annotations

import pygame

from dungeoneer.core import settings
from dungeoneer.core.i18n import t

_BG      = (10, 12, 20, 230)
_BORDER  = (80, 180, 160)
_COL_HDR = (80, 220, 200)
_COL_TXT = (180, 190, 210)
_COL_YES = (80, 200, 160)
_COL_NO  = (180, 80,  80)
_COL_DIM = (70,  80,  95)

_W   = 340
_PAD = 20


class QuitConfirmDialog:
    def __init__(self, key_prefix: str = "quit_confirm") -> None:
        self._prefix     = key_prefix
        self._font_title = pygame.font.SysFont("consolas", 18, bold=True)
        self._font_text  = pygame.font.SysFont("consolas", 15)
        self._font_key   = pygame.font.SysFont("consolas", 15, bold=True)

    # ------------------------------------------------------------------

    def handle_key(self, key: int) -> str | None:
        """Return 'confirm', 'cancel', or None."""
        if key in (pygame.K_y, pygame.K_RETURN, pygame.K_KP_ENTER):
            return "confirm"
        if key in (pygame.K_n, pygame.K_ESCAPE):
            return "cancel"
        return None

    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface) -> None:
        sw = settings.SCREEN_WIDTH
        sh = settings.SCREEN_HEIGHT

        title_h  = 28
        gap      = 10
        row_h    = 22

        h = _PAD + title_h + gap + row_h + gap * 2 + row_h + row_h + _PAD

        ox = (sw - _W) // 2
        oy = (sh - h)  // 2

        # Background panel
        panel = pygame.Surface((_W, h), pygame.SRCALPHA)
        panel.fill(_BG)
        screen.blit(panel, (ox, oy))
        pygame.draw.rect(screen, _BORDER, (ox, oy, _W, h), 2)

        # Title
        title_surf = self._font_title.render(t(f"{self._prefix}.title"), True, _COL_HDR)
        screen.blit(title_surf, (ox + (_W - title_surf.get_width()) // 2, oy + _PAD))
        pygame.draw.line(screen, (40, 70, 65),
                         (ox + _PAD, oy + _PAD + title_h - 2),
                         (ox + _W - _PAD, oy + _PAD + title_h - 2))

        cy = oy + _PAD + title_h + gap + 4

        # Question
        q_surf = self._font_text.render(t(f"{self._prefix}.question"), True, _COL_TXT)
        screen.blit(q_surf, (ox + (_W - q_surf.get_width()) // 2, cy))
        cy += row_h + gap

        # Confirm
        yes_surf = self._font_key.render(t(f"{self._prefix}.confirm"), True, _COL_YES)
        screen.blit(yes_surf, (ox + (_W - yes_surf.get_width()) // 2, cy))
        cy += row_h

        # Cancel
        no_surf = self._font_key.render(t(f"{self._prefix}.cancel"), True, _COL_DIM)
        screen.blit(no_surf, (ox + (_W - no_surf.get_width()) // 2, cy))
