"""Melee power-charge overlay — hold and release to time a strike.

Not a Scene — no push/pop.  GameScene owns a MeleeOverlay instance directly,
routes events to it, and calls update()/render() each frame.

A horizontal power bar oscillates with a compound beat pattern (product of two
sine waves at different frequencies).  The amplitude envelope varies — some
cycles peak high, others low — so the player must READ the movement and time
the release to a high crest.  Both frequencies drift upward over time.

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
    MELEE_FREQ1, MELEE_FREQ2, MELEE_FREQ_ACCEL, MELEE_TIMEOUT,
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
_BG_BAR      = (20,  25,  35, 200)
_BAR_BORDER  = (60, 100, 130, 220)
_COL_LOW     = (200, 55,  55)
_COL_MID     = (220, 200, 50)
_COL_HIGH    = (50,  200, 80)
_COL_CRIT    = (255, 220, 40)
_COL_CRIT_GLOW = (255, 220, 40, 60)
_MARKER      = (240, 240, 255)
_TEXT         = (180, 220, 200)
_TEXT_DIM     = (80,  120, 100)
_COL_RESULT_CRIT = (255, 220, 0)
_COL_RESULT_HIT  = (80,  220, 80)
_COL_RESULT_WEAK = (200, 80,  80)


class _State(Enum):
    CHARGING = auto()
    RESULT   = auto()
    DONE     = auto()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _power_colour(power: float) -> tuple:
    """Gradient: red → yellow → green → gold."""
    if power >= MELEE_CRIT_THRESHOLD:
        return _COL_CRIT
    if power > 0.6:
        ratio = (power - 0.6) / 0.4
        return (
            int(_COL_MID[0] + (_COL_HIGH[0] - _COL_MID[0]) * ratio),
            int(_COL_MID[1] + (_COL_HIGH[1] - _COL_MID[1]) * ratio),
            int(_COL_MID[2] + (_COL_HIGH[2] - _COL_MID[2]) * ratio),
        )
    if power > 0.25:
        ratio = (power - 0.25) / 0.35
        return (
            int(_COL_LOW[0] + (_COL_MID[0] - _COL_LOW[0]) * ratio),
            int(_COL_LOW[1] + (_COL_MID[1] - _COL_LOW[1]) * ratio),
            int(_COL_LOW[2] + (_COL_MID[2] - _COL_LOW[2]) * ratio),
        )
    return _COL_LOW


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class MeleeOverlay:
    """In-world power-charge bar overlay for melee attacks.

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
        self._weapon      = weapon
        self._player      = player
        self._target      = target
        self._on_complete = on_complete

        self._freq1       = MELEE_FREQ1 * freq_mult
        self._freq2       = MELEE_FREQ2 * freq_mult
        self._freq_accel  = MELEE_FREQ_ACCEL * freq_mult
        self._phase2      = random.uniform(0.0, 2.0 * math.pi)  # random start for envelope
        self._timeout     = MELEE_TIMEOUT
        self._crit_thresh = MELEE_CRIT_THRESHOLD
        self._result_pause = MELEE_RESULT_PAUSE
        self._bar_w       = MELEE_BAR_W
        self._bar_h       = MELEE_BAR_H

        self._state        = _State.CHARGING
        self._time         = 0.0
        self._power        = 0.0       # current oscillation value
        self._locked_power = 0.0       # value at release
        self._result_timer = 0.0
        self._completed    = False
        self._show_help    = False
        self._grace        = 0.08      # ignore release events for 80ms to avoid instant fire

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
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
            self._show_help = not self._show_help
            return
        if self._show_help:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._show_help = False
            return

        if self._state == _State.CHARGING:
            if self._grace > 0:
                return  # swallow all events during grace period
            release = (
                (event.type == pygame.KEYUP and event.key == pygame.K_f)
                or (event.type == pygame.MOUSEBUTTONUP and event.button == 1)
                # Also accept a second press as "release" for tap-tap style
                or (event.type == pygame.KEYDOWN and event.key == pygame.K_f)
                or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)
            )
            cancel = (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE)
            if cancel:
                self._locked_power = -1.0
                self._state = _State.DONE
                self._result_timer = 0.0
            elif release:
                self._lock_power()

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
            if self._show_help:
                return  # freeze while help is open
            if self._grace > 0:
                self._grace -= dt
            self._time += dt
            t = self._time
            drift = self._freq_accel * t
            # Primary wave — the one the player reads and times
            s1 = math.sin(2.0 * math.pi * (self._freq1 + drift) * t)
            # Envelope wave — slowly modulates amplitude (random phase each attack)
            s2 = math.sin(2.0 * math.pi * (self._freq2 + drift * 0.5) * t + self._phase2)
            # Envelope ranges from 0.55 to 1.0: even at worst, player gets decent damage
            # At best (envelope=1.0), full range including crits is reachable
            envelope = 0.55 + 0.45 * max(0.0, s2)
            # Apply envelope to the primary wave
            self._power = max(0.0, min(1.0, 0.5 + 0.5 * s1 * envelope))
            # Timeout
            if self._time >= self._timeout:
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

        # --- Background ---
        bg_surf = pygame.Surface((bar_w + 4, bar_h + 4), pygame.SRCALPHA)
        bg_surf.fill(_BG_BAR)
        screen.blit(bg_surf, (bx - 2, by - 2))

        # --- Crit zone marker (rightmost strip) ---
        crit_x = bx + int(self._crit_thresh * bar_w)
        crit_w = bar_w - int(self._crit_thresh * bar_w)
        if crit_w > 0:
            crit_surf = pygame.Surface((crit_w, bar_h), pygame.SRCALPHA)
            crit_surf.fill((*_COL_CRIT[:3], 40))
            screen.blit(crit_surf, (crit_x, by))

        # --- Filled portion (up to current power) ---
        power = self._locked_power if self._state == _State.RESULT else self._power
        fill_w = max(0, min(bar_w, int(power * bar_w)))
        if fill_w > 0:
            colour = _power_colour(power)
            pygame.draw.rect(screen, colour, (bx, by, fill_w, bar_h))

        # --- Bar border ---
        pygame.draw.rect(screen, _BAR_BORDER[:3], (bx - 1, by - 1, bar_w + 2, bar_h + 2), 1)

        # --- Marker (current power level) ---
        if self._state == _State.CHARGING:
            mx = bx + int(self._power * bar_w)
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
        if self._state == _State.CHARGING:
            hint = t("melee.hint_release")
            h_surf = self._font_small.render(hint, True, _TEXT_DIM)
            screen.blit(h_surf, (px - h_surf.get_width() // 2, by + bar_h + 4))
            # F1 help hint
            f1 = self._font_small.render("[F1]", True, _TEXT_DIM)
            screen.blit(f1, (px - f1.get_width() // 2, by + bar_h + 18))

        # --- Help overlay ---
        if self._show_help:
            self._render_help(screen)

    def _render_help(self, screen: pygame.Surface) -> None:
        """Full-screen help overlay — mirrors aim/heal pattern."""
        sw, sh = screen.get_size()
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        pw, ph = 520, 280
        ox = (sw - pw) // 2
        oy = (sh - ph) // 2
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((8, 10, 22, 240))
        pygame.draw.rect(panel, (0, 200, 170), panel.get_rect(), 2, border_radius=6)
        screen.blit(panel, (ox, oy))

        cy = oy + 14
        title = self._font_big.render(t("melee.help.title"), True, (0, 220, 180))
        screen.blit(title, (ox + pw // 2 - title.get_width() // 2, cy))
        cy += 34

        lines = [
            t("melee.help.1"),
            t("melee.help.2"),
            t("melee.help.3"),
            t("melee.help.4"),
            "",
            t("melee.help.controls_header"),
            t("melee.help.key_release"),
            t("melee.help.key_cancel"),
            t("melee.help.key_help"),
        ]
        for line in lines:
            if not line:
                cy += 8
                continue
            is_header = line == t("melee.help.controls_header")
            font = self._font_med if is_header else self._font_small
            col = (0, 200, 170) if is_header else _TEXT
            surf = font.render(line, True, col)
            screen.blit(surf, (ox + 24, cy))
            cy += surf.get_height() + 4

        close_hint = self._font_small.render(t("melee.help.close"), True, _TEXT_DIM)
        screen.blit(close_hint, (ox + pw // 2 - close_hint.get_width() // 2, oy + ph - 24))
