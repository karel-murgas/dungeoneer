"""Help catalog overlay — opened from main menu help icon.

Tabbed reference guide covering all gameplay mechanics.  Navigate tabs with
◄ ► arrow keys or by clicking tab labels.  Close with Esc / Enter.

Tabs:  EXPLORATION | COMBAT | AIMING | MELEE | HEALING | HACKING | ITEMS

Each tab can have an illustration drawn at the top of the content area:
  - Exploration: sprite icons for container / ammo / elevator / vault
  - Aiming:      arc diagram with MISS / HIT / CRITICAL zones
  - Hacking:     node-type legend + loot icon examples

When adding a new mechanic with in-game help, add a matching entry here too
(see CLAUDE.md rule).
"""
from __future__ import annotations

import math
import os

import pygame

from dungeoneer.core import settings
from dungeoneer.core.i18n import t


# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------

_BG      = (8, 8, 20, 240)
_BORDER  = (60, 200, 160)
_COL_HDR = (0, 220, 180)
_COL_SEC = (80, 200, 170)
_COL_TXT = (170, 185, 200)
_COL_DIM = (70, 85, 95)
_TAB_SEL_BG  = (10, 70, 58)
_TAB_NRM_BG  = (18, 32, 28)
_TAB_HOV_BG  = (25, 55, 45)
_TAB_BORDER  = (50, 160, 130)
_TAB_SEL_BDR = (0, 220, 180)
_BULLET_COL  = (0, 180, 150)

# Illustration colours — aim arc
_ARC_MISS_FILL  = (22, 38, 55)
_ARC_MISS_RIM   = (38, 65, 90)
_ARC_HIT_FILL   = (0,  90, 40)
_ARC_HIT_RIM    = (0, 155, 60)
_ARC_CRIT_FILL  = (140, 120, 0)
_ARC_CRIT_RIM   = (220, 195, 0)
_ARC_NEEDLE     = (240, 240, 255)
_LABEL_MISS     = (180, 60,  60)
_LABEL_HIT      = (0,  210, 80)
_LABEL_CRIT     = (240, 210, 0)

# Illustration colours — hack nodes
_NODE_ENTRY  = (0,   190, 210)
_NODE_CACHE  = (0,   160,  60)
_NODE_EMPTY  = (38,   60,  76)
_NODE_ICE    = (200,  40,  40)
_NODE_BORDER = (55,   90, 110)

_PAD    = 20
_MARGIN = 30   # min gap between panel and screen edge

# ---------------------------------------------------------------------------
# Content definition
# ---------------------------------------------------------------------------
# Each tab: (tab_key, [ (section_header_key, [bullet_key, ...]), ... ])

