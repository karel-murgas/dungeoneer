"""Statistics overlay — shows lifetime stats for the active profile.

Tabbed panel with three tabs:
  COMBAT  — kills total, kills by enemy (top 7 + others), deaths total, deaths by enemy
  WEAPONS — kills by weapon, HP healed, bullets fired
  HISTORY — hacking & loot stats, runs won, credits earned

Opened from MainMenuScene's "Statistics" button; only available when a profile
is active.  All bucket keys are stable IDs (enemy_id / weapon Item.id) so the
display re-renders in the correct language whenever the language changes.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from dungeoneer.core import settings
from dungeoneer.core.i18n import t

if TYPE_CHECKING:
    from dungeoneer.meta.profile import LifetimeStats

# ---------------------------------------------------------------------------
# Visual constants (match main-menu / help-catalog palette)
# ---------------------------------------------------------------------------

_BG          = (8, 8, 20, 240)
_BORDER      = (60, 200, 160)
_COL_HDR     = (0, 220, 180)
_COL_SEC     = (80, 200, 170)
_COL_TXT     = (170, 185, 200)
_COL_DIM     = (70, 85, 95)
_COL_VAL     = (220, 255, 240)
_COL_EMPTY   = (80, 100, 95)

_TAB_SEL_BG  = (10, 70, 58)
_TAB_NRM_BG  = (18, 32, 28)
_TAB_HOV_BG  = (25, 55, 45)
_TAB_BORDER  = (50, 160, 130)
_TAB_SEL_BDR = (0, 220, 180)

_PAD     = 20
_MARGIN  = 30
_ROW_H   = 20   # height per stat row
_INDENT  = 24   # indentation for bucketed rows

# ---------------------------------------------------------------------------
# Tab definitions
# ---------------------------------------------------------------------------

_TAB_COMBAT  = 0
_TAB_WEAPONS = 1
_TAB_HISTORY = 2

_TAB_KEYS = [
    "stats.tab.combat",
    "stats.tab.weapons",
    "stats.tab.history",
]

_TOP_N_ENEMIES = 7   # show top N enemies before collapsing into "others"


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


class StatisticsOverlay:
    """Floating tabbed statistics panel for the main menu."""

    def __init__(self, scene) -> None:
        self._scene = scene

        self._font_title = pygame.font.SysFont("consolas", 18, bold=True)
        self._font_tab   = pygame.font.SysFont("consolas", 12, bold=True)
        self._font_sec   = pygame.font.SysFont("consolas", 13, bold=True)
        self._font_body  = pygame.font.SysFont("consolas", 13)
        self._font_val   = pygame.font.SysFont("consolas", 13, bold=True)
        self._font_foot  = pygame.font.SysFont("consolas", 12)

        self._tab_idx     = 0
        self._hov_tab: int | None = None
        self._tab_rects: list[pygame.Rect] = []
        self._panel_rect: pygame.Rect | None = None
        self._close_rect: pygame.Rect | None = None
        self._close_hov   = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def open(self) -> None:
        self._tab_idx = 0

    def handle_key(self, key: int) -> bool:
        """Return True to close."""
        if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER):
            return True
        if key in (pygame.K_LEFT, pygame.K_a):
            self._tab_idx = (self._tab_idx - 1) % len(_TAB_KEYS)
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self._tab_idx = (self._tab_idx + 1) % len(_TAB_KEYS)
        return False

    def handle_motion(self, pos: tuple) -> None:
        self._hov_tab   = self._tab_hit(pos)
        self._close_hov = bool(self._close_rect and self._close_rect.collidepoint(pos))

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

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface) -> None:
        sw, sh = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT

        pw = min(820, sw - _MARGIN * 2)
        ph = min(560, sh - _MARGIN * 2)
        ox = (sw - pw) // 2
        oy = (sh - ph) // 2

        # Background panel
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill(_BG)
        screen.blit(panel, (ox, oy))
        pygame.draw.rect(screen, _BORDER, (ox, oy, pw, ph), 2, border_radius=6)
        self._panel_rect = pygame.Rect(ox, oy, pw, ph)

        cy = oy + _PAD

        # Close button
        close_size = 20
        self._close_rect = pygame.Rect(ox + pw - _PAD - close_size, oy + _PAD // 2,
                                        close_size, close_size)
        if self._close_hov:
            pygame.draw.rect(screen, (60, 30, 30), self._close_rect, border_radius=3)
            pygame.draw.rect(screen, (180, 60, 60), self._close_rect, 1, border_radius=3)
        x_surf = self._font_tab.render("x", True,
                                        (180, 60, 60) if self._close_hov else _COL_DIM)
        screen.blit(x_surf, (self._close_rect.centerx - x_surf.get_width() // 2,
                               self._close_rect.centery - self._font_tab.get_height() // 2 + 1))

        # Title
        title = self._font_title.render(t("stats.title"), True, _COL_HDR)
        screen.blit(title, (ox + (pw - title.get_width()) // 2, cy))
        cy += title.get_height() + 8

        # Tab bar
        cy = self._draw_tabs(screen, ox, cy, pw)
        pygame.draw.line(screen, (30, 55, 50), (ox + _PAD, cy), (ox + pw - _PAD, cy))
        cy += 8

        # Content area
        content_bottom = oy + ph - self._font_foot.get_height() - 10
        stats = self._get_stats()
        if stats is None:
            # No active profile — shouldn't normally be shown, but handle gracefully
            empty = self._font_body.render(t("stats.empty"), True, _COL_EMPTY)
            screen.blit(empty, (ox + (pw - empty.get_width()) // 2,
                                 (cy + content_bottom) // 2))
        else:
            self._draw_content(screen, ox, cy, pw, content_bottom, stats)

        # Footer
        foot = self._font_foot.render(t("stats.footer"), True, _COL_DIM)
        screen.blit(foot, (ox + pw - foot.get_width() - _PAD, oy + ph - foot.get_height() - 6))

    # ------------------------------------------------------------------
    # Tabs
    # ------------------------------------------------------------------

    def _draw_tabs(self, screen: pygame.Surface, ox: int, cy: int, pw: int) -> int:
        tab_h   = self._font_tab.get_height() + 10
        tab_gap = 4
        widths  = [self._font_tab.size(t(k))[0] + 20 for k in _TAB_KEYS]
        total_w = sum(widths) + tab_gap * (len(widths) - 1)
        tx      = ox + (pw - total_w) // 2

        self._tab_rects = []
        for i, key in enumerate(_TAB_KEYS):
            rect = pygame.Rect(tx, cy, widths[i], tab_h)
            self._tab_rects.append(rect)

            sel = i == self._tab_idx
            hov = i == self._hov_tab and not sel
            if sel:
                bg, bdr, col = _TAB_SEL_BG, _TAB_SEL_BDR, _COL_HDR
            elif hov:
                bg, bdr, col = _TAB_HOV_BG, _TAB_BORDER, (200, 235, 220)
            else:
                bg, bdr, col = _TAB_NRM_BG, _TAB_BORDER, _COL_DIM

            pygame.draw.rect(screen, bg,  rect, border_radius=4)
            pygame.draw.rect(screen, bdr, rect, 1, border_radius=4)
            lbl = self._font_tab.render(t(key), True, col)
            bounds = lbl.get_bounding_rect()
            y = rect.bottom - 6 - bounds.bottom
            screen.blit(lbl, (rect.centerx - lbl.get_width() // 2, y))
            tx += widths[i] + tab_gap

        return cy + tab_h + 4

    # ------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------

    def _draw_content(self, screen: pygame.Surface, ox: int, cy: int,
                       pw: int, bottom: int, stats: "LifetimeStats") -> None:
        if self._tab_idx == _TAB_COMBAT:
            self._draw_combat_tab(screen, ox, cy, pw, bottom, stats)
        elif self._tab_idx == _TAB_WEAPONS:
            self._draw_weapons_tab(screen, ox, cy, pw, bottom, stats)
        else:
            self._draw_history_tab(screen, ox, cy, pw, bottom, stats)

    def _draw_combat_tab(self, screen: pygame.Surface, ox: int, cy: int,
                          pw: int, bottom: int, stats: "LifetimeStats") -> None:
        is_empty = (stats.kills_total == 0 and stats.deaths_total == 0)
        if is_empty:
            self._draw_empty(screen, ox, cy, bottom)
            return

        cy = self._draw_sec(screen, ox, cy, pw, t("stats.section.combat"))

        # kills total
        cy = self._draw_stat_row(screen, ox, cy, pw, bottom,
                                   t("stats.kills_total"), str(stats.kills_total))

        # kills by enemy
        if stats.kills_by_enemy:
            cy = self._draw_label_row(screen, ox, cy, pw, bottom,
                                       t("stats.kills_by_enemy") + ":")
            sorted_kills = sorted(stats.kills_by_enemy.items(), key=lambda x: x[1], reverse=True)
            top = sorted_kills[:_TOP_N_ENEMIES]
            rest = sorted_kills[_TOP_N_ENEMIES:]
            for enemy_id, count in top:
                name = t(f"entity.{enemy_id}.name")
                cy = self._draw_bucketed_row(screen, ox, cy, pw, bottom, name, str(count))
                if cy >= bottom:
                    return
            if rest:
                others_count = sum(c for _, c in rest)
                cy = self._draw_bucketed_row(screen, ox, cy, pw, bottom,
                                              t("stats.others"), str(others_count))

        cy += 6
        cy = self._draw_sep(screen, ox, cy, pw)
        cy += 6

        # deaths total
        cy = self._draw_stat_row(screen, ox, cy, pw, bottom,
                                   t("stats.deaths_total"), str(stats.deaths_total))

        # deaths by killer
        if stats.deaths_by_killer:
            cy = self._draw_label_row(screen, ox, cy, pw, bottom,
                                       t("stats.deaths_by_killer") + ":")
            for enemy_id, count in sorted(stats.deaths_by_killer.items(),
                                           key=lambda x: x[1], reverse=True):
                name = t(f"entity.{enemy_id}.name")
                cy = self._draw_bucketed_row(screen, ox, cy, pw, bottom, name, str(count))
                if cy >= bottom:
                    return

    def _draw_weapons_tab(self, screen: pygame.Surface, ox: int, cy: int,
                           pw: int, bottom: int, stats: "LifetimeStats") -> None:
        is_empty = (stats.kills_total == 0 and stats.hp_healed == 0 and stats.bullets_shot == 0)
        if is_empty:
            self._draw_empty(screen, ox, cy, bottom)
            return

        cy = self._draw_sec(screen, ox, cy, pw, t("stats.section.weapons"))

        if stats.kills_by_weapon:
            for weapon_id, count in sorted(stats.kills_by_weapon.items(),
                                            key=lambda x: x[1], reverse=True):
                name = t(f"item.{weapon_id}.name")
                value = t("stats.kills_count").format(n=count)
                cy = self._draw_stat_row(screen, ox, cy, pw, bottom, name, value)
                if cy >= bottom:
                    return
        else:
            cy = self._draw_label_row(screen, ox, cy, pw, bottom, "—")

        cy += 6
        cy = self._draw_sep(screen, ox, cy, pw)
        cy += 6

        cy = self._draw_sec(screen, ox, cy, pw, t("stats.section.resources"))
        cy = self._draw_stat_row(screen, ox, cy, pw, bottom,
                                   t("stats.hp_healed"), str(stats.hp_healed))
        cy = self._draw_stat_row(screen, ox, cy, pw, bottom,
                                   t("stats.bullets_shot"), str(stats.bullets_shot))

    def _draw_history_tab(self, screen: pygame.Surface, ox: int, cy: int,
                           pw: int, bottom: int, stats: "LifetimeStats") -> None:
        is_empty = (stats.containers_hacked == 0 and stats.runs_won == 0
                    and stats.credits_lifetime == 0)
        if is_empty:
            self._draw_empty(screen, ox, cy, bottom)
            return

        cy = self._draw_sec(screen, ox, cy, pw, t("stats.section.hacking"))
        cy = self._draw_stat_row(screen, ox, cy, pw, bottom,
                                   t("stats.containers_hacked"), str(stats.containers_hacked))
        cy = self._draw_stat_row(screen, ox, cy, pw, bottom,
                                   t("stats.containers_fully_hacked"), str(stats.containers_fully_hacked))
        cy = self._draw_stat_row(screen, ox, cy, pw, bottom,
                                   t("stats.containers_failed"), str(stats.containers_failed))
        cy = self._draw_stat_row(screen, ox, cy, pw, bottom,
                                   t("stats.nodes_hacked"), str(stats.nodes_hacked))

        cy += 6
        cy = self._draw_sep(screen, ox, cy, pw)
        cy += 6

        cy = self._draw_sec(screen, ox, cy, pw, t("stats.section.career"))
        cy = self._draw_stat_row(screen, ox, cy, pw, bottom,
                                   t("stats.runs_won"), str(stats.runs_won))
        cy = self._draw_stat_row(screen, ox, cy, pw, bottom,
                                   t("stats.credits_lifetime"), str(stats.credits_lifetime))

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _get_stats(self) -> "LifetimeStats | None":
        p = self._scene._active_profile
        return p.stats if p is not None else None

    def _draw_empty(self, screen: pygame.Surface, ox: int, cy: int, bottom: int) -> None:
        surf = self._font_body.render(t("stats.empty"), True, _COL_EMPTY)
        screen.blit(surf, (ox + _PAD, (cy + bottom) // 2 - surf.get_height() // 2))

    def _draw_sec(self, screen: pygame.Surface, ox: int, cy: int,
                   pw: int, label: str) -> int:
        surf = self._font_sec.render(label, True, _COL_SEC)
        screen.blit(surf, (ox + _PAD, cy))
        cy += surf.get_height() + 2
        pygame.draw.line(screen, (28, 50, 46), (ox + _PAD, cy), (ox + pw - _PAD, cy))
        return cy + 5

    def _draw_sep(self, screen: pygame.Surface, ox: int, cy: int, pw: int) -> int:
        pygame.draw.line(screen, (28, 40, 36), (ox + _PAD, cy), (ox + pw - _PAD, cy))
        return cy + 1

    def _draw_stat_row(self, screen: pygame.Surface, ox: int, cy: int,
                        pw: int, bottom: int, label: str, value: str) -> int:
        if cy >= bottom:
            return cy
        lbl_surf = self._font_body.render(label, True, _COL_TXT)
        val_surf = self._font_val.render(value, True, _COL_VAL)
        screen.blit(lbl_surf, (ox + _PAD, cy))
        screen.blit(val_surf, (ox + pw - _PAD - val_surf.get_width(), cy))
        return cy + _ROW_H

    def _draw_label_row(self, screen: pygame.Surface, ox: int, cy: int,
                         pw: int, bottom: int, label: str) -> int:
        if cy >= bottom:
            return cy
        surf = self._font_body.render(label, True, _COL_DIM)
        screen.blit(surf, (ox + _PAD, cy))
        return cy + _ROW_H

    def _draw_bucketed_row(self, screen: pygame.Surface, ox: int, cy: int,
                            pw: int, bottom: int, name: str, value: str) -> int:
        if cy >= bottom:
            return cy
        name_surf = self._font_body.render(name, True, _COL_TXT)
        val_surf  = self._font_val.render(value, True, _COL_VAL)
        screen.blit(name_surf, (ox + _PAD + _INDENT, cy))
        screen.blit(val_surf,  (ox + pw - _PAD - val_surf.get_width(), cy))
        return cy + _ROW_H

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _tab_hit(self, pos: tuple) -> int | None:
        for i, rect in enumerate(self._tab_rects):
            if rect.collidepoint(pos):
                return i
        return None
