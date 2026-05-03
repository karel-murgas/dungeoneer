"""RechargeOverlay — small centered overlay shown when player uses a recharge node.

Shows 4 options (25/50/75/100%) with computed EP gain and heat cost.
Options that would add 0 EP are shown disabled.
Keys 1–4 select, Esc cancels.  Calls on_choice(amount_ep) or on_choice(None).
"""
from __future__ import annotations

import math
from typing import Callable, TYPE_CHECKING

import pygame

from dungeoneer.core import settings
from dungeoneer.core.i18n import t

if TYPE_CHECKING:
    from dungeoneer.entities.recharge_node import RechargeNode
    from dungeoneer.entities.player import Player

# ---------------------------------------------------------------------------
# Layout / colours
# ---------------------------------------------------------------------------
_BG        = (8, 10, 20, 230)
_BORDER    = (80, 200, 255)
_COL_TITLE = (80, 220, 255)
_COL_ROW   = (170, 200, 220)
_COL_DIM   = (60, 80, 100)
_COL_SEL   = (100, 240, 220)
_COL_HOV   = (60, 160, 200)
_COL_HEAT  = (220, 100, 60)
_COL_EP    = (80, 200, 255)
_W         = 360
_ROW_H     = 32
_PAD       = 16
_TITLE_H   = 22

_PCTS = (25, 50, 75, 100)


def _compute_options(node: "RechargeNode", player: "Player") -> list[dict]:
    """Return list of option dicts: pct, ep_requested, ep_actual, heat, disabled."""
    missing = settings.ENERGY_MAX - player.energy
    opts = []
    for pct in _PCTS:
        ep_req = round(node.capacity_ep * pct / 100)
        ep_actual = min(ep_req, missing)
        heat = int(math.ceil(ep_req * settings.RECHARGE_HEAT_PER_EP))
        opts.append({
            "pct":        pct,
            "ep_req":     ep_req,
            "ep_actual":  ep_actual,
            "heat":       heat,
            "disabled":   ep_actual <= 0,
        })
    return opts


class RechargeOverlay:
    def __init__(
        self,
        node: "RechargeNode",
        player: "Player",
        on_choice: Callable[[int | None], None],
    ) -> None:
        self._node      = node
        self._player    = player
        self._on_choice = on_choice
        self._font_title = pygame.font.SysFont("consolas", 16, bold=True)
        self._font_row   = pygame.font.SysFont("consolas", 15)
        self._font_hint  = pygame.font.SysFont("consolas", 13)
        self._sel_idx    = 0
        self._hovered: int | None = None
        # Computed on each draw; used by click handler
        self._row_rects: list[pygame.Rect] = []
        self._panel_rect: pygame.Rect | None = None
        # Advance selection to first non-disabled option
        opts = _compute_options(node, player)
        for i, opt in enumerate(opts):
            if not opt["disabled"]:
                self._sel_idx = i
                break

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        opts = _compute_options(self._node, self._player)

        if event.type == pygame.KEYDOWN:
            key = event.key
            if key == pygame.K_ESCAPE:
                self._on_choice(None)
                return
            # 1–4 key maps to option index
            _key_map = {
                pygame.K_1: 0, pygame.K_2: 1,
                pygame.K_3: 2, pygame.K_4: 3,
            }
            if key in _key_map:
                idx = _key_map[key]
                opt = opts[idx]
                if not opt["disabled"]:
                    self._on_choice(opt["ep_req"])
                return
            if key in (pygame.K_UP, pygame.K_w):
                self._move_sel(-1, opts)
            elif key in (pygame.K_DOWN, pygame.K_s):
                self._move_sel(1, opts)
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_e):
                opt = opts[self._sel_idx]
                if not opt["disabled"]:
                    self._on_choice(opt["ep_req"])

        elif event.type == pygame.MOUSEMOTION:
            self._hovered = None
            for i, rect in enumerate(self._row_rects):
                if rect.collidepoint(event.pos):
                    self._hovered = i
                    break

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Click outside panel → cancel
            if self._panel_rect and not self._panel_rect.collidepoint(event.pos):
                self._on_choice(None)
                return
            for i, rect in enumerate(self._row_rects):
                if rect.collidepoint(event.pos):
                    opt = opts[i]
                    if not opt["disabled"]:
                        self._on_choice(opt["ep_req"])
                    return

    def _move_sel(self, delta: int, opts: list[dict]) -> None:
        n = len(opts)
        idx = self._sel_idx
        for _ in range(n):
            idx = (idx + delta) % n
            if not opts[idx]["disabled"]:
                self._sel_idx = idx
                return

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface) -> None:
        opts = _compute_options(self._node, self._player)
        sw, sh = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT

        n_rows   = len(opts)
        hint_h   = 18
        panel_h  = _PAD + _TITLE_H + 4 + n_rows * _ROW_H + _PAD // 2 + hint_h + _PAD
        panel_w  = _W
        ox = (sw - panel_w) // 2
        oy = (sh - panel_h) // 2

        self._panel_rect = pygame.Rect(ox, oy, panel_w, panel_h)

        # Background
        bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        bg.fill(_BG)
        screen.blit(bg, (ox, oy))
        pygame.draw.rect(screen, _BORDER, (ox, oy, panel_w, panel_h), 2, border_radius=4)

        # Title
        cy = oy + _PAD
        title = self._font_title.render(t("recharge.title"), True, _COL_TITLE)
        screen.blit(title, (ox + (panel_w - title.get_width()) // 2, cy))
        cy += _TITLE_H + 4

        # Option rows
        self._row_rects = []
        for i, opt in enumerate(opts):
            row_rect = pygame.Rect(ox + 4, cy, panel_w - 8, _ROW_H)
            self._row_rects.append(row_rect)

            is_sel = (i == self._sel_idx and not opt["disabled"])
            is_hov = (i == self._hovered and not opt["disabled"])
            is_dis = opt["disabled"]

            if is_sel:
                hl = pygame.Surface((row_rect.width, row_rect.height), pygame.SRCALPHA)
                hl.fill((20, 60, 70, 160))
                screen.blit(hl, row_rect.topleft)
                pygame.draw.rect(screen, _COL_SEL, row_rect, 1, border_radius=2)
            elif is_hov:
                hl = pygame.Surface((row_rect.width, row_rect.height), pygame.SRCALPHA)
                hl.fill((10, 40, 55, 120))
                screen.blit(hl, row_rect.topleft)

            col = _COL_DIM if is_dis else (_COL_SEL if is_sel else _COL_ROW)

            key_lbl = self._font_row.render(f"[{i + 1}]", True, col)
            pct_lbl = self._font_row.render(f"{opt['pct']}%", True, col)

            ep_col  = _COL_DIM if is_dis else _COL_EP
            heat_col = _COL_DIM if is_dis else _COL_HEAT

            ep_lbl   = self._font_row.render(f"+{opt['ep_actual']} EP", True, ep_col)
            heat_lbl = self._font_row.render(f"+{opt['heat']} heat", True, heat_col)

            text_y = cy + (_ROW_H - key_lbl.get_height()) // 2
            screen.blit(key_lbl,  (ox + _PAD,        text_y))
            screen.blit(pct_lbl,  (ox + _PAD + 38,   text_y))
            screen.blit(ep_lbl,   (ox + _PAD + 100,  text_y))
            screen.blit(heat_lbl, (ox + _PAD + 190,  text_y))

            cy += _ROW_H

        # Hint line
        cy += _PAD // 2
        hint = self._font_hint.render(t("recharge.cancel"), True, (80, 110, 100))
        screen.blit(hint, (ox + (panel_w - hint.get_width()) // 2, cy))