_TABS: list[tuple[str, list[tuple[str, list[str]]]]] = [
    ("help_catalog.tab.exploration", [
        ("help_catalog.expl.h1", [
            "help_catalog.expl.1.1",
            "help_catalog.expl.1.2",
            "help_catalog.expl.1.3",
        ]),
        ("help_catalog.expl.h2", [
            "help_catalog.expl.2.1",
            "help_catalog.expl.2.2",
        ]),
        ("help_catalog.expl.h3", [
            "help_catalog.expl.3.1",
            "help_catalog.expl.3.2",
            "help_catalog.expl.3.3",
        ]),
        ("help_catalog.expl.h4", [
            "help_catalog.expl.4.1",
            "help_catalog.expl.4.2",
        ]),
        ("help_catalog.expl.h5", [
            "help_catalog.expl.5.1",
            "help_catalog.expl.5.2",
        ]),
    ]),
    ("help_catalog.tab.combat", [
        ("help_catalog.comb.intro", [
            "help_catalog.comb.intro.1",
            "help_catalog.comb.intro.2",
            "help_catalog.comb.intro.3",
            "help_catalog.comb.intro.4",
        ]),
        ("help_catalog.comb.h1", [
            "help_catalog.comb.1.1",
            "help_catalog.comb.1.2",
            "help_catalog.comb.1.3",
        ]),
        ("help_catalog.shoot.h1", [
            "help_catalog.shoot.1.1",
            "help_catalog.shoot.1.2",
            "help_catalog.shoot.1.3",
            "help_catalog.shoot.1.4",
        ]),
    ]),
    ("help_catalog.tab.aiming", [
        ("help_catalog.aim.h1", [
            "help_catalog.aim.1.1",
            "help_catalog.aim.1.2",
            "help_catalog.aim.1.3",
            "help_catalog.aim.1.4",
            "help_catalog.aim.1.5",
        ]),
        ("help_catalog.aim.h2", [
            "help_catalog.aim.2.1",
            "help_catalog.aim.2.2",
            "help_catalog.aim.2.3",
        ]),
        ("help_catalog.aim.h3", [
            "help_catalog.aim.3.1",
            "help_catalog.aim.3.2",
            "help_catalog.aim.3.3",
        ]),
    ]),
    ("help_catalog.tab.melee", [
        ("help_catalog.melee.h1", [
            "help_catalog.melee.1.1",
            "help_catalog.melee.1.2",
            "help_catalog.melee.1.3",
            "help_catalog.melee.1.4",
        ]),
        ("help_catalog.melee.h2", [
            "help_catalog.melee.2.1",
            "help_catalog.melee.2.2",
            "help_catalog.melee.2.3",
        ]),
        ("help_catalog.melee.h3", [
            "help_catalog.melee.3.1",
            "help_catalog.melee.3.2",
            "help_catalog.melee.3.3",
        ]),
    ]),
    ("help_catalog.tab.healing", [
        ("heal.help.h1", [
            "heal.help.1",
            "heal.help.2",
            "heal.help.3",
            "heal.help.4",
        ]),
        ("heal.help.h2", [
            "heal.help.s1",
            "heal.help.s2",
            "heal.help.s3",
        ]),
        ("heal.help.h3", [
            "heal.help.key1",
            "heal.help.key2",
            "heal.help.key3",
            "heal.help.key4",
        ]),
    ]),
    ("help_catalog.tab.hacking", [
        ("help_catalog.hack.h1", [
            "help_catalog.hack.1.1",
            "help_catalog.hack.1.2",
            "help_catalog.hack.1.3",
        ]),
        ("help_catalog.hack.h2", [
            "help_catalog.hack.2.1",
            "help_catalog.hack.2.2",
            "help_catalog.hack.2.3",
            "help_catalog.hack.2.4",
        ]),
        ("help_catalog.hack.h3", [
            "help_catalog.hack.3.1",
            "help_catalog.hack.3.2",
            "help_catalog.hack.3.3",
        ]),
        ("help_catalog.hack.h4", [
            "help_catalog.hack.4.1",
            "help_catalog.hack.4.2",
            "help_catalog.hack.4.3",
            "help_catalog.hack.4.4",
        ]),
    ]),
    ("help_catalog.tab.items", [
        ("help_catalog.items.h1", [
            "help_catalog.shoot.3.1",
            "help_catalog.shoot.3.2",
            "help_catalog.shoot.3.3",
            "help_catalog.shoot.3.4",
            "help_catalog.shoot.3.5",
            "help_catalog.shoot.3.6",
        ]),
        ("help_catalog.shoot.h2", [
            "help_catalog.shoot.2.1",
            "help_catalog.shoot.2.2",
            "help_catalog.shoot.2.3",
            "help_catalog.shoot.2.4",
        ]),
        ("help_catalog.comb.h2", [
            "help_catalog.comb.2.1",
            "help_catalog.comb.2.2",
            "help_catalog.comb.2.3",
            "help_catalog.comb.2.4",
        ]),
    ]),
]

_TAB_EXPLORATION = 0
_TAB_AIMING      = 2
_TAB_MELEE       = 3
_TAB_HEALING     = 4
_TAB_HACKING     = 5
_TAB_ITEMS       = 6


def _wrap(font: pygame.font.Font, text: str, max_w: int) -> list[str]:
    if font.size(text)[0] <= max_w:
        return [text]
    words = text.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        cand = (cur + " " + word).strip()
        if font.size(cand)[0] <= max_w:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines or [text]


def _arc_polygon(cx: int, cy: int, r_out: float, r_in: float,
                 a0: float, a1: float, steps: int = 16) -> list[tuple[int, int]]:
    """Return polygon points for a thick arc segment."""
    pts: list[tuple[int, int]] = []
    for i in range(steps + 1):
        a = a0 + (a1 - a0) * i / steps
        pts.append((round(cx + r_out * math.cos(a)), round(cy + r_out * math.sin(a))))
    for i in range(steps, -1, -1):
        a = a0 + (a1 - a0) * i / steps
        pts.append((round(cx + r_in * math.cos(a)), round(cy + r_in * math.sin(a))))
    return pts


