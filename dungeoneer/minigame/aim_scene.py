"""Aiming overlay — in-world arc rendered on top of the game world.

Not a Scene — no push/pop.  GameScene owns an AimOverlay instance directly,
routes events to it, and calls update()/render() each frame.
"""
from __future__ import annotations

import math
import random
from enum import auto, Enum
from typing import Callable, List, Optional, TYPE_CHECKING

import pygame

from dungeoneer.core.i18n import t

if TYPE_CHECKING:
    from dungeoneer.items.weapon import Weapon
    from dungeoneer.entities.player import Player
    from dungeoneer.entities.enemy import Enemy


# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
_ARC_TRACK_FILL = (20,  40,  60,  130)
_ARC_BORDER     = (40,  80, 130,  180)
_HIT_ZONE_FILL  = (0,  200,  80,  110)
_HIT_ZONE_EDGE  = (0,  220, 100,  200)
_NEEDLE         = (230, 230,  50)
_NEEDLE_GLOW    = (70,   70,  15)
_CENTER_DOT     = (230, 230,  50)
_END_MARK       = (60,  100, 160)
_TEXT           = (180, 220, 200)
_TEXT_DIM       = (80,  120, 100)
_COL_MISS       = (200,  55,  55)
_COL_HIT        = (80,  200,  80)
_COL_CRIT       = (240, 220,   0)

_DONE_PAUSE = 0.35


