"""Vault drain overlay — cursor-tracking credit-drain minigame on the final floor.

Not a Scene — no push/pop.  GameScene owns a VaultOverlay instance and routes
events / update / render calls to it each frame.

Mechanics:
  - 1D vertical cursor (0.0 = bottom, 1.0 = top), starts centred at 0.5
  - Player holds UP/W or DOWN/S to push the cursor toward the target zone
  - Physics: outward spring (pushes away from centre) + low damping (momentum/
    overshoot) + wind drift.  Overshooting centre carries cursor to other side.
  - Every VAULT_CHECK_INTERVAL seconds the cursor zone is evaluated:
      Perfect / Good / Bad / Fail → adjusts drain multiplier and adds heat
  - Credits drain continuously at base_rate × multiplier
  - Player sees credits earned this session (going up) — NOT remaining total
  - Q / Escape → voluntary disconnect (can re-enter vault later)
  - force_close() → patrol interrupt (can still re-enter after combat)

Callback:
  on_complete(credits_this_session: int, fully_drained: bool)
"""
from __future__ import annotations

import math
import random
from enum import auto, Enum
from typing import Callable, TYPE_CHECKING

import pygame

from dungeoneer.core.i18n import t
from dungeoneer.core.settings import (
    VAULT_CHECK_INTERVAL, VAULT_IMPULSE, VAULT_DAMPING,
    VAULT_DRIFT_SIGMA, VAULT_DRIFT_HEAT_SCALE, VAULT_DRIFT_FINALE_MULT,
    VAULT_OUTWARD_BIAS, VAULT_DRIFT_SPEED_VARY, VAULT_DRIFT_SPEED_FREQ,
    VAULT_WIND_SIGMA, VAULT_WIND_DAMPING,
    VAULT_ZONE_PERFECT, VAULT_ZONE_GOOD, VAULT_ZONE_BAD,
    VAULT_DRAIN_SECONDS, VAULT_MULT_MIN, VAULT_MULT_MAX,
    VAULT_FULL_DRAIN_BONUS, VAULT_RESULT_PAUSE,
    VAULT_HEAT_PERFECT, VAULT_HEAT_GOOD, VAULT_HEAT_BAD, VAULT_HEAT_FAIL,
    VAULT_MULT_PERFECT, VAULT_MULT_GOOD, VAULT_MULT_BAD, VAULT_MULT_FAIL,
    SCREEN_WIDTH, SCREEN_HEIGHT,
)

if TYPE_CHECKING:
    from dungeoneer.entities.player import Player
    from dungeoneer.systems.heat import HeatSystem
    from dungeoneer.core.difficulty import Difficulty


# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
_BG          = (8,  12,  22, 235)
_BORDER      = (40, 180, 150)
_COL_TITLE   = (0, 230, 190)
_COL_TEXT    = (170, 200, 185)
_COL_DIM     = (70,  90, 80)
_COL_CREDITS = (80, 230, 160)
_COL_MULT    = (200, 200, 80)

# Zone gauge colours
_COL_PERFECT = (0,   220,  80)
_COL_GOOD    = (160, 220,  40)
_COL_BAD     = (220, 140,  20)
_COL_FAIL    = (220,  40,  40)
_COL_ZONE_BG = (20,   35,  30)

# Check-result flash colours
_FLASH_PERFECT = (0,   255,  90, 180)
_FLASH_GOOD    = (160, 230,  40, 160)
_FLASH_BAD     = (230, 130,  20, 160)
_FLASH_FAIL    = (230,  40,  40, 180)

# Cursor marker
_COL_CURSOR  = (240, 240, 255)

# Panel size
_PW = 500
_PH = 380
_GAUGE_W  = 28
_GAUGE_H  = 220
_GAUGE_X_OFF = 50   # from panel left
_INFO_X_OFF  = 120  # from panel left


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