class HelpCatalogOverlay:
    """Full-screen tabbed help catalog."""

    def __init__(self) -> None:
        self._font_title = pygame.font.SysFont("consolas", 18, bold=True)
        self._font_tab   = pygame.font.SysFont("consolas", 12, bold=True)
        self._font_sec   = pygame.font.SysFont("consolas", 13, bold=True)
        self._font_body  = pygame.font.SysFont("consolas", 13)
        self._font_foot  = pygame.font.SysFont("consolas", 12)
        self._font_ill   = pygame.font.SysFont("consolas", 11)   # illustration labels
        self._font_node  = pygame.font.SysFont("consolas", 11, bold=True)

        self._tab_idx   = 0
        self._hovered_tab: int | None = None
        self._tab_rects: list[pygame.Rect] = []
        # Fixed y-offset from tab bottom used for ALL labels — never varies with text.
        self._tab_text_bottom = self._font_tab.get_height() + 3
        self._elevator_tile: pygame.Surface | None = None   # lazy-loaded
        self._panel_rect: pygame.Rect | None = None
        self._close_rect: pygame.Rect | None = None
        self._close_hovered = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def open_tab(self, idx: int) -> None:
        """Open the overlay pre-selected on a specific tab index."""
        self._tab_idx = max(0, min(idx, len(_TABS) - 1))

    def handle_key(self, key: int) -> bool:
        """Return True to close."""
        if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER):
            return True
        if key in (pygame.K_LEFT, pygame.K_a):
            self._tab_idx = (self._tab_idx - 1) % len(_TABS)
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self._tab_idx = (self._tab_idx + 1) % len(_TABS)
        return False

    def handle_motion(self, pos: tuple) -> None:
        self._hovered_tab   = self._tab_hit(pos)
        self._close_hovered = bool(self._close_rect and self._close_rect.collidepoint(pos))

    def handle_click(self, pos: tuple) -> bool:
        """Return True to close."""
        if self._close_rect and self._close_rect.collidepoint(pos):
            return True
        if self._panel_rect and not self._panel_rect.collidepoint(pos):
            return True
        idx = self._tab_hit(pos)
        if idx is not None:
            self._tab_idx = idx
        return False

    def draw(self, screen: pygame.Surface) -> None:
        sw, sh = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT

        pw = min(820, sw - _MARGIN * 2)
        ph = min(560, sh - _MARGIN * 2)
        ox = (sw - pw) // 2
        oy = (sh - ph) // 2

        # Background
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill(_BG)
        screen.blit(panel, (ox, oy))
        pygame.draw.rect(screen, _BORDER, (ox, oy, pw, ph), 2, border_radius=6)
        self._panel_rect = pygame.Rect(ox, oy, pw, ph)

        cy = oy + _PAD

        # Close button ✕ — top-right corner
        close_size = 20
        self._close_rect = pygame.Rect(ox + pw - _PAD - close_size, oy + _PAD // 2, close_size, close_size)
        if self._close_hovered:
            pygame.draw.rect(screen, (60, 30, 30), self._close_rect, border_radius=3)
            pygame.draw.rect(screen, (180, 60, 60), self._close_rect, 1, border_radius=3)
        x_surf = self._font_tab.render("x", True, (180, 60, 60) if self._close_hovered else _COL_DIM)
        screen.blit(x_surf, (self._close_rect.centerx - x_surf.get_width() // 2,
                              self._close_rect.centery - self._font_tab.get_height() // 2 + 1))

        # Title
        title = self._font_title.render(t("help_catalog.title"), True, _COL_HDR)
        screen.blit(title, (ox + (pw - title.get_width()) // 2, cy))
        cy += title.get_height() + 8

        # Tabs
        cy = self._draw_tabs(screen, ox, cy, pw)
        pygame.draw.line(screen, (30, 55, 50),
                         (ox + _PAD, cy), (ox + pw - _PAD, cy))
        cy += 8

        # Content
        content_bottom = oy + ph - self._font_foot.get_height() - 10
        self._draw_content(screen, ox, cy, pw, content_bottom)

        # Footer
        foot = self._font_foot.render(t("help_catalog.footer"), True, _COL_DIM)
        screen.blit(foot,
                    (ox + (pw - foot.get_width()) // 2,
                     oy + ph - foot.get_height() - 6))

    # ------------------------------------------------------------------
    # Tabs
    # ------------------------------------------------------------------

    def _draw_tabs(self, screen: pygame.Surface, ox: int, cy: int, pw: int) -> int:
        tab_h   = self._font_tab.get_height() + 10
        tab_gap = 4
        widths  = [self._font_tab.size(t(tab_key))[0] + 20 for tab_key, _ in _TABS]
        total_w = sum(widths) + tab_gap * (len(widths) - 1)
        tx      = ox + (pw - total_w) // 2

        self._tab_rects = []
        for i, (tab_key, _) in enumerate(_TABS):
            rect = pygame.Rect(tx, cy, widths[i], tab_h)
            self._tab_rects.append(rect)

            selected = i == self._tab_idx
            hovered  = i == self._hovered_tab and not selected
            if selected:
                bg, bdr, col = _TAB_SEL_BG, _TAB_SEL_BDR, _COL_HDR
            elif hovered:
                bg, bdr, col = _TAB_HOV_BG, _TAB_BORDER, (200, 235, 220)
            else:
                bg, bdr, col = _TAB_NRM_BG, _TAB_BORDER, _COL_DIM

            pygame.draw.rect(screen, bg,  rect, border_radius=4)
            pygame.draw.rect(screen, bdr, rect, 1, border_radius=4)
            lbl = self._font_tab.render(t(tab_key), True, col)
            bounds = lbl.get_bounding_rect()
            y = rect.bottom - 6 - bounds.bottom
            screen.blit(lbl, (rect.centerx - lbl.get_width() // 2, y))
            tx += widths[i] + tab_gap

        return cy + tab_h + 4

    # ------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------

    def _draw_content(self, screen: pygame.Surface, ox: int, cy: int,
                       pw: int, bottom: int) -> None:
        # Draw illustration (tab-specific); advance cy by its height
        ill_h = self._draw_illustration(screen, ox, cy, pw, bottom)
        if ill_h:
            cy += ill_h + 6

        _, sections = _TABS[self._tab_idx]
        line_h   = self._font_body.get_height() + 2
        sec_gap  = 10
        bullet   = "\u2022 "
        indent   = _PAD + 14
        max_text_w = pw - indent - _PAD

        for sec_key, bullets in sections:
            if cy >= bottom:
                break

            sec_surf = self._font_sec.render(t(sec_key), True, _COL_SEC)
            screen.blit(sec_surf, (ox + _PAD, cy))
            cy += sec_surf.get_height() + 2
            pygame.draw.line(screen, (28, 50, 46),
                             (ox + _PAD, cy), (ox + pw - _PAD, cy))
            cy += 4

            for bkey in bullets:
                if cy >= bottom:
                    break
                text  = t(bkey)
                lines = _wrap(self._font_body, text, max_text_w)
                for i, line in enumerate(lines):
                    if cy >= bottom:
                        break
                    prefix   = bullet if i == 0 else "  "
                    pfx_surf = self._font_body.render(prefix, True, _BULLET_COL)
                    txt_surf = self._font_body.render(line,   True, _COL_TXT)
                    screen.blit(pfx_surf, (ox + _PAD,  cy))
                    screen.blit(txt_surf, (ox + indent, cy))
                    cy += line_h

            cy += sec_gap

    # ------------------------------------------------------------------
    # Illustration dispatcher
    # ------------------------------------------------------------------

    def _draw_illustration(self, screen: pygame.Surface, ox: int, cy: int,
                            pw: int, bottom: int) -> int:
        """Draw tab illustration.  Returns height consumed (0 = none)."""
        if self._tab_idx == _TAB_EXPLORATION:
            return self._draw_expl_illustration(screen, ox, cy, pw)
        if self._tab_idx == _TAB_AIMING:
            return self._draw_aim_illustration(screen, ox, cy, pw)
        if self._tab_idx == _TAB_HACKING:
            return self._draw_hack_illustration(screen, ox, cy, pw)
        if self._tab_idx == _TAB_MELEE:
            return self._draw_melee_illustration(screen, ox, cy, pw)
        if self._tab_idx == _TAB_HEALING:
            return self._draw_heal_illustration(screen, ox, cy, pw)
        return 0

    # ------------------------------------------------------------------
    # Exploration illustration — sprite icons row
    # ------------------------------------------------------------------

    def _get_elevator_tile(self) -> pygame.Surface:
        """Lazy-load and cache the closed elevator tile (floor + elevator blended)."""
        if self._elevator_tile is None:
            from dungeoneer.rendering.spritesheet import SpriteSheet
            path = os.path.join(
                os.path.dirname(__file__), "..", "..", "assets", "tiles", "dithart_scifi.png"
            )
            try:
                sheet = SpriteSheet(path, 32, 32)
                surf  = sheet.get_tile_surface(112)   # floor base
                sheet.blit_tile(surf, 36, 0, 0)       # closed elevator on top
                self._elevator_tile = surf
            except Exception:
                surf = pygame.Surface((32, 32), pygame.SRCALPHA)
                pygame.draw.rect(surf, (0, 180, 160), (0, 0, 32, 32))
                self._elevator_tile = surf
        return self._elevator_tile

    def _draw_expl_illustration(self, screen: pygame.Surface,
                                  ox: int, cy: int, pw: int) -> int:
        from dungeoneer.rendering import procedural_sprites

        items = [
            ("container_closed", t("help_catalog.expl.icon.container")),
            ("item_loot_ammo",   t("help_catalog.expl.icon.ammo")),
            ("elevator",         t("help_catalog.expl.icon.stairs")),
            ("vault_closed",     t("help_catalog.expl.icon.vault")),
        ]

        spr_size = 32
        lbl_h    = self._font_ill.get_height() + 3
        cell_w   = 90
        panel_h  = spr_size + lbl_h + 18

        panel_rect = pygame.Rect(ox + _PAD, cy, pw - _PAD * 2, panel_h)
        pygame.draw.rect(screen, (10, 14, 22), panel_rect, border_radius=4)
        pygame.draw.rect(screen, (28, 48, 44), panel_rect, 1, border_radius=4)

        total_w = len(items) * cell_w
        start_x = ox + (pw - total_w) // 2

        for i, (sprite_key, label) in enumerate(items):
            cell_cx = start_x + i * cell_w + cell_w // 2
            iy      = cy + 9

            if sprite_key == "elevator":
                spr = self._get_elevator_tile()
            else:
                spr = procedural_sprites.get(sprite_key)
            screen.blit(spr, (cell_cx - spr_size // 2, iy))

            lbl_surf = self._font_ill.render(label, True, _COL_TXT)
            screen.blit(lbl_surf,
                        (cell_cx - lbl_surf.get_width() // 2, iy + spr_size + 3))

        return panel_h

    # ------------------------------------------------------------------
    # Aiming illustration — arc with labelled zones
    # ------------------------------------------------------------------

    def _draw_aim_illustration(self, screen: pygame.Surface,
                                 ox: int, cy: int, pw: int) -> int:
        IH    = 138   # illustration height
        r_out = 78
        r_in  = 54
        STEPS = 18

        panel_rect = pygame.Rect(ox + _PAD, cy, pw - _PAD * 2, IH)
        pygame.draw.rect(screen, (8, 12, 22), panel_rect, border_radius=4)
        pygame.draw.rect(screen, (28, 48, 44), panel_rect, 1, border_radius=4)

        ax = ox + pw // 2
        ay = cy + IH - 8    # arc base sits near the bottom

        # Arc spans ±65° from straight up
        half_arc = math.radians(65)
        a0       = -math.pi / 2 - half_arc   # leftmost angle
        a1       = -math.pi / 2 + half_arc   # rightmost angle
        total    = a1 - a0

        # Zone boundaries (fraction of total arc)
        HIT_FRAC  = 0.24   # hit zone starts here on each side
        CRIT_FRAC = 0.43   # critical zone starts here

        def arc(fa: float, fb: float, steps: int = STEPS) -> list[tuple[int, int]]:
            return _arc_polygon(ax, ay, r_out, r_in, a0 + fa * total,
                                a0 + fb * total, steps)

        # 1. Full MISS background
        pygame.draw.polygon(screen, _ARC_MISS_FILL, arc(0.0, 1.0))
        pygame.draw.polygon(screen, _ARC_MISS_RIM,  arc(0.0, 1.0), 1)

        # 2. HIT zones (left and right of centre)
        for fs, fe in [(HIT_FRAC, CRIT_FRAC), (1.0 - CRIT_FRAC, 1.0 - HIT_FRAC)]:
            pygame.draw.polygon(screen, _ARC_HIT_FILL,  arc(fs, fe, steps=10))
            pygame.draw.polygon(screen, _ARC_HIT_RIM,   arc(fs, fe, steps=10), 1)

        # 3. CRITICAL zone (centre)
        pygame.draw.polygon(screen, _ARC_CRIT_FILL, arc(CRIT_FRAC, 1.0 - CRIT_FRAC, steps=8))
        pygame.draw.polygon(screen, _ARC_CRIT_RIM,  arc(CRIT_FRAC, 1.0 - CRIT_FRAC, steps=8), 1)

        # 4. Needle — in left hit zone
        needle_frac = HIT_FRAC + 0.07
        needle_a    = a0 + needle_frac * total
        nx = round(ax + r_out * math.cos(needle_a))
        ny = round(ay + r_out * math.sin(needle_a))
        pygame.draw.line(screen, _ARC_NEEDLE, (ax, ay), (nx, ny), 2)
        pygame.draw.circle(screen, _ARC_NEEDLE, (nx, ny), 4)
        pygame.draw.circle(screen, (80, 80, 120), (nx, ny), 3)

        # 5. Centre dot (arc pivot)
        pygame.draw.circle(screen, (55, 70, 90), (ax, ay), 4)
        pygame.draw.circle(screen, _ARC_MISS_RIM, (ax, ay), 4, 1)

        # 6. Labels outside the arc with small leader lines
        label_r = r_out + 14
        self._aim_label(screen, ax, ay, a0 + 0.10 * total, label_r,
                        t("aim.miss"), _LABEL_MISS)
        self._aim_label(screen, ax, ay, a0 + 0.33 * total, label_r,
                        t("aim.hit"),  _LABEL_HIT)
        self._aim_label(screen, ax, ay, a0 + 0.50 * total, label_r + 6,
                        t("aim.crit"), _LABEL_CRIT)
        self._aim_label(screen, ax, ay, a0 + 0.67 * total, label_r,
                        t("aim.hit"),  _LABEL_HIT)
        self._aim_label(screen, ax, ay, a0 + 0.90 * total, label_r,
                        t("aim.miss"), _LABEL_MISS)

        return IH

    def _aim_label(self, screen: pygame.Surface,
                    ax: int, ay: int, angle: float,
                    r: float, text: str, col: tuple) -> None:
        lx = round(ax + r * math.cos(angle))
        ly = round(ay + r * math.sin(angle))
        # Small leader dot at arc surface
        dot_x = round(ax + (r - 12) * math.cos(angle))
        dot_y = round(ay + (r - 12) * math.sin(angle))
        pygame.draw.circle(screen, col, (dot_x, dot_y), 2)
        surf = self._font_ill.render(text, True, col)
        screen.blit(surf, (lx - surf.get_width() // 2,
                            ly - self._font_ill.get_height() // 2 + 1))

    # ------------------------------------------------------------------
    # Hacking illustration — node legend + loot icon row
    # ------------------------------------------------------------------

    def _draw_hack_illustration(self, screen: pygame.Surface,
                                  ox: int, cy: int, pw: int) -> int:
        from dungeoneer.rendering import procedural_sprites

        NODE_SIZE = 34
        CELL_W    = 100
        SPR_SIZE  = 28
        LOOT_CELL = 72
        LBL_H     = self._font_ill.get_height() + 3

        nodes = [
            (_NODE_ENTRY, (0, 80, 100),  "\u25ba", t("help_catalog.hack.node.entry")),
            (_NODE_CACHE, (0, 55, 22),   "\u25aa", t("help_catalog.hack.node.cache")),
            (_NODE_EMPTY, (28, 45, 58),  "",       t("help_catalog.hack.node.empty")),
            (_NODE_ICE,   (80, 10, 10),  "?",      t("help_catalog.hack.node.ice")),
        ]
        loot_items = [
            ("item_hack_credits",    t("hack.loot.credits")),
            ("item_loot_ammo",       t("hack.loot.ammo")),
            ("item_loot_consumable", t("hack.loot.heal")),
            ("item_hack_bonus_time", t("hack.loot.bonus_time")),
            ("item_loot_armor",      t("hack.loot.armor")),
            ("item_hack_mystery",    t("hack.loot.mystery")),
        ]

        # Panel height = nodes row + gap + loot row + padding
        row1_h = NODE_SIZE + LBL_H + 4
        row2_h = SPR_SIZE + LBL_H + 4
        panel_h = row1_h + 10 + row2_h + 18

        panel_rect = pygame.Rect(ox + _PAD, cy, pw - _PAD * 2, panel_h)
        pygame.draw.rect(screen, (8, 12, 22), panel_rect, border_radius=4)
        pygame.draw.rect(screen, (28, 48, 44), panel_rect, 1, border_radius=4)

        # --- Row 1: node types ---
        total_nodes_w = len(nodes) * CELL_W
        node_start_x  = ox + (pw - total_nodes_w) // 2
        node_y        = cy + 9

        for i, (fill, dark, icon, label) in enumerate(nodes):
            cell_cx = node_start_x + i * CELL_W + CELL_W // 2
            nx = cell_cx - NODE_SIZE // 2
            ny = node_y

            # Node box
            pygame.draw.rect(screen, dark,    (nx, ny, NODE_SIZE, NODE_SIZE), border_radius=3)
            pygame.draw.rect(screen, fill,    (nx, ny, NODE_SIZE, NODE_SIZE), 2, border_radius=3)

            # Icon inside node
            if icon:
                ic = self._font_node.render(icon, True, fill)
                screen.blit(ic, (cell_cx - ic.get_width() // 2,
                                  ny + NODE_SIZE // 2 - self._font_node.get_height() // 2 + 1))

            # Label below node
            lbl = self._font_ill.render(label, True, _COL_TXT)
            screen.blit(lbl, (cell_cx - lbl.get_width() // 2,
                               node_y + NODE_SIZE + 3))

        # Separator + "Loot examples:" label
        sep_y = node_y + NODE_SIZE + LBL_H + 8
        pygame.draw.line(screen, (25, 45, 40),
                         (ox + _PAD + 8, sep_y), (ox + pw - _PAD - 8, sep_y))
        loot_label_surf = self._font_ill.render(t("help_catalog.hack.loot_label"),
                                                 True, _COL_DIM)
        screen.blit(loot_label_surf, (ox + _PAD + 10, sep_y + 3))

        # --- Row 2: loot examples ---
        total_loot_w  = len(loot_items) * LOOT_CELL
        loot_start_x  = ox + (pw - total_loot_w) // 2
        loot_y        = sep_y + loot_label_surf.get_height() + 5

        for i, (sprite_key, label) in enumerate(loot_items):
            cell_cx = loot_start_x + i * LOOT_CELL + LOOT_CELL // 2

            # Scale sprite to SPR_SIZE
            spr     = procedural_sprites.get(sprite_key)
            scaled  = pygame.transform.smoothscale(spr, (SPR_SIZE, SPR_SIZE))
            screen.blit(scaled, (cell_cx - SPR_SIZE // 2, loot_y))

            lbl_surf = self._font_ill.render(label, True, _COL_TXT)
            screen.blit(lbl_surf,
                        (cell_cx - lbl_surf.get_width() // 2,
                         loot_y + SPR_SIZE + 2))

        return panel_h

    # ------------------------------------------------------------------
    # Healing illustration — EKG heartbeat waveform
    # ------------------------------------------------------------------

    def _draw_heal_illustration(self, screen: pygame.Surface,
                                  ox: int, cy: int, pw: int) -> int:
        IH = 90
        panel_rect = pygame.Rect(ox + _PAD, cy, pw - _PAD * 2, IH)
        pygame.draw.rect(screen, (8, 12, 22), panel_rect, border_radius=4)
        pygame.draw.rect(screen, (28, 48, 44), panel_rect, 1, border_radius=4)

        base_y = cy + IH // 2 + 4
        font_s = self._font_ill

        def _waveform(sx: int) -> tuple[list[tuple[int, int]], int]:
            pts: list[tuple[int, int]] = []
            x = sx
            for _ in range(8):
                pts.append((x, base_y)); x += 3
            pts += [(x, base_y), (x+3, base_y-9), (x+6, base_y)]   # du
            x += 9
            pts += [
                (x, base_y), (x+3, base_y+6), (x+5, base_y-22),
                (x+8, base_y+6), (x+11, base_y),
            ]
            x += 14
            for _ in range(4):
                pts.append((x, base_y)); x += 3
            return pts, x

        pts1, x1 = _waveform(ox + _PAD + 10)
        if len(pts1) >= 2:
            pygame.draw.lines(screen, (0, 130, 60), False, pts1, 2)
        pts2, x2 = _waveform(x1)
        if len(pts2) >= 2:
            pygame.draw.lines(screen, (0, 160, 70), False, pts2, 2)

        # Third beat — highlighted, player presses H here
        du3  = [(x2, base_y), (x2+3, base_y-9), (x2+6, base_y)]
        dum3_b = [(x2+6, base_y), (x2+9, base_y+6), (x2+11, base_y-22)]
        mark   = (x2+11, base_y-22)
        dum3_a = [(x2+11, base_y-22), (x2+14, base_y+6), (x2+17, base_y)]
        for pts in (du3, dum3_b, dum3_a):
            if len(pts) >= 2:
                pygame.draw.lines(screen, (0, 210, 90), False, pts, 2)
        pygame.draw.circle(screen, (240, 200, 80), mark, 5)
        pygame.draw.line(screen, (240, 200, 80),
                         (mark[0], base_y - 30), (mark[0], base_y + 12), 1)

        # [H] label below the spike
        h_surf = self._font_sec.render("[H]", True, (0, 220, 180))
        screen.blit(h_surf, (mark[0] - h_surf.get_width() // 2, base_y + 14))

        # Beat labels: "1" "2" "3"
        for i, bx in enumerate([ox + _PAD + 30, x1 + 20, x2 + 20]):
            lbl = font_s.render(str(i + 1), True, _COL_DIM)
            screen.blit(lbl, (bx, cy + 6))

        return IH

    # ------------------------------------------------------------------
    # Melee illustration — power bar with zones
    # ------------------------------------------------------------------

    def _draw_melee_illustration(self, screen: pygame.Surface,
                                  ox: int, cy: int, pw: int) -> int:
        IH = 86
        panel_rect = pygame.Rect(ox + _PAD, cy, pw - _PAD * 2, IH)
        pygame.draw.rect(screen, (8, 12, 22), panel_rect, border_radius=4)
        pygame.draw.rect(screen, (28, 48, 44), panel_rect, 1, border_radius=4)

        bar_w = pw - _PAD * 4 - 40
        bar_h = 16
        bx = ox + _PAD + 20
        by = cy + 32   # leave room for timer bar above

        # --- Timer bar (thin strip above power bar) ---
        timer_h = 5
        timer_by = by - timer_h - 5
        pygame.draw.rect(screen, (25, 35, 45), (bx, timer_by, bar_w, timer_h))
        # Show ~60% remaining as example
        pygame.draw.rect(screen, (100, 185, 165), (bx, timer_by, round(0.60 * bar_w), timer_h))
        font_s = self._font_ill
        t_lbl = font_s.render("1.8s", True, (100, 185, 165))
        screen.blit(t_lbl, (bx + bar_w + 4, timer_by - 1))

        # --- Bar background ---
        pygame.draw.rect(screen, (20, 25, 35), (bx, by, bar_w, bar_h))

        # --- Color gradient fill (full bar showing all zones) ---
        crit_start = 0.92
        for i in range(bar_w):
            ratio = i / bar_w
            if ratio >= crit_start:
                c = (255, 240, 80)    # bright vivid yellow — critical
            elif ratio >= 0.6:
                t_val = (ratio - 0.6) / (crit_start - 0.6)
                c = (
                    round(210 + (40 - 210) * t_val),
                    round(165 + (200 - 165) * t_val),
                    round(25  + (80  -  25) * t_val),
                )
            elif ratio >= 0.3:
                t_val = (ratio - 0.3) / 0.3
                c = (
                    round(200 + (210 - 200) * t_val),
                    round( 40 + (165 -  40) * t_val),
                    round( 40 + ( 25 -  40) * t_val),
                )
            else:
                c = (200, 40, 40)     # deep red — weak
            pygame.draw.line(screen, c, (bx + i, by + 1), (bx + i, by + bar_h - 2))

        # --- Crit zone border highlight ---
        crit_x = bx + round(crit_start * bar_w)
        pygame.draw.rect(screen, (60, 100, 130), (bx, by, bar_w, bar_h), 1)

        # --- Zone labels below bar ---
        label_y = by + bar_h + 3
        for lbl, col, x in [
            ("WEAK",  (200,  50,  50), bx + 2),
            ("HIT",   (  0, 210,  80), bx + round(0.38 * bar_w)),
            ("CRIT",  (255, 240,  80), crit_x - 2),
        ]:
            s = font_s.render(lbl, True, col)
            screen.blit(s, (x, label_y))

        # --- Example marker (strong hit, not crit) ---
        mx = bx + round(0.74 * bar_w)
        pygame.draw.line(screen, (240, 240, 255), (mx, by - 3), (mx, by + bar_h + 2), 2)

        return IH

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _tab_hit(self, pos: tuple) -> int | None:
        for i, rect in enumerate(self._tab_rects):
            if rect.collidepoint(pos):
                return i
        return None
