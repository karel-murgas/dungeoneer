"""Healing rhythm overlay.

Not a Scene — no push/pop.  GameScene owns a HealOverlay instance directly,
routes events to it, and calls update()/render() each frame.

The player watches 2 heartbeat cycles (du-dum, du-dum), then must match the
3rd: press H on the beat, hold through the gap, release on the second thump.
Timing accuracy maps to ±20% of the consumable's base heal amount.
"""
from __future__ import annotations

import random
from enum import auto, Enum
from typing import Callable, Optional, TYPE_CHECKING

import pygame

from dungeoneer.core.i18n import t
from dungeoneer.core.settings import (
    HEAL_MIN_CYCLE_MS, HEAL_MAX_CYCLE_MS,
    HEAL_MIN_DU_GAP_MS, HEAL_MAX_DU_GAP_MS,
    HEAL_BEAT_FLASH_MS, HEAL_ACCURACY_WINDOW,
    HEAL_RESULT_PAUSE, HEAL_RANGE,
)

if TYPE_CHECKING:
    from dungeoneer.items.consumable import Consumable
    from dungeoneer.entities.player import Player


# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
_BG          = (0,   0,   0,  210)
_BORDER      = (40,  80, 130, 220)
_TITLE       = (0,  200, 190)
_TEXT        = (180, 220, 200)
_TEXT_DIM    = (80,  120, 100)
_HEART_BASE  = (200,  40,  60)
_HEART_FLASH = (255,  90,  90)
_DU_COL      = (255, 130, 130)
_DUM_COL     = (255, 190, 130)
_NOW_COL     = (240, 220,   0)
_TIMER_FG    = (140, 200, 180)
_TIMER_BG    = (30,   35,  45)
_PERFECT_COL = (80,  220,  80)
_GOOD_COL    = (210, 215,  60)
_POOR_COL    = (210,  70,  70)
_DOT_ON      = (0,  200, 190)
_DOT_OFF     = (50,  70,  70)


