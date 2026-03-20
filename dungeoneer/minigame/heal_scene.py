"""Healing rhythm overlay.

Not a Scene — no push/pop.  GameScene owns a HealOverlay instance directly,
routes events to it, and calls update()/render() each frame.

The player watches 2 heartbeat cycles (du-dum, du-dum), then must match the
3rd: press H on the beat, hold through the gap, release on the second thump.
Timing accuracy maps to ±20% of the consumable's base heal amount.

Visual: scrolling ECG line that moves left.  The cursor (vertical line at 70%
from the left edge) marks "now".  DU fires at the R-spike; DUM at the T-wave.
A ghost trace shows the expected 3rd beat ahead of the cursor.
"""
from __future__ import annotations

import math
import random
from enum import auto, Enum
from typing import Callable, Optional, TYPE_CHECKING

import pygame

from dungeoneer.core.i18n import t
from dungeoneer.core.settings import (
    HEAL_MIN_CYCLE_MS, HEAL_MAX_CYCLE_MS,
    HEAL_MIN_DU_GAP_MS, HEAL_MAX_DU_GAP_MS,
    HEAL_BEAT_FLASH_MS, HEAL_RESULT_PAUSE, HEAL_RANGE,
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

# ECG-specific colours
_ECG_LINE    = (0,  210, 190)   # main trace (cycles 1+2)
_ECG_THIRD   = (80, 110, 120)   # dashed 3rd beat — player must match this
_ECG_PLAYER  = (220, 210,  50)  # player's actual input trace

# Experiment flag — set True to restore original behaviour (3rd beat always visible)
_SHOW_THIRD_BEAT_ALWAYS = False
_ECG_CURSOR  = (55,  85, 120)   # "now" marker line
_ECG_GRID    = (20,  32,  48)   # background grid lines
_ECG_BG      = (8,   14,  22)   # ECG area fill

# ---------------------------------------------------------------------------
# Timing constants
# ---------------------------------------------------------------------------
_DELAY = 0.5   # seconds of flat line before first heartbeat


class _State(Enum):
    WATCHING    = auto()
    PLAYER_TURN = auto()
    RESULT      = auto()
    DONE        = auto()


# ---------------------------------------------------------------------------
# ECG waveform parameters (Gaussian component widths, in seconds)
# ---------------------------------------------------------------------------
_P_D  = 2 * 0.030 ** 2   # P wave
_QS_D = 2 * 0.016 ** 2   # Q / S dip
_R_D  = 2 * 0.020 ** 2   # R spike
_T_D  = 2 * 0.055 ** 2   # T wave


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

    # ECG area layout (relative to panel origin)
    _ECG_PAD    = 20          # left/right padding inside panel
    _ECG_TOP    = 35          # y offset of ECG area top
    _ECG_H      = 88          # height of ECG area
    _ECG_CURSOR = 0.55        # cursor at 55%: ~3.0 s future visible at 65 px/s
    _PX_PER_S   = 65          # slow enough that all 3 cycles fit on screen at t=0

    def __init__(
        self,
        consumable: "Consumable",
        player: "Player",
        on_complete: Callable[[int], None],
        audio_manager=None,
        difficulty=None,
    ) -> None:
        self._consumable  = consumable
        self._player      = player
        self._on_complete = on_complete
        self._audio       = audio_manager
        # (perfect_ms, great_ms, good_ms, poor_ms) — sum of |press_off|+|release_off|
        self._thresholds = (
            difficulty.heal_timing_thresholds if difficulty is not None
            else (80, 200, 360, 520)   # default = hard
        )

        # Randomise rhythm per use
        self._cycle  = random.randint(HEAL_MIN_CYCLE_MS,  HEAL_MAX_CYCLE_MS)  / 1000.0
        self._du_gap = random.randint(HEAL_MIN_DU_GAP_MS, HEAL_MAX_DU_GAP_MS) / 1000.0

        # Scheduled game beat events (absolute times including _DELAY)
        self._beats = [
            (_DELAY,                                    "du"),
            (_DELAY + self._du_gap,                     "dum"),
            (_DELAY + self._cycle,                      "du"),
            (_DELAY + self._cycle + self._du_gap,       "dum"),
        ]
        self._next_beat_idx = 0

        self._t         = 0.0
        self._state     = _State.WATCHING
        self._completed = False
        self._show_help = False

        # Beat flash animation
        self._flash_dur   = HEAL_BEAT_FLASH_MS / 1000.0
        self._flash_timer = 0.0
        self._flash_label = ""     # "DU" or "DUM"

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
        """Absolute time when the player input phase begins (after 2nd dum)."""
        return self._beats[-1][0]

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
            if self._audio:
                self._audio.play("heart_du", 1.0)
        else:
            if self._audio:
                self._audio.play("heart_dum", 0.9)

    def _finalize(self) -> None:
        """Determine quality tier from raw timing error, then heal amount from tier."""
        expected_press   = _DELAY + 2.0 * self._cycle
        expected_release = expected_press + self._du_gap

        press_ms   = abs(self._press_t   - expected_press)   * 1000 if self._press_t   is not None else float("inf")
        release_ms = abs(self._release_t - expected_release) * 1000 if self._release_t is not None else float("inf")
        total_ms   = press_ms + release_ms

        t_perfect, t_great, t_good, t_poor = self._thresholds
        if   total_ms < t_perfect: self._quality = "perfect"
        elif total_ms < t_great:   self._quality = "great"
        elif total_ms < t_good:    self._quality = "good"
        elif total_ms < t_poor:    self._quality = "poor"
        else:                      self._quality = "miss"

        base = self._consumable.heal_amount
        mult = {"perfect": 1.20, "great": 1.10, "good": 1.00, "poor": 0.90, "miss": 0.80}
        self._actual_heal = max(1, round(base * mult[self._quality]))

        self._state        = _State.RESULT
        self._result_timer = HEAL_RESULT_PAUSE

    def update(self, dt: float) -> None:
        if self._completed:
            return
        if self._show_help:
            return   # freeze everything while help is visible

        self._t += dt

        # Decay flash timer
        if self._flash_timer > 0.0:
            self._flash_timer -= dt
            if self._flash_timer <= 0.0:
                self._flash_timer = 0.0

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
            # Timeout after one full cycle of waiting
            if self._t >= _DELAY + 3.0 * self._cycle:
                self._finalize()

        elif self._state == _State.RESULT:
            self._result_timer -= dt
            if self._result_timer <= 0.0:
                self._completed = True
                self._on_complete(self._actual_heal)

    # ------------------------------------------------------------------
    # Rendering — main entry
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

        cx = px + pw // 2

        # Title
        title_s = self._font_med.render(t("heal.overlay.title"), True, _TITLE)
        screen.blit(title_s, (cx - title_s.get_width() // 2, py + 10))

        # ECG strip
        self._render_ecg(screen, px, py)

        # Beat flash label — DU or DUM, shown below ECG
        if (
            self._flash_timer > 0.0
            and self._flash_label
            and self._state in (_State.WATCHING, _State.PLAYER_TURN)
        ):
            frac  = self._flash_timer / self._flash_dur
            col   = _DU_COL if self._flash_label == "DU" else _DUM_COL
            lbl_s = self._font_big.render(self._flash_label, True, col)
            lbl_s.set_alpha(round(255 * min(1.0, frac * 1.5)))
            screen.blit(lbl_s, (cx - lbl_s.get_width() // 2, py + 130))

        # State-specific content
        if self._state == _State.WATCHING:
            self._render_watching(screen, cx, py)
        elif self._state == _State.PLAYER_TURN:
            self._render_player_turn(screen, cx, py)
        elif self._state == _State.RESULT:
            self._render_result(screen, cx, py)

        # Progress dots
        self._render_dots(screen, cx, py + ph - 30)

        # F1 hint
        hint_s = self._font_small.render(t("aim.help.hint"), True, _TEXT_DIM)
        screen.blit(hint_s, (cx - hint_s.get_width() // 2, py + ph - 16))

        if self._show_help:
            self._draw_help_overlay(screen)

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _draw_dashed(
        surface: pygame.Surface,
        color: tuple,
        pts: list,
        width: int = 2,
        dash_px: int = 10,
        gap_px: int = 7,
    ) -> None:
        """Draw a dashed polyline through pre-computed (x, y) points.

        Points are assumed to be ~2 px apart in x (as generated by _render_ecg),
        so dash_px and gap_px are in screen pixels.
        """
        n = len(pts)
        if n < 2:
            return
        step = 2               # x-step between consecutive pts (see _build_pts range step)
        dash_pts = max(2, dash_px  // step)
        gap_pts  = max(1, gap_px   // step)
        i       = 0
        drawing = True
        while i < n - 1:
            count = dash_pts if drawing else gap_pts
            if drawing:
                seg = pts[i : i + count + 1]
                if len(seg) >= 2:
                    pygame.draw.lines(surface, color, False, seg, width)
            i      += count
            drawing = not drawing

    # ------------------------------------------------------------------
    # ECG waveform
    # ------------------------------------------------------------------

    def _ecg_y(self, t_sample: float, beats: list) -> float:
        """Normalised ECG amplitude at t_sample for the given beat list.

        Returns a value roughly in [-0.35, 1.0].  Positive = upward (R spike).
        Uses sum of Gaussians: P wave, Q dip, R spike, S dip, T wave.
        """
        val = 0.0
        for bt, kind in beats:
            dt = t_sample - bt
            # Skip contribution when far from beat (> ~10 sigma of widest component)
            if abs(dt) > 0.55:
                continue
            if kind == "du":
                # P wave (small bump ~130 ms before QRS)
                p_dt = dt + 0.13
                val += 0.18 * math.exp(-(p_dt * p_dt) / _P_D)
                # Q dip
                q_dt = dt + 0.028
                val -= 0.30 * math.exp(-(q_dt * q_dt) / _QS_D)
                # R spike
                val += 1.00 * math.exp(-(dt * dt) / _R_D)
                # S dip
                s_dt = dt - 0.028
                val -= 0.28 * math.exp(-(s_dt * s_dt) / _QS_D)
            else:  # "dum" → T wave
                t_dt = dt - 0.06
                val += 0.40 * math.exp(-(t_dt * t_dt) / _T_D)
        return val

    # ------------------------------------------------------------------
    # ECG strip renderer
    # ------------------------------------------------------------------

    def _render_ecg(self, screen: pygame.Surface, px: int, py: int) -> None:
        ecg_left = px + self._ECG_PAD
        ecg_top  = py + self._ECG_TOP
        ecg_w    = self._PANEL_W - 2 * self._ECG_PAD
        ecg_h    = self._ECG_H
        ecg_mid  = ecg_top + round(ecg_h * 0.58)   # baseline slightly below centre
        ecg_amp  = ecg_h * 0.42                   # max amplitude in pixels
        cur_x    = ecg_left + round(ecg_w * self._ECG_CURSOR)
        pps      = self._PX_PER_S

        # Background fill
        pygame.draw.rect(screen, _ECG_BG, (ecg_left, ecg_top, ecg_w, ecg_h))

        # Horizontal baseline grid
        pygame.draw.line(screen, _ECG_GRID,
                         (ecg_left, ecg_mid), (ecg_left + ecg_w, ecg_mid))

        # Vertical grid lines every 0.5 s (scroll with time)
        t_step  = 0.5
        t_left  = self._t - (cur_x - ecg_left) / pps
        t_right = self._t + (ecg_left + ecg_w - cur_x) / pps
        t_g     = math.ceil(t_left / t_step) * t_step
        while t_g <= t_right + t_step:
            xg = cur_x + round((t_g - self._t) * pps)
            if ecg_left <= xg <= ecg_left + ecg_w:
                pygame.draw.line(screen, _ECG_GRID,
                                 (xg, ecg_top), (xg, ecg_top + ecg_h))
            t_g += t_step

        y_top = ecg_top + 1
        y_bot = ecg_top + ecg_h - 1

        third_beats = [
            (_DELAY + 2 * self._cycle,               "du"),
            (_DELAY + 2 * self._cycle + self._du_gap, "dum"),
        ]

        def _build_pts(beat_list, past_only=False):
            pts = []
            for xi in range(0, ecg_w, 2):
                x = ecg_left + xi
                if past_only and x > cur_x:
                    continue
                t_at_x = self._t - (cur_x - x) / pps
                y_val  = self._ecg_y(t_at_x, beat_list)
                y      = ecg_mid - round(y_val * ecg_amp)
                pts.append((x, max(y_top, min(y_bot, y))))
            return pts

        # 1. Dashed 3rd beat (player must match) — drawn first, underneath
        #    Hidden until RESULT phase (experiment); revert: set _SHOW_THIRD_BEAT_ALWAYS=True
        if _SHOW_THIRD_BEAT_ALWAYS or self._state == _State.RESULT:
            third_pts = _build_pts(third_beats)
            if len(third_pts) >= 2:
                self._draw_dashed(screen, _ECG_THIRD, third_pts, width=2,
                                  dash_px=10, gap_px=7)

        # 2. Main ECG trace — cycles 1+2, full width from t=0
        main_pts = _build_pts(self._beats)
        if len(main_pts) >= 2:
            pygame.draw.lines(screen, _ECG_LINE, False, main_pts, 2)

        # 3. Player input trace (past only) — drawn on top in yellow
        player_beats = []
        if self._press_t   is not None: player_beats.append((self._press_t,   "du"))
        if self._release_t is not None: player_beats.append((self._release_t, "dum"))
        if player_beats:
            ppts = _build_pts(player_beats, past_only=True)
            if len(ppts) >= 2:
                pygame.draw.lines(screen, _ECG_PLAYER, False, ppts, 2)

        # 4. Cursor line ("now")
        pygame.draw.line(screen, _ECG_CURSOR,
                         (cur_x, ecg_top), (cur_x, ecg_top + ecg_h), 1)

        # 5. Border
        pygame.draw.rect(screen, (30, 50, 70), (ecg_left, ecg_top, ecg_w, ecg_h), 1)

    # ------------------------------------------------------------------
    # State-specific render helpers
    # ------------------------------------------------------------------

    def _render_watching(self, screen: pygame.Surface, cx: int, py: int) -> None:
        self._render_hint(screen, cx, py)

    def _render_player_turn(
        self, screen: pygame.Surface, cx: int, py: int
    ) -> None:
        self._render_hint(screen, cx, py)

    def _render_hint(self, screen: pygame.Surface, cx: int, py: int) -> None:
        s = self._font_small.render(t("heal.overlay.hint"), True, _TEXT_DIM)
        screen.blit(s, (cx - s.get_width() // 2, py + 152))

    def _render_result(
        self, screen: pygame.Surface, cx: int, py: int
    ) -> None:
        _GREAT_COL = (140, 230, 100)
        _WEAK_COL  = (255, 160,  60)
        quality_map = {
            "perfect": ("heal.overlay.perfect", _PERFECT_COL),
            "great":   ("heal.overlay.great",   _GREAT_COL),
            "good":    ("heal.overlay.good",     _GOOD_COL),
            "poor":    ("heal.overlay.poor",     _WEAK_COL),
            "miss":    ("heal.overlay.miss",     _POOR_COL),
        }
        label, col = quality_map.get(self._quality, ("heal.overlay.miss", _POOR_COL))

        ql_s = self._font_big.render(t(label), True, col)
        screen.blit(ql_s, (cx - ql_s.get_width() // 2, py + 130))

        hp_s = self._font_med.render(f"+{self._actual_heal} HP", True, _PERFECT_COL)
        screen.blit(hp_s, (cx - hp_s.get_width() // 2, py + 160))

    def _render_dots(self, screen: pygame.Surface, cx: int, y: int) -> None:
        """Three progress dots — one per heartbeat cycle + player's turn."""
        dot_r   = 5
        spacing = 22

        if self._state == _State.WATCHING:
            filled = self._next_beat_idx // 2
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

        _BG2 = (8,  14,  22)
        _CYN = (0, 200, 190)

        pw = min(sw - 60, 500)
        ph = 360
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
        _bullet("heal.help.s1")
        _bullet("heal.help.s2")
        _bullet("heal.help.s3")
        y += 8

        _section("heal.help.h3")
        _bullet("heal.help.key1")
        _bullet("heal.help.key2")
        _bullet("heal.help.key3")
        _bullet("heal.help.key4")

        close_s = self._font_small.render(t("aim.help.close"), True, _TEXT_DIM)
        screen.blit(close_s, (sw // 2 - close_s.get_width() // 2, by + ph - 18))