class _State(Enum):
    DRAINING = auto()   # main gameplay loop
    RESULT   = auto()   # brief disconnect message pause
    DONE     = auto()   # fires callback


# ---------------------------------------------------------------------------
# Zone helpers
# ---------------------------------------------------------------------------

def _get_zone(pos: float) -> str:
    """Return zone name based on cursor distance from 0.5."""
    d = abs(pos - 0.5)
    if d <= VAULT_ZONE_PERFECT:
        return "perfect"
    if d <= VAULT_ZONE_GOOD:
        return "good"
    if d <= VAULT_ZONE_BAD:
        return "bad"
    return "fail"


def _zone_colour(zone: str) -> tuple:
    return {
        "perfect": _COL_PERFECT,
        "good":    _COL_GOOD,
        "bad":     _COL_BAD,
        "fail":    _COL_FAIL,
    }.get(zone, _COL_FAIL)


def _zone_flash_colour(zone: str) -> tuple:
    return {
        "perfect": _FLASH_PERFECT,
        "good":    _FLASH_GOOD,
        "bad":     _FLASH_BAD,
        "fail":    _FLASH_FAIL,
    }.get(zone, _FLASH_FAIL)


def _zone_heat(zone: str) -> int:
    return {
        "perfect": VAULT_HEAT_PERFECT,
        "good":    VAULT_HEAT_GOOD,
        "bad":     VAULT_HEAT_BAD,
        "fail":    VAULT_HEAT_FAIL,
    }.get(zone, VAULT_HEAT_FAIL)