class _State(Enum):
    WATCHING    = auto()
    PLAYER_TURN = auto()
    RESULT      = auto()
    DONE        = auto()


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class HealOverlay:
    """Heartbeat rhythm overlay for healing consumables.

    Callback:
        on_complete(actual_heal: int) — actual HP to restore;
        -1 = cancelled.
    """

    _PANEL_W = 460
    _PANEL_H = 300

    def __init__(
        self,
        consumable: "Consumable",
        player: "Player",
        on_complete: Callable[[int], None],
        audio_manager=None,
    ) -> None:
        self._consumable  = consumable
        self._player      = player
        self._on_complete = on_complete
        self._audio       = audio_manager

        # Randomise rhythm per use
        self._cycle  = random.randint(HEAL_MIN_CYCLE_MS,  HEAL_MAX_CYCLE_MS)  / 1000.0
        self._du_gap = random.randint(HEAL_MIN_DU_GAP_MS, HEAL_MAX_DU_GAP_MS) / 1000.0

        # Scheduled game beat events: (time_s, kind) sorted by time
        self._beats = [
            (0.0,                       "du"),
            (self._du_gap,              "dum"),
            (self._cycle,               "du"),
            (self._cycle + self._du_gap, "dum"),
        ]
        self._next_beat_idx = 0

        self._t          = 0.0
        self._state      = _State.WATCHING
        self._completed  = False
        self._show_help  = False

        # Beat flash animation
        self._flash_dur   = HEAL_BEAT_FLASH_MS / 1000.0
        self._flash_timer = 0.0    # seconds remaining
        self._flash_label = ""     # "DU" or "DUM"
        self._heart_scale = 1.0

        # Player input — absolute _t timestamps
        self._press_t:   Optional[float] = None
        self._release_t: Optional[float] = None

        # Result
        self._result_timer = 0.0
        self._actual_heal  = 0
        self._quality      = ""   # "perfect" | "good" | "poor"

        # Fonts
        try:
            self._font_big   = pygame.font.SysFont("consolas", 26, bold=True)
            self._font_med   = pygame.font.SysFont("consolas", 16, bold=True)
            self._font_small = pygame.font.SysFont("consolas", 13)
        except Exception:
            self._font_big   = pygame.font.Font(None, 32)
            self._font_med   = pygame.font.Font(None, 20)
            self._font_small = pygame.font.Font(None, 16)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_active(self) -> bool:
        return not self._completed

    @property
    def _player_phase_start(self) -> float:
        """Absolute time when the player input phase begins."""
        return 2.0 * self._cycle

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
            self._show_help = not self._show_help
            return
        if self._show_help:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._show_help = False
            return

        if self._state == _State.WATCHING:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._cancel()

        elif self._state == _State.PLAYER_TURN:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_h:
                if self._press_t is None:
                    self._press_t = self._t
                    self._fire_beat("du")
            elif event.type == pygame.KEYUP and event.key == pygame.K_h:
                if self._press_t is not None and self._release_t is None:
                    self._release_t = self._t
                    self._fire_beat("dum")
                    self._finalize()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._cancel()

    # ------------------------------------------------------------------
    # Logic
    # ------------------------------------------------------------------

    def _cancel(self) -> None:
        self._completed = True
        self._on_complete(-1)

    def _fire_beat(self, kind: str) -> None:
        self._flash_timer = self._flash_dur
        self._flash_label = kind.upper()
        if kind == "du":
            self._heart_scale = 0.78
            if self._audio:
                self._audio.play("heart_du", 0.7)
        else:
            self._heart_scale = 1.12
            if self._audio:
                self._audio.play("heart_dum", 0.6)

    def _finalize(self) -> None:
        """Compute accuracy from timing, transition to RESULT."""
        expected_press = self._player_phase_start

        if self._press_t is not None:
            press_off = self._press_t - expected_press
        else:
            press_off = self._cycle   # very late = complete miss

        if self._press_t is not None and self._release_t is not None:
            hold_dur    = self._release_t - self._press_t
            release_off = abs(hold_dur - self._du_gap)
        else:
            release_off = self._du_gap   # no release = complete miss

        half_win    = HEAL_ACCURACY_WINDOW / 2.0
        press_acc   = max(0.0, 1.0 - abs(press_off)  / half_win)
        release_acc = max(0.0, 1.0 - release_off      / (self._du_gap * 0.5))
        accuracy    = (press_acc + release_acc) / 2.0

        base = self._consumable.heal_amount
        self._actual_heal = max(1, int(base * (1.0 - HEAL_RANGE + 2.0 * HEAL_RANGE * accuracy)))

        if accuracy >= 0.80:
            self._quality = "perfect"
        elif accuracy >= 0.40:
            self._quality = "good"
        else:
            self._quality = "poor"

        self._state        = _State.RESULT
        self._result_timer = HEAL_RESULT_PAUSE

    def update(self, dt: float) -> None:
        if self._completed:
            return
        if self._show_help:
            return   # freeze everything while help is visible

        self._t += dt

        # Decay flash; restore heart scale
        if self._flash_timer > 0.0:
            self._flash_timer -= dt
            if self._flash_timer <= 0.0:
                self._flash_timer = 0.0
                self._heart_scale = 1.0

        if self._state == _State.WATCHING:
            # Fire scheduled game beats
            while (
                self._next_beat_idx < len(self._beats)
                and self._t >= self._beats[self._next_beat_idx][0]
            ):
                _, kind = self._beats[self._next_beat_idx]
                self._fire_beat(kind)
                self._next_beat_idx += 1

            if self._t >= self._player_phase_start:
                self._state = _State.PLAYER_TURN

        elif self._state == _State.PLAYER_TURN:
            # Timeout
            if self._t >= 3.0 * self._cycle:
                self._finalize()

        elif self._state == _State.RESULT:
            self._result_timer -= dt
            if self._result_timer <= 0.0:
                self._completed = True
                self._on_complete(self._actual_heal)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self, screen: pygame.Surface) -> None:
        sw, sh = screen.get_size()

        pw, ph = self._PANEL_W, self._PANEL_H
        px = (sw - pw) // 2
        py = (sh - ph) // 2

        # Semi-transparent panel
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill(_BG)
        pygame.draw.rect(panel, _BORDER, (0, 0, pw, ph), 1)
        screen.blit(panel, (px, py))

        cx      = px + pw // 2
        cy_heart = py + 130

        # Title
        title_s = self._font_med.render(t("heal.overlay.title"), True, _TITLE)
        screen.blit(title_s, (cx - title_s.get_width() // 2, py + 10))

        # Heart
        self._draw_heart(screen, cx, cy_heart, scale=self._heart_scale)

        # Beat flash label — shown only during WATCHING / PLAYER_TURN
        if (
            self._flash_timer > 0.0
            and self._flash_label
            and self._state in (_State.WATCHING, _State.PLAYER_TURN)
        ):
            frac  = self._flash_timer / self._flash_dur
            col   = _DU_COL if self._flash_label == "DU" else _DUM_COL
            lbl_s = self._font_big.render(self._flash_label, True, col)
            lbl_s.set_alpha(int(255 * min(1.0, frac * 1.5)))
            screen.blit(lbl_s, (cx - lbl_s.get_width() // 2, cy_heart + 44))

        # State-specific content
        if self._state == _State.WATCHING:
            self._render_watching(screen, cx, py)
        elif self._state == _State.PLAYER_TURN:
            self._render_player_turn(screen, cx, cy_heart, py)
        elif self._state == _State.RESULT:
            self._render_result(screen, cx, cy_heart)

        # Progress dots
        self._render_dots(screen, cx, py + ph - 30)

        # F1 hint (reuse aim key)
        hint_s = self._font_small.render(t("aim.help.hint"), True, _TEXT_DIM)
        screen.blit(hint_s, (cx - hint_s.get_width() // 2, py + ph - 16))

        if self._show_help:
            self._draw_help_overlay(screen)

    # ------------------------------------------------------------------
    # Heart glyph (drawn with pygame.draw — no image assets)
    # ------------------------------------------------------------------

    def _draw_heart(
        self, screen: pygame.Surface, cx: int, cy: int, scale: float = 1.0
    ) -> None:
        r = max(2, int(22 * scale))
        col = _HEART_FLASH if self._flash_timer > 0.0 else _HEART_BASE
        bump_off = max(1, int(r * 0.55))
        cy_bumps = cy - int(r * 0.15)

        # Lower V-fill first
        pts = [
            (cx - int(r * 1.4), cy - int(r * 0.3)),
            (cx + int(r * 1.4), cy - int(r * 0.3)),
            (cx,                cy + int(r * 1.3)),
        ]
        pygame.draw.polygon(screen, col, pts)

        # Two top bumps
        pygame.draw.circle(screen, col, (cx - bump_off, cy_bumps), r)
        pygame.draw.circle(screen, col, (cx + bump_off, cy_bumps), r)

    # ------------------------------------------------------------------
    # State-specific render helpers
    # ------------------------------------------------------------------

    def _render_watching(
        self, screen: pygame.Surface, cx: int, py: int
    ) -> None:
        s = self._font_small.render(t("heal.overlay.watch"), True, _TEXT_DIM)
        screen.blit(s, (cx - s.get_width() // 2, py + 40))

    def _render_player_turn(
        self,
        screen: pygame.Surface,
        cx: int,
        cy_heart: int,
        py: int,
    ) -> None:
        phase_t = self._t - self._player_phase_start

        # "NOW!" flash — fades out over 0.35 s
        if phase_t < 0.35:
            frac  = 1.0 - phase_t / 0.35
            now_s = self._font_big.render(t("heal.overlay.now"), True, _NOW_COL)
            now_s.set_alpha(int(255 * frac))
            screen.blit(now_s, (cx - now_s.get_width() // 2, cy_heart - 75))

        # Timer bar depleting from full → empty over one cycle
        timeout_dur = self._cycle
        frac_elapsed = min(1.0, phase_t / timeout_dur)
        bar_w, bar_h = 200, 6
        bx = cx - bar_w // 2
        by = py + 40
        pygame.draw.rect(screen, _TIMER_BG, (bx, by, bar_w, bar_h))
        fill_w = int(bar_w * (1.0 - frac_elapsed))
        if fill_w > 0:
            bar_col = _POOR_COL if frac_elapsed > 0.6 else _TIMER_FG
            pygame.draw.rect(screen, bar_col, (bx, by, fill_w, bar_h))

    def _render_result(
        self,
        screen: pygame.Surface,
        cx: int,
        cy_heart: int,
    ) -> None:
        if self._quality == "perfect":
            label, col = t("heal.overlay.perfect"), _PERFECT_COL
        elif self._quality == "good":
            label, col = t("heal.overlay.good"), _GOOD_COL
        else:
            label, col = t("heal.overlay.poor"), _POOR_COL

        ql_s = self._font_big.render(label, True, col)
        screen.blit(ql_s, (cx - ql_s.get_width() // 2, cy_heart - 75))

        hp_s = self._font_med.render(f"+{self._actual_heal} HP", True, _PERFECT_COL)
        screen.blit(hp_s, (cx - hp_s.get_width() // 2, cy_heart + 46))

    def _render_dots(
        self, screen: pygame.Surface, cx: int, y: int
    ) -> None:
        """Three progress dots — one per heartbeat cycle + player's turn."""
        dot_r   = 5
        spacing = 22

        if self._state == _State.WATCHING:
            filled = self._next_beat_idx // 2   # 0 → 0, after dum-1 → 1, after dum-2 → 2
        elif self._state == _State.PLAYER_TURN:
            filled = 2
        else:  # RESULT / DONE
            filled = 3

        for i in range(3):
            dx  = cx + (i - 1) * spacing
            col = _DOT_ON if i < filled else _DOT_OFF
            pygame.draw.circle(screen, col, (dx, y), dot_r)

    # ------------------------------------------------------------------
    # Help overlay (F1)
    # ------------------------------------------------------------------

    def _draw_help_overlay(self, screen: pygame.Surface) -> None:
        sw, sh = screen.get_size()

        dim = pygame.Surface((sw, sh), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 200))
        screen.blit(dim, (0, 0))

        _BG2  = (8,  14,  22)
        _CYN  = (0, 200, 190)
        _YEL  = (210, 215, 60)

        pw = min(sw - 60, 500)
        ph = 276
        bx = (sw - pw) // 2
        by = (sh - ph) // 2

        pygame.draw.rect(screen, _BG2, (bx, by, pw, ph))
        pygame.draw.rect(screen, _CYN, (bx, by, pw, ph), 1)

        title_s = self._font_big.render(t("heal.overlay.title"), True, _CYN)
        screen.blit(title_s, (sw // 2 - title_s.get_width() // 2, by + 10))
        sep_y = by + 10 + title_s.get_height() + 6
        pygame.draw.line(screen, _CYN, (bx + 20, sep_y), (bx + pw - 20, sep_y), 1)

        y  = sep_y + 12
        lh = 18
        lx = bx + 24

        def _section(key: str) -> None:
            nonlocal y
            s = self._font_med.render(t(key), True, _CYN)
            screen.blit(s, (lx, y))
            y += 22

        def _bullet(key: str) -> None:
            nonlocal y
            dot = self._font_small.render("\u2022 ", True, _TEXT_DIM)
            txt = self._font_small.render(t(key), True, _TEXT)
            screen.blit(dot, (lx, y))
            screen.blit(txt, (lx + dot.get_width(), y))
            y += lh

        _section("heal.help.h1")
        _bullet("heal.help.1")
        _bullet("heal.help.2")
        _bullet("heal.help.3")
        _bullet("heal.help.4")
        y += 8

        _section("heal.help.h2")
        _bullet("heal.help.key1")
        _bullet("heal.help.key2")
        _bullet("heal.help.key3")

        close_s = self._font_small.render(t("aim.help.close"), True, _TEXT_DIM)
        screen.blit(close_s, (sw // 2 - close_s.get_width() // 2, by + ph - 18))
