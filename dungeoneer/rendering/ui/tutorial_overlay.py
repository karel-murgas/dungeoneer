"""Tutorial overlay — shows in-game tutorial steps once per run when tutorial is enabled.

Two public classes:
  TutorialManager  — tracks which steps have been shown; call should_show(step) to check.
  TutorialOverlay  — renders the tutorial panel over the game screen.

Steps (in typical encounter order):
  "movement"  — game start: WASD / arrows + elevator ([E] descend)
  "enemy"     — first enemy visible: shooting (F) + aim minigame arc
  "container" — first container in FOV: hack minigame intro (Q escape, timer, nodes)
  "ammo"      — first empty clip or extra ranged weapon: C switch, R reload
  "medipack"  — first consumable in inventory: H heal + rhythm minigame EKG diagram

Body text markup: lines starting with ">> " are rendered in amber (accent/warning).
"""
from __future__ import annotations

import math
import os
from typing import Callable

import pygame

from dungeoneer.core import settings
from dungeoneer.core.i18n import t

# ---------------------------------------------------------------------------
# Visual constants
# ---------------------------------------------------------------------------

_BG        = (8, 10, 20, 240)
_BORDER    = (0, 220, 180)
_COL_TITLE = (0, 240, 200)
_COL_BODY  = (160, 200, 190)
_COL_ACCENT_LINE = (230, 170, 60)   # amber — for ">>" prefixed lines
_COL_HINT  = (60, 100, 90)
_COL_IMG   = (12, 24, 22)

_W   = 700
_H   = 420
_PAD = 22
_IMG_W = 240
_IMG_H = 280

# Elevator tile indices in tileset_for_free.png (verified from tile_renderer.py)
_ELEVATOR_CLOSED_INDEX = 36
_FLOOR_INDEX = 112


# ---------------------------------------------------------------------------
# Lazy tileset loader (used for the elevator tile illustration)
# ---------------------------------------------------------------------------

_tileset: object = None
_tileset_tried = False


def _get_tileset():
    global _tileset, _tileset_tried
    if _tileset_tried:
        return _tileset
    _tileset_tried = True
    try:
        from dungeoneer.rendering.spritesheet import SpriteSheet
        path = os.path.normpath(os.path.join(
            os.path.dirname(__file__), "..", "..", "assets", "tiles", "dithart_scifi.png"
        ))
        _tileset = SpriteSheet(path, 32, 32)
    except Exception:
        _tileset = None
    return _tileset


# ---------------------------------------------------------------------------
# TutorialManager
# ---------------------------------------------------------------------------

class TutorialManager:
    """Tracks which tutorial steps have been shown this run."""

    ALL_STEPS = ("movement", "enemy", "container", "ammo", "medipack", "melee")

    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled
        self._seen: set[str] = set()

    def should_show(self, step: str) -> bool:
        """Return True (and mark as seen) if tutorial is on and step not yet shown."""
        if not self.enabled or step in self._seen:
            return False
        self._seen.add(step)
        return True

    def reset(self) -> None:
        """Reset for a new run."""
        self._seen.clear()


# ---------------------------------------------------------------------------
# TutorialOverlay
# ---------------------------------------------------------------------------