def _zone_mult_delta(zone: str) -> float:
    return {
        "perfect": VAULT_MULT_PERFECT,
        "good":    VAULT_MULT_GOOD,
        "bad":     VAULT_MULT_BAD,
        "fail":    VAULT_MULT_FAIL,
    }.get(zone, VAULT_MULT_FAIL)


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class VaultOverlay:
    """Cursor-tracking vault-drain minigame overlay.

    Instantiate in GameScene, route events, call update() and render() each frame.
    The overlay is *not* a pygame Scene — it never gets pushed/popped.
    """

    def __init__(
        self,
        total_credits: int,
        credits_already_drained: int,
        player: "Player",
        heat_system: "HeatSystem",
        difficulty: "Difficulty",
        on_complete: Callable[[int, bool], None],
        session_state: "dict | None" = None,
    ) -> None:
        self._total_credits      = total_credits
        self._credits_banked_in  = credits_already_drained   # from prior sessions
        self._player             = player
        self._heat_system        = heat_system
        self._difficulty         = difficulty
        self._on_complete        = on_complete

        self._state              = _State.DRAINING
        self._completed          = False

        # Cursor physics — restored from session_state on re-entry, fresh otherwise
        s = session_state or {}
        self._pos:        float = s.get("pos",        0.5)
        self._velocity:   float = s.get("velocity",   0.0)
        self._wind:       float = s.get("wind",        0.0)
        self._drift_time: float = s.get("drift_time", 0.0)
        self._keys_held:  set[int] = set()
        # Grace period: suppress drift/wind for the first 0.5s so cursor
        # doesn't shoot away before the player can react (skipped on re-entry)
        self._grace_timer: float = 0.0 if session_state else 0.5

        # Drain state
        self._multiplier: float = s.get("multiplier", 1.0)
        self._credits_drained_f: float = 0.0   # float precision accumulator
        self._credits_remaining: float = max(0.0, total_credits - credits_already_drained)

        # Check timer
        self._check_timer: float = s.get("check_timer", VAULT_CHECK_INTERVAL)
        self._last_zone: str | None = s.get("last_zone")
        self._flash_timer: float = 0.0
        self._flash_duration: float = 0.4   # seconds to show zone flash

        # Result pause
        self._result_timer: float = 0.0
        self._result_voluntary: bool = True   # True=Q, False=patrol

        # Fonts
        try:
            self._font_title  = pygame.font.SysFont("consolas", 18, bold=True)
            self._font_body   = pygame.font.SysFont("consolas", 15)
            self._font_small  = pygame.font.SysFont("consolas", 13)
            self._font_zone   = pygame.font.SysFont("consolas", 17, bold=True)
        except Exception:
            self._font_title  = pygame.font.Font(None, 22)
            self._font_body   = pygame.font.Font(None, 18)
            self._font_small  = pygame.font.Font(None, 16)
            self._font_zone   = pygame.font.Font(None, 20)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_active(self) -> bool:
        return not self._completed

    @property
    def credits_drained_this_session(self) -> int:
        return round(self._credits_drained_f)

    def get_session_state(self) -> dict:
        """Return all cursor/drain state so GameScene can restore it on re-entry."""
        return {
            "pos":         self._pos,
            "velocity":    self._velocity,
            "wind":        self._wind,
            "drift_time":  self._drift_time,
            "multiplier":  self._multiplier,
            "check_timer": self._check_timer,
            "last_zone":   self._last_zone,
        }

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def force_close(self) -> None:
        """Called by GameScene when a heat level-up fires during drain (patrol interrupt)."""
        if self._state == _State.DRAINING:
            self._result_voluntary = False
            self._state = _State.RESULT
            self._result_timer = VAULT_RESULT_PAUSE

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._state != _State.DRAINING:
            return

        if event.type == pygame.KEYDOWN:
            self._keys_held.add(event.key)
            if event.key in (pygame.K_q, pygame.K_ESCAPE):
                self._result_voluntary = True
                self._state = _State.RESULT
                self._result_timer = VAULT_RESULT_PAUSE

        elif event.type == pygame.KEYUP:
            self._keys_held.discard(event.key)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        if self._completed:
            return

        if self._state == _State.DRAINING:
            self._update_draining(dt)

        elif self._state == _State.RESULT:
            self._result_timer -= dt
            if self._result_timer <= 0.0:
                self._state = _State.DONE

        if self._state == _State.DONE:
            self._completed = True
            fully = (self._credits_remaining <= 0.0)
            self._on_complete(self.credits_drained_this_session, fully)

    def _update_draining(self, dt: float) -> None:
        # --- Grace period: tick down, suppress drift/wind while active ---
        in_grace = self._grace_timer > 0.0
        if in_grace:
            self._grace_timer -= dt

        # --- Key impulse (continuous while held) ---
        _UP_KEYS   = {pygame.K_UP, pygame.K_w}
        _DOWN_KEYS = {pygame.K_DOWN, pygame.K_s}
        if self._keys_held & _UP_KEYS:
            self._velocity += VAULT_IMPULSE * dt
        if self._keys_held & _DOWN_KEYS:
            self._velocity -= VAULT_IMPULSE * dt

        # --- Drift scaling (heat + difficulty + finale) ---
        self._drift_time += dt
        heat_level = self._heat_system.level if self._heat_system else 1
        diff_mult = self._difficulty.vault_drift_mult
        finale_mult = 1.0
        if self._total_credits > 0:
            drained_total = self._credits_banked_in + self._credits_drained_f
            if drained_total / self._total_credits >= 0.80:
                finale_mult = VAULT_DRIFT_FINALE_MULT
        scale = (1.0 + VAULT_DRIFT_HEAT_SCALE * (heat_level - 1)) * diff_mult * finale_mult

        if not in_grace:
            # --- Outward spring: main challenge force, pushes cursor away from centre ---
            # sqrt(distance) so force grows sub-linearly: strong near centre,
            # but capped at edges so player can always fight back even at high heat
            d = self._pos - 0.5
            sign = 1.0 if d >= 0.0 else -1.0
            self._velocity += VAULT_OUTWARD_BIAS * scale * sign * math.sqrt(abs(d) + 1e-6) * dt

            # --- Persistent wind: slow random walk — gives sustained current to fight ---
            wind_sigma = VAULT_WIND_SIGMA * scale
            self._wind += random.gauss(0.0, wind_sigma) * dt
            self._wind *= VAULT_WIND_DAMPING
            self._velocity += self._wind * dt

            # --- Frame noise: fast random jitter that averages out (keeps cursor twitchy) ---
            _t = self._drift_time
            speed_cycle = (
                1.0
                + VAULT_DRIFT_SPEED_VARY * (
                    0.5 * abs(math.sin(2 * math.pi * VAULT_DRIFT_SPEED_FREQ * _t))
                    + 0.5 * abs(math.sin(2 * math.pi * VAULT_DRIFT_SPEED_FREQ * 1.618 * _t))
                )
            )
            drift_sigma = VAULT_DRIFT_SIGMA * scale * speed_cycle
            self._velocity += random.gauss(0.0, drift_sigma) * dt

        # --- Damping ---
        self._velocity *= VAULT_DAMPING

        # --- Integrate ---
        self._pos += self._velocity * dt

        # --- Boundary bounce ---
        if self._pos < 0.0:
            self._pos = 0.0
            self._velocity *= -0.5
        elif self._pos > 1.0:
            self._pos = 1.0
            self._velocity *= -0.5

        # --- Flash timer ---
        if self._flash_timer > 0.0:
            self._flash_timer -= dt

        # --- Periodic check ---
        self._check_timer -= dt
        if self._check_timer <= 0.0:
            self._check_timer = VAULT_CHECK_INTERVAL
            self._do_check()

        # --- Credit drain ---
        if self._credits_remaining > 0.0:
            base_rate = self._total_credits / VAULT_DRAIN_SECONDS
            drained = base_rate * self._multiplier * dt
            actual = min(drained, self._credits_remaining)
            self._credits_drained_f += actual
            self._credits_remaining -= actual
            if self._credits_remaining <= 0.0:
                self._credits_remaining = 0.0
                # Vault fully drained — show result then close
                self._result_voluntary = True
                self._state = _State.RESULT
                self._result_timer = VAULT_RESULT_PAUSE

    def _do_check(self) -> None:
        """Evaluate cursor zone, adjust multiplier, add heat."""
        zone = _get_zone(self._pos)
        self._last_zone = zone

        # Multiplier change
        delta = _zone_mult_delta(zone)
        self._multiplier = max(VAULT_MULT_MIN,
                               min(VAULT_MULT_MAX, self._multiplier + delta))

        # Add heat via HeatSystem (may trigger HeatLevelUpEvent → force_close())
        heat = _zone_heat(zone)
        if self._heat_system is not None:
            self._heat_system.add_heat(heat)

        self._flash_timer = self._flash_duration

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(self, screen: pygame.Surface) -> None:
        if self._completed:
            return

        sw, sh = SCREEN_WIDTH, SCREEN_HEIGHT
        ox = (sw - _PW) // 2
        oy = (sh - _PH) // 2

        # Dim backdrop
        dim = pygame.Surface((sw, sh), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 150))
        screen.blit(dim, (0, 0))

        # Panel background
        panel = pygame.Surface((_PW, _PH), pygame.SRCALPHA)
        panel.fill(_BG)
        screen.blit(panel, (ox, oy))
        pygame.draw.rect(screen, _BORDER, (ox, oy, _PW, _PH), 2, border_radius=5)

        # Edge glow at heat level 3+
        if self._heat_system and self._heat_system.level >= 3:
            glow_col    = self._heat_system.level_colour
            glow_pulse  = 0.5 + 0.5 * abs(math.sin(
                (self._drift_time if self._state == _State.DRAINING else 0.0) * 1.8
            ))
            glow_alpha  = round((20 + 60 * ((self._heat_system.level - 2) / 3)) * glow_pulse)
            glow_surf   = pygame.Surface((_PW, _PH), pygame.SRCALPHA)
            for t_px in range(5, 0, -1):
                a = max(0, glow_alpha - t_px * 8)
                pygame.draw.rect(
                    glow_surf, (*glow_col, a),
                    (t_px, t_px, _PW - 2 * t_px, _PH - 2 * t_px),
                    2, border_radius=5,
                )
            screen.blit(glow_surf, (ox, oy))

        # Title
        title_surf = self._font_title.render(
            t("vault.overlay.title"), True, _COL_TITLE
        )
        screen.blit(title_surf, (ox + 18, oy + 14))

        # Separator
        sep_y = oy + 14 + title_surf.get_height() + 6
        pygame.draw.line(screen, (30, 80, 65),
                         (ox + 14, sep_y), (ox + _PW - 14, sep_y))

        # Zone flash overlay (behind gauge)
        if self._flash_timer > 0.0 and self._last_zone is not None:
            alpha = round(200 * (self._flash_timer / self._flash_duration))
            flash_col = (*_zone_flash_colour(self._last_zone)[:3], alpha)
            flash_surf = pygame.Surface((_PW, _PH), pygame.SRCALPHA)
            flash_surf.fill(flash_col)
            screen.blit(flash_surf, (ox, oy))

        # --- Vertical gauge (left side) ---
        gx = ox + _GAUGE_X_OFF
        gy = sep_y + 20
        gh = _GAUGE_H
        gw = _GAUGE_W

        # Gauge background
        pygame.draw.rect(screen, _COL_ZONE_BG, (gx, gy, gw, gh), border_radius=3)
        pygame.draw.rect(screen, (30, 60, 50), (gx, gy, gw, gh), 1, border_radius=3)

        # Zone colour bands (from bottom to top: fail, bad, good, perfect, good, bad, fail)
        # Centred at 0.5 → map [0,1] to pixel rows (top=1.0, bottom=0.0)
        def _pos_to_py(p: float) -> int:
            return gy + gh - round(p * gh)

        def _draw_band(lo: float, hi: float, col: tuple) -> None:
            ty = _pos_to_py(hi)
            by = _pos_to_py(lo)
            if by > ty:
                pygame.draw.rect(screen, col, (gx, ty, gw, by - ty))

        _draw_band(0.0,  0.5 - VAULT_ZONE_BAD,     _COL_FAIL)
        _draw_band(0.5 + VAULT_ZONE_BAD, 1.0,       _COL_FAIL)
        _draw_band(0.5 - VAULT_ZONE_BAD, 0.5 - VAULT_ZONE_GOOD,  _COL_BAD)
        _draw_band(0.5 + VAULT_ZONE_GOOD, 0.5 + VAULT_ZONE_BAD,  _COL_BAD)
        _draw_band(0.5 - VAULT_ZONE_GOOD, 0.5 - VAULT_ZONE_PERFECT, _COL_GOOD)
        _draw_band(0.5 + VAULT_ZONE_PERFECT, 0.5 + VAULT_ZONE_GOOD, _COL_GOOD)
        _draw_band(0.5 - VAULT_ZONE_PERFECT, 0.5 + VAULT_ZONE_PERFECT, _COL_PERFECT)

        # Gauge border
        pygame.draw.rect(screen, (50, 120, 100), (gx, gy, gw, gh), 1, border_radius=3)

        # Cursor marker
        cursor_y = _pos_to_py(self._pos)
        marker_h = 4
        pygame.draw.rect(screen, _COL_CURSOR,
                         (gx - 3, cursor_y - marker_h // 2, gw + 6, marker_h),
                         border_radius=2)

        # --- Info panel (right of gauge) ---
        ix = ox + _INFO_X_OFF
        iy = sep_y + 24
        line_h = self._font_body.get_height() + 6

        # Credits earned (total across all sessions, so resume starts from right amount)
        cred_text = t("vault.overlay.credits").format(
            n=self._credits_banked_in + self.credits_drained_this_session
        )
        cred_surf = self._font_body.render(cred_text, True, _COL_CREDITS)
        screen.blit(cred_surf, (ix, iy))
        iy += line_h + 2

        # Multiplier
        mult_text = t("vault.overlay.multiplier").format(n=f"{self._multiplier:.2f}")
        mult_surf = self._font_body.render(mult_text, True, _COL_MULT)
        screen.blit(mult_surf, (ix, iy))
        iy += line_h + 10

        # --- Heat indicator ---
        heat_level    = self._heat_system.level    if self._heat_system else 1
        heat_progress = self._heat_system.progress if self._heat_system else 0.0
        heat_col      = self._heat_system.level_colour if self._heat_system else (80, 200, 80)
        heat_name     = self._heat_system.level_name   if self._heat_system else "GHOST"

        heat_label_surf = self._font_small.render(
            t("vault.overlay.heat"), True, _COL_TEXT
        )
        screen.blit(heat_label_surf, (ix, iy))

        bar_x = ix
        bar_y = iy + heat_label_surf.get_height() + 3
        bar_w = 180
        bar_h = 12

        # Bar background
        pygame.draw.rect(screen, (20, 40, 30), (bar_x, bar_y, bar_w, bar_h),
                         border_radius=2)
        # Bar fill — pulses faster at high heat levels
        fill_w = round(bar_w * heat_progress)
        if fill_w > 0:
            if heat_level >= 3:
                pulse = 0.65 + 0.35 * abs(math.sin(
                    self._drift_time * (1.8 + heat_level * 0.6)
                ))
                fill_col = tuple(round(c * pulse) for c in heat_col)
            else:
                fill_col = heat_col
            pygame.draw.rect(screen, fill_col,
                             (bar_x, bar_y, fill_w, bar_h), border_radius=2)
        # Bar border
        pygame.draw.rect(screen, (50, 80, 60), (bar_x, bar_y, bar_w, bar_h),
                         1, border_radius=2)
        # Level name to the right
        lname_surf = self._font_small.render(heat_name, True, heat_col)
        screen.blit(lname_surf, (bar_x + bar_w + 7, bar_y + (bar_h - lname_surf.get_height()) // 2))

        iy = bar_y + bar_h + 10

        # Last check result
        if self._last_zone is not None:
            sep2_y = iy
            pygame.draw.line(screen, (30, 70, 60),
                             (ix, sep2_y), (ox + _PW - 20, sep2_y))
            iy += 8
            zone_key = f"vault.zone.{self._last_zone}"
            zone_surf = self._font_zone.render(
                t(zone_key), True, _zone_colour(self._last_zone)
            )
            screen.blit(zone_surf, (ix, iy))

        # Result / FULLY DRAINED message
        if self._state == _State.RESULT:
            if self._credits_remaining <= 0.0:
                msg = t("vault.overlay.drained")
                col = _COL_PERFECT
            else:
                msg = t("vault.overlay.severed")
                col = _COL_FAIL
            msg_surf = self._font_zone.render(msg, True, col)
            mx = ox + (_PW - msg_surf.get_width()) // 2
            my = oy + _PH - 70
            screen.blit(msg_surf, (mx, my))

        # Disconnect hint + controls hint
        if self._state == _State.DRAINING:
            hint_surf = self._font_small.render(
                t("vault.overlay.disconnect"), True, _COL_DIM
            )
            ctrl_surf = self._font_small.render(
                t("vault.overlay.controls"), True, _COL_TEXT
            )
            hint_y = oy + _PH - hint_surf.get_height() - 10
            screen.blit(hint_surf, (
                ox + (_PW - hint_surf.get_width()) // 2,
                hint_y,
            ))
            screen.blit(ctrl_surf, (
                ox + (_PW - ctrl_surf.get_width()) // 2,
                hint_y - ctrl_surf.get_height() - 4,
            ))