class _State(Enum):
    AIMING = auto()
    RESULT = auto()
    DONE   = auto()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _arc_polygon(
    lcx: float, lcy: float,
    r_outer: float, r_inner: float,
    start_rad: float, stop_rad: float,
    steps: int = 20,
) -> list:
    """Return polygon points for an annular arc sector.

    Angles are in math-space radians (CCW from +x, y-up).
    Screen rendering uses  x = lcx + r*cos(a),  y = lcy - r*sin(a).
    """
    pts_outer = []
    pts_inner = []
    for i in range(steps + 1):
        a = start_rad + (i / steps) * (stop_rad - start_rad)
        ca, sa = math.cos(a), math.sin(a)
        pts_outer.append((lcx + r_outer * ca, lcy - r_outer * sa))
        pts_inner.append((lcx + r_inner * ca, lcy - r_inner * sa))
    return pts_outer + list(reversed(pts_inner))


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class AimOverlay:
    """In-world aiming arc overlay.

    The 90° (AIM_ARC_DEGREES) arc is centred on the player tile and points
    toward the target.  The player stops a rotating needle inside the green
    hit zone by pressing F or clicking.

    Callback:
        on_complete(results: list[float])  — one accuracy per shot;
        -1.0 = miss, 0.0–1.0 = hit (1.0 = bullseye / crit).
    """

    def __init__(
        self,
        weapon: "Weapon",
        player: "Player",
        target: "Enemy",
        shots: int,
        on_complete: Callable[[List[float]], None],
        needle_speed_mult: float = 1.0,
    ) -> None:
        from dungeoneer.core import settings as S

        self._weapon       = weapon
        self._player       = player
        self._target       = target
        self._total_shots  = shots
        self._on_complete  = on_complete

        self._arc_degrees  = S.AIM_ARC_DEGREES
        self._min_zone     = S.AIM_MIN_ZONE
        self._start_speed  = S.AIM_START_SPEED * needle_speed_mult
        self._bounce_boost = self._start_speed * S.AIM_BOUNCE_SPEED_BOOST
        self._crit_thresh  = S.AIM_CRIT_THRESHOLD
        self._result_pause = S.AIM_RESULT_PAUSE
        self._radius       = S.AIM_RADIUS_PX

        self._results: List[float]       = []
        self._current_shot               = 0
        self._state                      = _State.AIMING
        self._result_timer               = 0.0
        self._done_timer                 = 0.0
        self._last_accuracy: Optional[float] = None
        self._completed                  = False
        self._show_help                  = False

        try:
            self._font_med   = pygame.font.SysFont("consolas", 16, bold=True)
            self._font_small = pygame.font.SysFont("consolas", 13)
            self._font_big   = pygame.font.SysFont("consolas", 26, bold=True)
        except Exception:
            self._font_med   = pygame.font.Font(None, 20)
            self._font_small = pygame.font.Font(None, 16)
            self._font_big   = pygame.font.Font(None, 32)

        self._init_shot()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_active(self) -> bool:
        """True while the overlay should be kept alive."""
        return not self._completed

    # ------------------------------------------------------------------
    # Per-shot initialisation
    # ------------------------------------------------------------------

    def _init_shot(self) -> None:
        w = self._weapon
        dist = self._target_dist()
        zone_size = max(self._min_zone, w.aim_zone_base - dist * w.aim_zone_penalty)
        self._zone_size = zone_size

        margin = zone_size * 0.5
        self._zone_start = random.uniform(margin, self._arc_degrees - zone_size - margin)
        self._zone_end   = self._zone_start + zone_size

        self._needle_angle = random.uniform(0.0, self._arc_degrees)
        self._needle_dir   = 1.0 if random.random() > 0.5 else -1.0
        self._speed        = self._start_speed

    def _target_dist(self) -> int:
        return abs(self._player.x - self._target.x) + abs(self._player.y - self._target.y)

    # ------------------------------------------------------------------
    # Angle helpers
    # ------------------------------------------------------------------

    def _arc_center_angle(self, cam_offset_x: int, cam_offset_y: int) -> float:
        """Direction angle (math-space radians) from player toward target."""
        from dungeoneer.core.settings import TILE_SIZE
        half = TILE_SIZE // 2
        px = self._player.x * TILE_SIZE - cam_offset_x + half
        py = self._player.y * TILE_SIZE - cam_offset_y + half
        tx = self._target.x * TILE_SIZE - cam_offset_x + half
        ty = self._target.y * TILE_SIZE - cam_offset_y + half
        return math.atan2(-(ty - py), tx - px)

    def _pos_to_angle(self, pos_deg: float, center_angle: float) -> float:
        """Map arc position [0, arc_degrees] to math-space radians."""
        half_arc = self._arc_degrees / 2.0
        return center_angle + math.radians(pos_deg - half_arc)

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Route a pygame event to the overlay.  Consumes all events."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
            self._show_help = not self._show_help
            return
        if self._show_help:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._show_help = False
            return  # eat all other input while help is open
        if self._state == _State.AIMING:
            fire = (
                (event.type == pygame.KEYDOWN and event.key == pygame.K_f)
                or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)
            )
            if fire:
                self._stop_needle()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # Cancel — remaining shots all miss
                remaining = self._total_shots - self._current_shot
                self._results.extend([-1.0] * remaining)
                self._state      = _State.DONE
                self._done_timer = _DONE_PAUSE

    # ------------------------------------------------------------------
    # Logic
    # ------------------------------------------------------------------

    def _stop_needle(self) -> None:
        angle = self._needle_angle
        if self._zone_start <= angle <= self._zone_end:
            zone_center = self._zone_start + self._zone_size / 2.0
            half        = self._zone_size / 2.0
            accuracy    = max(0.0, min(1.0, 1.0 - abs(angle - zone_center) / half))
        else:
            accuracy = -1.0

        self._results.append(accuracy)
        self._last_accuracy = accuracy
        self._state         = _State.RESULT
        self._result_timer  = self._result_pause

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        if self._completed:
            return

        if self._state == _State.AIMING:
            if self._show_help:
                return  # freeze needle while help is open
            self._needle_angle += self._needle_dir * self._speed * dt
            if self._needle_angle >= self._arc_degrees:
                self._needle_angle = self._arc_degrees
                self._needle_dir = -1.0
                self._speed += self._bounce_boost
            elif self._needle_angle <= 0.0:
                self._needle_angle = 0.0
                self._needle_dir = 1.0
                self._speed += self._bounce_boost

        elif self._state == _State.RESULT:
            self._result_timer -= dt
            if self._result_timer <= 0.0:
                self._current_shot += 1
                if self._current_shot < self._total_shots:
                    self._init_shot()
                    self._state = _State.AIMING
                else:
                    self._state      = _State.DONE
                    self._done_timer = _DONE_PAUSE

        elif self._state == _State.DONE:
            self._done_timer -= dt
            if self._done_timer <= 0.0:
                self._completed = True
                self._on_complete(self._results)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self, screen: pygame.Surface, cam_offset_x: int, cam_offset_y: int) -> None:
        from dungeoneer.core.settings import TILE_SIZE

        half = TILE_SIZE // 2
        cx = self._player.x * TILE_SIZE - cam_offset_x + half
        cy = self._player.y * TILE_SIZE - cam_offset_y + half

        center_angle = self._arc_center_angle(cam_offset_x, cam_offset_y)
        r      = self._radius
        r_in   = r - 12
        half_r = math.radians(self._arc_degrees / 2.0)
        arc_start = center_angle - half_r
        arc_stop  = center_angle + half_r

        # Work on a small SRCALPHA surface to support transparency
        size = r * 2 + 8
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        lcx = lcy = size // 2

        # Arc track
        track_pts = _arc_polygon(lcx, lcy, r, r_in, arc_start, arc_stop, steps=24)
        if len(track_pts) >= 3:
            pygame.draw.polygon(surf, _ARC_TRACK_FILL, track_pts)
            pygame.draw.polygon(surf, _ARC_BORDER, track_pts, 1)

        # Hit zone
        zone_start = self._pos_to_angle(self._zone_start, center_angle)
        zone_stop  = self._pos_to_angle(self._zone_end,   center_angle)
        zone_pts = _arc_polygon(lcx, lcy, r, r_in, zone_start, zone_stop, steps=14)
        if len(zone_pts) >= 3:
            pygame.draw.polygon(surf, _HIT_ZONE_FILL, zone_pts)
            pygame.draw.polygon(surf, _HIT_ZONE_EDGE, zone_pts, 2)

        screen.blit(surf, (cx - size // 2, cy - size // 2))

        # Needle (drawn directly on screen for crisp lines)
        needle_rad = self._pos_to_angle(self._needle_angle, center_angle)
        tip_x = int(cx + r * math.cos(needle_rad))
        tip_y = int(cy - r * math.sin(needle_rad))
        pygame.draw.line(screen, _NEEDLE_GLOW, (cx, cy), (tip_x, tip_y), 4)
        pygame.draw.line(screen, _NEEDLE,      (cx, cy), (tip_x, tip_y), 2)
        pygame.draw.circle(screen, _CENTER_DOT, (cx, cy), 4)

        # Arc end tick marks
        for pos in (0.0, self._arc_degrees):
            a  = self._pos_to_angle(pos, center_angle)
            ex = int(cx + r * math.cos(a))
            ey = int(cy - r * math.sin(a))
            pygame.draw.circle(screen, _END_MARK, (ex, ey), 3)

        # Labels
        self._render_labels(screen, cx, cy, r)

        # Result flash
        if self._state == _State.RESULT and self._last_accuracy is not None:
            self._render_result(screen, cx, cy, r)

        # Help overlay (F1)
        if self._show_help:
            self._draw_help_overlay(screen)

    def _render_labels(
        self, screen: pygame.Surface, cx: int, cy: int, r: int
    ) -> None:
        # Target name above the arc
        name_surf = self._font_small.render(self._target.name, True, _TEXT)
        screen.blit(name_surf, (cx - name_surf.get_width() // 2, cy - r - 18))

        # Shot counter for burst weapons (SMG)
        if self._total_shots > 1:
            shot_n = self._current_shot + 1
            s = t("aim.shot_n").format(n=shot_n, total=self._total_shots)
            ssurf = self._font_small.render(s, True, _TEXT_DIM)
            screen.blit(ssurf, (cx - ssurf.get_width() // 2, cy - r - 34))

        # F1 help hint below the arc
        hint_s = self._font_small.render(t("aim.help.hint"), True, _TEXT_DIM)
        screen.blit(hint_s, (cx - hint_s.get_width() // 2, cy + r + 6))

    def _render_result(
        self, screen: pygame.Surface, cx: int, cy: int, r: int
    ) -> None:
        acc = self._last_accuracy
        if acc is None:
            return
        if acc < 0.0:
            label, colour = t("aim.miss"), _COL_MISS
        elif acc >= self._crit_thresh:
            label, colour = t("aim.crit"), _COL_CRIT
        else:
            label, colour = t("aim.hit"), _COL_HIT

        surf = self._font_big.render(label, True, colour)
        screen.blit(surf, (cx - surf.get_width() // 2, cy - r - 52))

    def _draw_help_overlay(self, screen: pygame.Surface) -> None:
        """Full-screen help overlay shown while self._show_help is True (F1)."""
        sw, sh = screen.get_size()

        # Dim background
        dim = pygame.Surface((sw, sh), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 200))
        screen.blit(dim, (0, 0))

        _HELP_BG  = (8,   14,  22)
        _HELP_CYN = (0,  200, 190)
        _HELP_YEL = (210, 215,  60)
        _HELP_GRN = (0,  200,  90)
        _HELP_DIM = (70, 100,  90)

        pw = min(sw - 60, 780)
        ph = 380
        px = (sw - pw) // 2
        py = (sh - ph) // 2

        pygame.draw.rect(screen, _HELP_BG,  (px, py, pw, ph))
        pygame.draw.rect(screen, _HELP_CYN, (px, py, pw, ph), 1)

        # Title
        title_s = self._font_big.render(t("aim.help.title"), True, _HELP_CYN)
        screen.blit(title_s, (sw // 2 - title_s.get_width() // 2, py + 10))
        sep_y = py + 10 + title_s.get_height() + 6
        pygame.draw.line(screen, _HELP_CYN, (px + 20, sep_y), (px + pw - 20, sep_y), 1)

        col_l = px + 24
        col_r = px + pw // 2 + 14
        y_l   = sep_y + 12
        y_r   = sep_y + 12
        lh    = 17
        font  = self._font_small

        def _section(x: int, y: int, text: str) -> int:
            s = self._font_med.render(text, True, _HELP_CYN)
            screen.blit(s, (x, y))
            return y + 20

        def _bullets(x: int, y: int, items: list) -> int:
            for bc, text in items:
                b = font.render("\u2022 ", True, bc)
                screen.blit(b, (x, y))
                screen.blit(font.render(text, True, _TEXT), (x + b.get_width(), y))
                y += lh
            return y

        def _aligned(x: int, y: int, items: list) -> int:
            if not items:
                return y
            col_dx = max(font.size(lbl)[0] for lbl, _, _ in items) + 10
            for lbl, lc, desc in items:
                screen.blit(font.render(lbl,  True, lc),    (x,          y))
                screen.blit(font.render(desc, True, _TEXT), (x + col_dx, y))
                y += lh
            return y

        # ── Left column ──────────────────────────────────────────────
        y_l = _section(col_l, y_l, t("aim.help.mechanic"))
        y_l = _bullets(col_l, y_l, [
            (_HELP_DIM, t("aim.help.mech.1")),
            (_HELP_GRN, t("aim.help.mech.2")),
            (_HELP_GRN, t("aim.help.mech.3")),
            (_TEXT,     t("aim.help.mech.4")),
            (_HELP_DIM, t("aim.help.mech.5")),
            (_HELP_DIM, t("aim.help.mech.zone")),
        ])
        # ── Right column ─────────────────────────────────────────────
        y_r = _section(col_r, y_r, t("aim.help.crit"))
        y_r = _bullets(col_r, y_r, [
            (_COL_CRIT, t("aim.help.crit.1")),
            (_HELP_DIM, t("aim.help.crit.2")),
        ])
        y_r += 10

        y_r = _section(col_r, y_r, t("aim.help.controls"))
        y_r = _aligned(col_r, y_r, [
            (t("aim.help.ctrl.f.key"),   _HELP_YEL, t("aim.help.ctrl.f.desc")),
            (t("aim.help.ctrl.tab.key"), _HELP_YEL, t("aim.help.ctrl.tab.desc")),
            (t("aim.help.ctrl.esc.key"), _HELP_YEL, t("aim.help.ctrl.esc.desc")),
            (t("aim.help.ctrl.f1.key"),  _HELP_YEL, t("aim.help.ctrl.f1.desc")),
        ])

        # Close hint
        close_s = font.render(t("aim.help.close"), True, _HELP_DIM)
        screen.blit(close_s, (sw // 2 - close_s.get_width() // 2, py + ph - 20))
