"""Alert banner — "!" pop above the player when combat starts."""
from __future__ import annotations

import pygame

from dungeoneer.core import settings

_DURATION   = 0.65   # total seconds
_SLIDE_END  = 0.12   # seconds to finish sliding up
_FADE_START = 0.45   # seconds when fade-out begins
_SLIDE_PX   = 22     # pixels the banner rises from player head

_COL_TEXT   = (255, 60, 60)
_COL_BG     = (40, 30, 10)
_COL_BORDER = (200, 160, 40)


class AlertBanner:
    def __init__(self) -> None:
        self._font  = pygame.font.SysFont("consolas", 22, bold=True)
        self._timer = 0.0          # seconds since trigger; 0 = idle

    # ------------------------------------------------------------------

    def trigger(self) -> None:
        self._timer = _DURATION

    @property
    def is_blocking(self) -> bool:
        return self._timer > 0.0

    def update(self, dt: float) -> None:
        if self._timer > 0.0:
            self._timer = max(0.0, self._timer - dt)

    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface, camera: "Camera",  # type: ignore[name-defined]
             player_x: int, player_y: int) -> None:
        if self._timer <= 0.0:
            return

        elapsed = _DURATION - self._timer

        # Slide progress (0→1 over _SLIDE_END)
        slide_t = min(1.0, elapsed / _SLIDE_END)
        # Ease-out: sqrt gives fast start, slow end
        slide_t = slide_t ** 0.5

        # Alpha (fade-out in last segment)
        if elapsed >= _FADE_START:
            fade_t = (elapsed - _FADE_START) / (_DURATION - _FADE_START)
            alpha  = round(255 * (1.0 - fade_t))
        else:
            alpha = 255

        # Screen position — above player sprite
        sx, sy = camera.world_to_screen(player_x, player_y)
        ts = settings.TILE_SIZE
        # Start at top edge of player tile, then slide up
        base_y = sy - 8
        draw_y = base_y - round(_SLIDE_PX * slide_t)
        draw_x = sx + ts // 2  # horizontally centred on tile

        # Render text
        text_surf = self._font.render("!", True, _COL_TEXT)
        tw, th    = text_surf.get_size()
        pad       = 6
        bw, bh    = tw + pad * 2, th + pad * 2

        # Composited onto an alpha surface
        box = pygame.Surface((bw, bh), pygame.SRCALPHA)
        bg_col  = (*_COL_BG,     min(alpha, 200))
        brd_col = (*_COL_BORDER, alpha)
        pygame.draw.rect(box, bg_col,  (0, 0, bw, bh), border_radius=4)
        pygame.draw.rect(box, brd_col, (0, 0, bw, bh), 2, border_radius=4)
        text_a = text_surf.copy()
        text_a.set_alpha(alpha)
        box.blit(text_a, (pad, pad))

        screen.blit(box, (draw_x - bw // 2, draw_y - bh))