class TutorialOverlay:
    """Centred blocking panel that shows one tutorial step at a time."""

    def __init__(self) -> None:
        self._font_title  = pygame.font.SysFont("consolas", 20, bold=True)
        self._font_body   = pygame.font.SysFont("consolas", 14)
        self._font_body_b = pygame.font.SysFont("consolas", 14, bold=True)
        self._font_hint   = pygame.font.SysFont("consolas", 13)
        self._font_close  = pygame.font.SysFont("consolas", 15, bold=True)
        self._step: str | None = None
        self._on_close: Callable | None = None
        self._panel_rect: pygame.Rect | None = None
        self._close_rect: pygame.Rect | None = None
        self._close_hovered = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show(self, step: str, on_close: Callable | None = None) -> None:
        self._step     = step
        self._on_close = on_close

    @property
    def is_active(self) -> bool:
        return self._step is not None

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._step is None:
            return
        close = False
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN,
                             pygame.K_KP_ENTER, pygame.K_ESCAPE):
                close = True
        elif event.type == pygame.MOUSEMOTION:
            self._close_hovered = bool(
                self._close_rect and self._close_rect.collidepoint(event.pos)
            )
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Close on X button click or click outside panel
            if self._close_rect and self._close_rect.collidepoint(event.pos):
                close = True
            elif self._panel_rect and not self._panel_rect.collidepoint(event.pos):
                close = True
        if close:
            cb = self._on_close
            self._step     = None
            self._on_close = None
            if cb:
                cb()

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface) -> None:
        if self._step is None:
            return
        sw, sh = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        ox = (sw - _W) // 2
        oy = (sh - _H) // 2

        # Dim backdrop
        dim = pygame.Surface((sw, sh), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        screen.blit(dim, (0, 0))

        # Panel
        panel = pygame.Surface((_W, _H), pygame.SRCALPHA)
        panel.fill(_BG)
        screen.blit(panel, (ox, oy))
        pygame.draw.rect(screen, _BORDER, (ox, oy, _W, _H), 2, border_radius=6)
        self._panel_rect = pygame.Rect(ox, oy, _W, _H)

        # Close button [x] — top-right corner
        close_size = 20
        self._close_rect = pygame.Rect(
            ox + _W - _PAD - close_size, oy + _PAD // 2,
            close_size, close_size,
        )
        if self._close_hovered:
            pygame.draw.rect(screen, (60, 30, 30), self._close_rect, border_radius=3)
            pygame.draw.rect(screen, (180, 60, 60), self._close_rect, 1, border_radius=3)
        x_surf = self._font_close.render(
            "x", True, (180, 60, 60) if self._close_hovered else _COL_HINT,
        )
        screen.blit(x_surf, (
            self._close_rect.centerx - x_surf.get_width() // 2,
            self._close_rect.centery - self._font_close.get_height() // 2 + 1,
        ))

        # Title
        title_surf = self._font_title.render(
            t(f"tutorial.{self._step}.title").upper(), True, _COL_TITLE
        )
        title_y = oy + _PAD
        screen.blit(title_surf, (ox + _PAD, title_y))
        sep_y = title_y + title_surf.get_height() + 4
        pygame.draw.line(screen, (30, 80, 70),
                         (ox + _PAD, sep_y), (ox + _W - _PAD, sep_y))

        content_y = sep_y + 10
        content_h = _H - (content_y - oy) - 34  # leave room for hint

        # Left column: wrapped body text
        left_w = _W - _PAD * 3 - _IMG_W
        body_text = t(f"tutorial.{self._step}.body")
        self._draw_wrapped(screen, body_text, ox + _PAD, content_y, left_w, content_h)

        # Right column: procedural illustration
        img_rect = pygame.Rect(ox + _W - _PAD - _IMG_W, content_y, _IMG_W, _IMG_H)
        _DRAW_FNS.get(self._step, _draw_placeholder)(screen, img_rect)

        # Bottom hint
        hint_surf = self._font_hint.render(t("tutorial.continue"), True, _COL_HINT)
        screen.blit(hint_surf, (
            ox + (_W - hint_surf.get_width()) // 2,
            oy + _H - hint_surf.get_height() - 8,
        ))

    def _draw_wrapped(self, screen: pygame.Surface, text: str,
                      x: int, y: int, w: int, max_h: int) -> None:
        """Render word-wrapped text.

        Lines starting with ">> " are rendered in amber bold (accent/warning).
        Newlines create paragraph breaks.
        """
        line_h = self._font_body.get_height() + 4
        cy = y
        for para in text.split("\n"):
            accent = para.startswith(">> ")
            raw    = para[3:] if accent else para
            font   = self._font_body_b if accent else self._font_body
            color  = _COL_ACCENT_LINE if accent else _COL_BODY
            words  = raw.split()
            line   = ""
            for word in words:
                test = (line + " " + word).strip()
                if font.size(test)[0] <= w:
                    line = test
                else:
                    if line:
                        screen.blit(font.render(line, True, color), (x, cy))
                        cy += line_h
                    line = word
                if cy > y + max_h:
                    return
            if line:
                screen.blit(font.render(line, True, color), (x, cy))
                cy += line_h
            cy += 3  # paragraph gap


# ---------------------------------------------------------------------------
# Procedural illustrations
# ---------------------------------------------------------------------------

def _draw_placeholder(screen: pygame.Surface, rect: pygame.Rect) -> None:
    pygame.draw.rect(screen, (20, 40, 35), rect, border_radius=4)


def _draw_movement(screen: pygame.Surface, rect: pygame.Rect) -> None:
    """WASD key cross (top) + elevator tile from tileset (bottom)."""
    pygame.draw.rect(screen, _COL_IMG, rect, border_radius=4)

    # --- WASD cross (upper portion) ---
    cx  = rect.centerx
    cy  = rect.top + 80
    ksz = 34
    step = ksz + 4
    font = pygame.font.SysFont("consolas", 13, bold=True)
    _KBG = (20, 50, 45)
    _BDR = (0, 200, 160)
    _TXT = (0, 240, 200)
    for lbl, ddx, ddy in (("W", 0, -1), ("A", -1, 0), ("S", 0, 0), ("D", 1, 0)):
        kx = cx + ddx * step - ksz // 2
        ky = cy + ddy * step - ksz // 2
        r  = pygame.Rect(kx, ky, ksz, ksz)
        pygame.draw.rect(screen, _KBG, r, border_radius=4)
        pygame.draw.rect(screen, _BDR, r, 2, border_radius=4)
        s = font.render(lbl, True, _TXT)
        screen.blit(s, (r.centerx - s.get_width() // 2,
                        r.centery - font.get_height() // 2 + 1))
    hint_font = pygame.font.SysFont("consolas", 11)
    h = hint_font.render(t("tutorial.img.arrow_keys"), True, (50, 100, 90))
    screen.blit(h, (rect.centerx - h.get_width() // 2, cy + step + 10))

    # --- Separator ---
    sep_y = cy + step + 28
    pygame.draw.line(screen, (25, 50, 45), (rect.left + 12, sep_y), (rect.right - 12, sep_y))

    # --- Elevator tile (bottom portion) ---
    elev_y = sep_y + 10
    ts = _get_tileset()
    scale = 3   # render at 3× (96×96 px)
    tile_px = 32 * scale
    tx = rect.centerx - tile_px // 2
    ty = elev_y

    if ts is not None:
        try:
            floor_surf = ts.get_tile_surface(_FLOOR_INDEX)
            ts.blit_tile(floor_surf, _ELEVATOR_CLOSED_INDEX, 0, 0)
            elev_big = pygame.transform.scale(floor_surf, (tile_px, tile_px))
            screen.blit(elev_big, (tx, ty))
        except Exception:
            ts = None  # fall through to procedural

    if ts is None:
        # Procedural fallback: teal square with down-arrow
        pygame.draw.rect(screen, (30, 80, 75), (tx, ty, tile_px, tile_px), border_radius=4)
        pygame.draw.rect(screen, (80, 200, 180), (tx, ty, tile_px, tile_px), 2, border_radius=4)
        fa = pygame.font.SysFont("consolas", 32, bold=True)
        arr = fa.render("v", True, (80, 200, 180))
        screen.blit(arr, (tx + tile_px // 2 - arr.get_width() // 2,
                          ty + tile_px // 2 - fa.get_height() // 2 + 1))

    # Label under the tile
    lbl_font = pygame.font.SysFont("consolas", 12, bold=True)
    lbl = lbl_font.render(t("tutorial.img.elevator"), True, (0, 200, 160))
    screen.blit(lbl, (rect.centerx - lbl.get_width() // 2, ty + tile_px + 6))


def _draw_enemy(screen: pygame.Surface, rect: pygame.Rect) -> None:
    """Aim arc: big arc = close target, small arc = far target. Needle in green zone."""
    pygame.draw.rect(screen, _COL_IMG, rect, border_radius=4)
    cx = rect.centerx
    cy = rect.centery + 10
    r  = 68

    # Arc background (grey spokes)
    for a_deg in range(45, 136):
        a  = math.radians(a_deg + 180)
        x1 = cx + math.cos(a) * (r - 7)
        y1 = cy + math.sin(a) * (r - 7)
        x2 = cx + math.cos(a) * (r + 7)
        y2 = cy + math.sin(a) * (r + 7)
        pygame.draw.line(screen, (40, 70, 65),
                         (round(x1), round(y1)), (round(x2), round(y2)), 2)
    # Green zone (centre 30° wide — "close" range example)
    for a_deg in range(75, 106):
        a  = math.radians(a_deg + 180)
        x1 = cx + math.cos(a) * (r - 7)
        y1 = cy + math.sin(a) * (r - 7)
        x2 = cx + math.cos(a) * (r + 7)
        y2 = cy + math.sin(a) * (r + 7)
        pygame.draw.line(screen, (0, 200, 80),
                         (round(x1), round(y1)), (round(x2), round(y2)), 3)
    # Needle pointing into green zone
    na = math.radians(91 + 180)
    nx = cx + math.cos(na) * (r - 14)
    ny = cy + math.sin(na) * (r - 14)
    pygame.draw.line(screen, (240, 200, 80), (cx, cy), (round(nx), round(ny)), 3)
    pygame.draw.circle(screen, (240, 200, 80), (cx, cy), 5)

    # [F] key label
    font = pygame.font.SysFont("consolas", 14, bold=True)
    k = font.render("[F]", True, (0, 240, 200))
    screen.blit(k, (cx - k.get_width() // 2, cy + 12))

    # Small "far" arc example — tiny green zone
    font_s = pygame.font.SysFont("consolas", 10)
    lbl_close = font_s.render(t("tutorial.img.close_zone"), True, (0, 160, 80))
    lbl_far   = font_s.render(t("tutorial.img.far_zone"), True, (160, 80, 80))
    screen.blit(lbl_close, (rect.centerx - lbl_close.get_width() // 2, cy + 32))
    screen.blit(lbl_far,   (rect.centerx - lbl_far.get_width()   // 2, cy + 46))


def _draw_container(screen: pygame.Surface, rect: pygame.Rect) -> None:
    """Mini hack grid: loot nodes (green), traps (red), timer bar, [Q] label prominently."""
    pygame.draw.rect(screen, _COL_IMG, rect, border_radius=4)

    # Timer bar at top
    bx = rect.left + 16
    by = rect.top  + 12
    bw = rect.width - 32
    font_s = pygame.font.SysFont("consolas", 11, bold=True)
    t_lbl  = font_s.render(t("tutorial.img.time"), True, (160, 120, 0))
    screen.blit(t_lbl, (bx, by - t_lbl.get_height() - 1))
    pygame.draw.rect(screen, (30, 60, 55), (bx, by, bw, 10), border_radius=3)
    pygame.draw.rect(screen, (200, 160, 0), (bx, by, round(bw * 0.45), 10),
                     border_radius=3)

    # 5×3 node grid
    cols, rows = 5, 3
    nr   = 8
    hgap, vgap = 32, 34
    gw   = (cols - 1) * hgap
    gx0  = rect.centerx - gw // 2
    gy0  = rect.top + 44
    GREEN = {(1, 0), (3, 1), (2, 2), (4, 0)}
    RED   = {(0, 2), (4, 1)}
    for row in range(rows):
        for col in range(cols):
            nx = gx0 + col * hgap
            ny = gy0 + row * vgap
            if (col, row) in GREEN:
                c = (0, 200, 80)
            elif (col, row) in RED:
                c = (200, 60, 60)
            elif col == 0 and row == 0:
                c = (0, 200, 180)  # start node
            else:
                c = (40, 70, 60)
            pygame.draw.circle(screen, c, (nx, ny), nr)
            pygame.draw.circle(screen, (0, 140, 110), (nx, ny), nr, 1)

    # [Q] label — large, amber, prominent
    font_q = pygame.font.SysFont("consolas", 14, bold=True)
    q = font_q.render(t("tutorial.img.escape"), True, (240, 180, 0))
    qy = rect.bottom - 28
    # amber background strip
    qbg = pygame.Surface((rect.width - 4, 20), pygame.SRCALPHA)
    qbg.fill((60, 40, 0, 120))
    screen.blit(qbg, (rect.left + 2, qy - 2))
    screen.blit(q, (rect.centerx - q.get_width() // 2, qy))


def _draw_ammo(screen: pygame.Surface, rect: pygame.Rect) -> None:
    """Weapon silhouette + ammo readout + C / R key labels."""
    pygame.draw.rect(screen, _COL_IMG, rect, border_radius=4)
    cx, cy = rect.centerx, rect.centery - 18
    _WC = (40, 80, 70)
    _WB = (0, 180, 140)
    body   = pygame.Rect(cx - 48, cy - 11, 68, 20)
    barrel = pygame.Rect(cx + 20, cy - 4,  28,  8)
    handle = pygame.Rect(cx - 18, cy +  9, 16, 22)
    for r in (body, barrel, handle):
        pygame.draw.rect(screen, _WC, r, border_radius=3)
    for r in (body, barrel):
        pygame.draw.rect(screen, _WB, r, 2, border_radius=3)
    font   = pygame.font.SysFont("consolas", 14, bold=True)
    ammo   = font.render("0 / 60", True, (220, 80, 80))   # show empty clip
    screen.blit(ammo, (cx - ammo.get_width() // 2, cy + 36))
    font_s = pygame.font.SysFont("consolas", 12, bold=True)
    lbl_c  = font_s.render(t("tutorial.img.switch_weapon"), True, (0, 200, 160))
    lbl_r  = font_s.render(t("tutorial.img.reload"),        True, (0, 200, 160))
    screen.blit(lbl_c, (cx - lbl_c.get_width() // 2, cy + 56))
    screen.blit(lbl_r, (cx - lbl_r.get_width() // 2, cy + 74))


def _draw_medipack(screen: pygame.Surface, rect: pygame.Rect) -> None:
    """EKG heartbeat waveform; third beat marked as player action point."""
    pygame.draw.rect(screen, _COL_IMG, rect, border_radius=4)
    cx, cy = rect.centerx, rect.centery - 12

    def _waveform(sx: int, base_y: int) -> tuple[list[tuple[int, int]], int]:
        pts: list[tuple[int, int]] = []
        x = sx
        for _ in range(10):               # flat lead-in
            pts.append((x, base_y)); x += 3
        pts += [(x, base_y), (x+4, base_y-12), (x+8, base_y)]  # du
        x += 12
        pts += [                          # DUM
            (x, base_y), (x+4, base_y+8), (x+6, base_y-28),
            (x+10, base_y+8), (x+14, base_y),
        ]
        x += 18
        for _ in range(6):               # flat tail
            pts.append((x, base_y)); x += 3
        return pts, x

    pts1, x1 = _waveform(rect.left + 8, cy)
    if len(pts1) >= 2:
        pygame.draw.lines(screen, (0, 160, 70), False, pts1, 2)
    pts2, x2 = _waveform(x1, cy)
    if len(pts2) >= 2:
        pygame.draw.lines(screen, (0, 180, 80), False, pts2, 2)

    # Third beat (du + DUM — player's action)
    du3   = [(x2, cy), (x2+4, cy-12), (x2+8, cy)]
    mark  = (x2+8+6, cy-28)           # top of the DUM spike
    dum3_before = [(x2+8, cy), (x2+12, cy+8), (x2+14, cy-28)]
    dum3_after  = [(x2+14, cy-28), (x2+18, cy+8), (x2+22, cy)]
    for pts in (du3, dum3_before, dum3_after):
        if len(pts) >= 2:
            pygame.draw.lines(screen, (0, 220, 100), False, pts, 2)
    # Highlight action beat
    pygame.draw.circle(screen, (240, 200, 80), mark, 5)
    pygame.draw.line(screen, (240, 200, 80),
                     (mark[0], cy - 36), (mark[0], cy + 14), 1)
    font = pygame.font.SysFont("consolas", 14, bold=True)
    h = font.render("[H]", True, (0, 240, 200))
    screen.blit(h, (rect.centerx - h.get_width() // 2, cy + 38))


# ---------------------------------------------------------------------------
# Melee illustration — oscillating power bar
# ---------------------------------------------------------------------------

def _draw_melee(screen: pygame.Surface, rect: pygame.Rect) -> None:
    """Draw a power-bar illustration for the melee tutorial."""
    pygame.draw.rect(screen, _COL_IMG, rect, border_radius=4)
    pygame.draw.rect(screen, (30, 80, 70), rect, 1, border_radius=4)

    cx = rect.centerx
    bar_w, bar_h = 170, 16
    bx = cx - bar_w // 2
    crit_start = 0.92
    font_s = pygame.font.SysFont("consolas", 11)

    # --- Timer bar ---
    timer_h = 4
    timer_by = rect.y + 36
    pygame.draw.rect(screen, (25, 35, 45), (bx, timer_by, bar_w, timer_h))
    pygame.draw.rect(screen, (100, 185, 165), (bx, timer_by, round(0.55 * bar_w), timer_h))
    t_lbl = font_s.render("1.6s", True, (100, 185, 165))
    screen.blit(t_lbl, (bx + bar_w + 3, timer_by - 1))

    # --- Power bar ---
    by = timer_by + timer_h + 5
    pygame.draw.rect(screen, (20, 25, 35), (bx, by, bar_w, bar_h))
    for i in range(bar_w):
        ratio = i / bar_w
        if ratio >= crit_start:
            c = (255, 240, 80)
        elif ratio >= 0.6:
            t_val = (ratio - 0.6) / (crit_start - 0.6)
            c = (
                round(210 + (40  - 210) * t_val),
                round(165 + (200 - 165) * t_val),
                round( 25 + ( 80 -  25) * t_val),
            )
        elif ratio >= 0.3:
            t_val = (ratio - 0.3) / 0.3
            c = (
                round(200 + (210 - 200) * t_val),
                round( 40 + (165 -  40) * t_val),
                round( 40 + ( 25 -  40) * t_val),
            )
        else:
            c = (200, 40, 40)
        pygame.draw.line(screen, c, (bx + i, by + 1), (bx + i, by + bar_h - 2))
    pygame.draw.rect(screen, (60, 100, 130), (bx, by, bar_w, bar_h), 1)

    # Example marker
    mx = bx + round(0.72 * bar_w)
    pygame.draw.line(screen, (240, 240, 255), (mx, by - 2), (mx, by + bar_h + 1), 2)

    # --- Zone labels ---
    crit_x = bx + round(crit_start * bar_w)
    for lbl, col, x in [
        ("WEAK", (200,  50,  50), bx),
        ("HIT",  (  0, 210,  80), bx + round(0.38 * bar_w)),
        ("CRIT", (255, 240,  80), crit_x - 2),
    ]:
        screen.blit(font_s.render(lbl, True, col), (x, by + bar_h + 3))

    # --- Key hint ---
    font_k = pygame.font.SysFont("consolas", 13, bold=True)
    key_lbl = font_k.render("[F] / LMB  hold & release", True, (0, 240, 200))
    screen.blit(key_lbl, (cx - key_lbl.get_width() // 2, by + bar_h + 22))


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

_DRAW_FNS: dict[str, Callable[[pygame.Surface, pygame.Rect], None]] = {
    "movement":  _draw_movement,
    "enemy":     _draw_enemy,
    "container": _draw_container,
    "ammo":      _draw_ammo,
    "medipack":  _draw_medipack,
    "melee":     _draw_melee,
}
