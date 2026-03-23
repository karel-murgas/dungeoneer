"""Melee power-charge overlay — two-phase hold-and-release mechanic.

Not a Scene — no push/pop.  GameScene owns a MeleeOverlay instance directly,
routes events to it, and calls update()/render() each frame.

Phase 1 — IDLE:
    The bar oscillates using a compound beat pattern (product of two sine waves
    at different frequencies).  The amplitude envelope varies so some cycles
    peak high, others low — the player reads the movement and waits for a good
    moment.  No countdown.  Press [F]/LMB to commit.

Phase 2 — CHARGING:
    A countdown timer starts (MELEE_TIMEOUT seconds).  The player holds [F]/LMB
    and releases at a crest for maximum damage.  If the timer expires the power
    is locked automatically at the current value.

Callback:
    on_complete(power: float)  — 0.0–1.0 mapped to damage_min..damage_max,
    or -1.0 if cancelled.
"""
from __future__ import annotations

import math
import random
from enum import auto, Enum
from typing import Callable, TYPE_CHECKING

import pygame

from dungeoneer.core.i18n import t
from dungeoneer.core.settings import (
    MELEE_FREQ1, MELEE_FREQ2, MELEE_TIMEOUT,
    MELEE_CRIT_THRESHOLD, MELEE_RESULT_PAUSE,
    MELEE_BAR_W, MELEE_BAR_H, TILE_SIZE,
)

if TYPE_CHECKING:
    from dungeoneer.items.weapon import Weapon
    from dungeoneer.entities.player import Player
    from dungeoneer.entities.enemy import Enemy


# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
_BG_BAR        = (20,  25,  35, 200)
_BAR_BORDER    = (60, 100, 130, 220)
_COL_LOW       = (200,  40,  40)    # deep red   — weak
_COL_MID       = (210, 165,  25)    # amber      — medium
_COL_HIGH      = ( 40, 200,  80)    # green      — strong
_COL_CRIT      = (255, 240,  80)    # bright vivid yellow — critical (distinct from amber)
_COL_CRIT_GLOW = (255, 240,  80, 60)
_MARKER        = (240, 240, 255)
_TEXT          = (180, 220, 200)
_TEXT_DIM      = (140, 190, 165)   # readable over dark game background
_COL_RESULT_CRIT = (255, 240,  80)
_COL_RESULT_HIT  = ( 40, 220,  80)
_COL_RESULT_WEAK = (200,  50,  50)
_COL_TIMER_FG    = (120, 200, 180)
_COL_TIMER_BG    = ( 25,  35,  45)


class _State(Enum):
    IDLE     = auto()   # bar oscillating — waiting for first [F]/LMB press
    CHARGING = auto()   # countdown active — hold and release at peak
    RESULT   = auto()
    DONE     = auto()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _power_colour(power: float) -> tuple:
    """Gradient: deep red → amber → green → bright vivid yellow (crit)."""
    if power >= MELEE_CRIT_THRESHOLD:
        return _COL_CRIT
    if power > 0.6:
        ratio = (power - 0.6) / (MELEE_CRIT_THRESHOLD - 0.6)
        return (
            round(_COL_MID[0] + (_COL_HIGH[0] - _COL_MID[0]) * ratio),
            round(_COL_MID[1] + (_COL_HIGH[1] - _COL_MID[1]) * ratio),
            round(_COL_MID[2] + (_COL_HIGH[2] - _COL_MID[2]) * ratio),
        )
    if power > 0.25:
        ratio = (power - 0.25) / 0.35
        return (
            round(_COL_LOW[0] + (_COL_MID[0] - _COL_LOW[0]) * ratio),
            round(_COL_LOW[1] + (_COL_MID[1] - _COL_LOW[1]) * ratio),
            round(_COL_LOW[2] + (_COL_MID[2] - _COL_LOW[2]) * ratio),
        )
    return _COL_LOW


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class MeleeOverlay:
    """Two-phase power-charge bar overlay for melee attacks.

    Callback:
        on_complete(power: float)  — power ∈ [0,1], or -1.0 if cancelled.
    """

    def __init__(
        self,
        weapon: "Weapon",
        player: "Player",
        target: "Enemy",
        on_complete: Callable[[float], None],
        freq_mult: float = 1.0,
    ) -> None:
        self._weapon       = weapon
        self._player       = player
        self._target       = target
        self._on_complete  = on_complete

        self._freq1        = MELEE_FREQ1 * freq_mult
        self._freq2        = MELEE_FREQ2 * freq_mult
        self._phase2       = random.uniform(0.0, 2.0 * math.pi)  # random envelope start
        self._timeout      = MELEE_TIMEOUT
        self._crit_thresh  = MELEE_CRIT_THRESHOLD
        self._result_pause = MELEE_RESULT_PAUSE
        self._bar_w        = MELEE_BAR_W
        self._bar_h        = MELEE_BAR_H

        self._state        = _State.IDLE
        self._time         = 0.0          # total elapsed (drives oscillation)
        self._charge_time  = 0.0          # time since CHARGING began
        self._power        = 0.0          # current oscillation value
        self._locked_power = 0.0          # value at release / timeout
        self._result_timer = 0.0
        self._completed    = False

        try:
            self._font_med   = pygame.font.SysFont("consolas", 14, bold=True)
            self._font_small = pygame.font.SysFont("consolas", 12)
            self._font_big   = pygame.font.SysFont("consolas", 22, bold=True)
        except Exception:
            self._font_med   = pygame.font.Font(None, 18)
            self._font_small = pygame.font.Font(None, 14)
            self._font_big   = pygame.font.Font(None, 26)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_active(self) -> bool:
        """True while the overlay should be kept alive."""
        return not self._completed

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Route a pygame event.  Consumes all events while active."""
        if self._state == _State.IDLE:
            start = (
                (event.type == pygame.KEYDOWN and event.key == pygame.K_f)
                or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)
            )
            cancel = event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            if cancel:
                self._locked_power = -1.0
                self._state = _State.DONE
            elif start:
                self._state = _State.CHARGING
                self._charge_time = 0.0

        elif self._state == _State.CHARGING:
            release = (
                (event.type == pygame.KEYUP and event.key == pygame.K_f)
                or (event.type == pygame.MOUSEBUTTONUP and event.button == 1)
            )
            if release:
                self._lock_power()
            # Esc is intentionally ignored during CHARGING — no accidental cancel

    # ------------------------------------------------------------------
    # Logic
    # ------------------------------------------------------------------

    def _lock_power(self) -> None:
        self._locked_power = self._power
        self._state        = _State.RESULT
        self._result_timer = self._result_pause

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        if self._completed:
            return

        if self._state == _State.CHARGING:
            self._time += dt
            self._charge_time += dt
            # Compound sine: primary wave modulated by envelope wave (no acceleration)
            s1 = math.sin(2.0 * math.pi * self._freq1 * self._time)
            s2 = math.sin(2.0 * math.pi * self._freq2 * self._time + self._phase2)
            # Envelope: 0.55–1.0 so even worst cycles give decent damage
            envelope = 0.55 + 0.45 * max(0.0, s2)
            self._power = max(0.0, min(1.0, 0.5 + 0.5 * s1 * envelope))
            if self._charge_time >= self._timeout:
                self._lock_power()

        elif self._state == _State.RESULT:
            self._result_timer -= dt
            if self._result_timer <= 0.0:
                self._state = _State.DONE

        if self._state == _State.DONE:
            self._completed = True
            self._on_complete(self._locked_power)

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(self, screen: pygame.Surface, cam_offset_x: int, cam_offset_y: int) -> None:
        if self._completed:
            return

        half = TILE_SIZE // 2
        px = self._player.x * TILE_SIZE - cam_offset_x + half
        py = self._player.y * TILE_SIZE - cam_offset_y + half

        bar_w = self._bar_w
        bar_h = self._bar_h
        bx = px - bar_w // 2
        by = py - TILE_SIZE - bar_h - 8  # above player sprite

        # --- Timer bar (thin strip above power bar, visible during CHARGING) ---
        timer_h = 4
        timer_by = by - timer_h - 4
        if self._state == _State.CHARGING:
            time_ratio = max(0.0, 1.0 - self._charge_time / self._timeout)
            pygame.draw.rect(screen, _COL_TIMER_BG, (bx, timer_by, bar_w, timer_h))
            fill = max(0, round(time_ratio * bar_w))
            if fill > 0:
                pygame.draw.rect(screen, _COL_TIMER_FG, (bx, timer_by, fill, timer_h))
            # Time remaining text
            remaining = max(0.0, self._timeout - self._charge_time)
            t_surf = self._font_small.render(f"{remaining:.1f}s", True, _COL_TIMER_FG)
            screen.blit(t_surf, (bx + bar_w + 4, timer_by - 1))

        # --- Background ---
        bg_surf = pygame.Surface((bar_w + 4, bar_h + 4), pygame.SRCALPHA)
        bg_surf.fill(_BG_BAR)
        screen.blit(bg_surf, (bx - 2, by - 2))

        # --- Crit zone marker (rightmost strip) ---
        crit_x = bx + round(self._crit_thresh * bar_w)
        crit_w = bar_w - round(self._crit_thresh * bar_w)
        if crit_w > 0:
            crit_surf = pygame.Surface((crit_w, bar_h), pygame.SRCALPHA)
            crit_surf.fill((*_COL_CRIT[:3], 40))
            screen.blit(crit_surf, (crit_x, by))

        # --- Filled portion (up to current power) ---
        power = self._locked_power if self._state == _State.RESULT else self._power
        fill_w = max(0, min(bar_w, round(power * bar_w)))
        if fill_w > 0:
            colour = _power_colour(power)
            pygame.draw.rect(screen, colour, (bx, by, fill_w, bar_h))

        # --- Bar border ---
        pygame.draw.rect(screen, _BAR_BORDER[:3], (bx - 1, by - 1, bar_w + 2, bar_h + 2), 1)

        # --- Marker (current power level, only while oscillating) ---
        if self._state == _State.CHARGING:
            mx = bx + round(self._power * bar_w)
            pygame.draw.line(screen, _MARKER, (mx, by - 2), (mx, by + bar_h + 1), 2)

        # --- Result text ---
        if self._state == _State.RESULT:
            is_crit = self._locked_power >= self._crit_thresh
            if is_crit:
                txt = t("melee.result.crit")
                col = _COL_RESULT_CRIT
            elif self._locked_power >= 0.5:
                txt = t("melee.result.hit")
                col = _COL_RESULT_HIT
            else:
                txt = t("melee.result.weak")
                col = _COL_RESULT_WEAK
            surf = self._font_big.render(txt, True, col)
            screen.blit(surf, (px - surf.get_width() // 2, by - surf.get_height() - 4))

        # --- Hint text ---
        if self._state == _State.IDLE:
            hint = t("melee.hint_press")
            h_surf = self._font_small.render(hint, True, _TEXT_DIM)
            screen.blit(h_surf, (px - h_surf.get_width() // 2, by + bar_h + 4))
        elif self._state == _State.CHARGING:
            hint = t("melee.hint_release")
            h_surf = self._font_small.render(hint, True, _TEXT)
            screen.blit(h_surf, (px - h_surf.get_width() // 2, by + bar_h + 4))
