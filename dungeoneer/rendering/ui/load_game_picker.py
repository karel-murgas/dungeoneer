"""Load Game Picker — scrollable profile list with delete support.

Each row shows: profile name | difficulty | last-played date | wins badge
An [x] icon per row opens a confirm dialog to delete that profile.

Callback: ``scene._load_game_done(profile_name)`` when a row is selected.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from dungeoneer.core import settings
from dungeoneer.core.i18n import t
from dungeoneer.meta.storage import list_profiles, load_profile, delete_profile

if TYPE_CHECKING:
    from dungeoneer.scenes.main_menu_scene import MainMenuScene

# ---------------------------------------------------------------------------
# Visual constants
# ---------------------------------------------------------------------------

_BG          = (8, 8, 20, 240)
_BORDER      = (60, 200, 160)
_COL_ACCENT  = (0, 220, 180)
_COL_SEC     = (60, 160, 140)
_COL_LBL     = (120, 150, 140)
_COL_NAME    = (200, 230, 220)
_COL_META    = (90, 115, 110)
_COL_WIN     = (80, 220, 120)

_ROW_NRM  = (18, 36, 30)
_ROW_HOV  = (30, 65, 52)
_ROW_BDR  = (50, 140, 110)
_ROW_BDR_H= (80, 200, 160)

_DEL_NRM  = (40, 20, 20)
_DEL_HOV  = (100, 30, 30)
_DEL_BDR  = (150, 40, 40)

_BTN_NRM  = (20, 40, 35)
_BTN_HOV  = (35, 90, 70)
_COL_BDR_NRM = (60, 200, 160)
_COL_BDR_HOV = (100, 240, 200)
_COL_BTN_NRM = (140, 180, 160)
_COL_BTN_HOV = (200, 240, 220)
_COL_BTN_SEL = (220, 255, 240)

_W       = 560
_ROW_H   = 52
_PAD     = 22
_DEL_W   = 26
_DEL_GAP = 6
_MAX_ROWS_VISIBLE = 7


class LoadGamePicker:
    """Scrollable profile list overlay."""

    def __init__(self, scene: "MainMenuScene") -> None:
        self._scene = scene
        self._profiles: list[str] = []      # display names
        self._scroll = 0                     # first visible row index
        self._hovered: str | None = None
        self._btn_rects: dict[str, pygame.Rect] = {}
        self._panel_rect: pygame.Rect | None = None

        # Delete confirm state
        self._delete_target: str | None = None   # profile name pending deletion
        self._delete_dialog = None               # lazy import to avoid circular

        self._font_title = pygame.font.SysFont("consolas", 19, bold=True)
        self._font_name  = pygame.font.SysFont("consolas", 15, bold=True)
        self._font_meta  = pygame.font.SysFont("consolas", 11)
        self._font_btn   = pygame.font.SysFont("consolas", 12, bold=True)
        self._font_empty = pygame.font.SysFont("consolas", 14)

    def refresh(self) -> None:
        """Reload profile list from disk."""
        self._profiles = list_profiles()
        self._scroll = 0
        self._delete_target = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def handle_key(self, key: int) -> bool:
        """Return True to close overlay."""
        if self._delete_target:
            if key in (pygame.K_y, pygame.K_RETURN, pygame.K_KP_ENTER):
                self._do_delete()
                return False
            if key in (pygame.K_n, pygame.K_ESCAPE):
                self._delete_target = None
            return False
        if key == pygame.K_ESCAPE:
            return True
        if key == pygame.K_UP:
            self._scroll = max(0, self._scroll - 1)
        elif key == pygame.K_DOWN:
            max_scroll = max(0, len(self._profiles) - _MAX_ROWS_VISIBLE)
            self._scroll = min(max_scroll, self._scroll + 1)
        return False

    def handle_motion(self, pos: tuple) -> None:
        self._hovered = self._hit_test(pos)

    def handle_click(self, pos: tuple) -> bool:
        """Return True to close overlay."""
        if self._panel_rect and not self._panel_rect.collidepoint(pos):
            return True
        if self._delete_target:
            hit = self._hit_test(pos)
            if hit == "del_yes":
                self._do_delete()
            elif hit == "del_no":
                self._delete_target = None
            return False
        hit = self._hit_test(pos)
        if hit is None:
            return False
        return self._dispatch(hit)

    def handle_scroll(self, dy: int) -> None:
        max_scroll = max(0, len(self._profiles) - _MAX_ROWS_VISIBLE)
        self._scroll = max(0, min(max_scroll, self._scroll - dy))

    def draw(self, screen: pygame.Surface) -> None:
        sw, sh = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        self._btn_rects = {}

        visible = min(len(self._profiles), _MAX_ROWS_VISIBLE)
        content_h = (
            _PAD
            + self._font_title.get_height() + 10
            + 1 + 10                               # sep
            + max(1, visible) * _ROW_H             # rows (at least 1 for empty state)
            + 12 + 1 + 12                          # bottom sep + close hint
            + self._font_btn.get_height()
            + _PAD
        )
        ph = content_h
        ox = (sw - _W) // 2
        oy = (sh - ph) // 2

        panel = pygame.Surface((_W, ph), pygame.SRCALPHA)
        panel.fill(_BG)
        screen.blit(panel, (ox, oy))
        pygame.draw.rect(screen, _BORDER, (ox, oy, _W, ph), 2, border_radius=6)
        self._panel_rect = pygame.Rect(ox, oy, _W, ph)

        cy = oy + _PAD

        # Title + close button
        title_surf = self._font_title.render(t("loadpicker.title"), True, _COL_ACCENT)
        screen.blit(title_surf, (ox + (_W - title_surf.get_width()) // 2, cy))

        close_w = 22
        close_rect = pygame.Rect(ox + _W - _PAD - close_w, cy, close_w, close_w)
        self._btn_rects["close"] = close_rect
        hov_close = self._hovered == "close"
        pygame.draw.rect(screen, (60, 30, 30) if hov_close else _BTN_NRM, close_rect, border_radius=3)
        pygame.draw.rect(screen, (180, 60, 60) if hov_close else _ROW_BDR, close_rect, 1, border_radius=3)
        x_s = self._font_btn.render("x", True, (200, 80, 80) if hov_close else _COL_LBL)
        screen.blit(x_s, (close_rect.centerx - x_s.get_width() // 2,
                          close_rect.centery - self._font_btn.get_height() // 2 + 1))

        cy += title_surf.get_height() + 8
        pygame.draw.line(screen, (30, 55, 50), (ox + _PAD, cy), (ox + _W - _PAD, cy))
        cy += 10

        # Delete confirm dialog (in-panel)
        if self._delete_target:
            cy = self._draw_delete_confirm(screen, ox, cy)
        elif not self._profiles:
            cy = self._draw_empty_state(screen, ox, cy, ph)
        else:
            cy = self._draw_rows(screen, ox, cy)

        # Bottom sep + hint
        cy_sep = oy + ph - _PAD - self._font_btn.get_height() - 14
        pygame.draw.line(screen, (30, 55, 50), (ox + _PAD, cy_sep), (ox + _W - _PAD, cy_sep))
        hint_surf = self._font_meta.render("[Esc] Close   [Up/Down] Scroll", True, _COL_LBL)
        screen.blit(hint_surf, (ox + (_W - hint_surf.get_width()) // 2,
                                cy_sep + 8))

    # ------------------------------------------------------------------
    # Sub-renders
    # ------------------------------------------------------------------

    def _draw_rows(self, screen: pygame.Surface, ox: int, cy: int) -> int:
        visible_names = self._profiles[self._scroll:self._scroll + _MAX_ROWS_VISIBLE]
        for i, name in enumerate(visible_names):
            idx = self._scroll + i
            ry = cy + i * _ROW_H
            row_rect = pygame.Rect(ox + _PAD, ry, _W - _PAD * 2 - _DEL_W - _DEL_GAP, _ROW_H - 4)
            del_rect  = pygame.Rect(ox + _W - _PAD - _DEL_W, ry + (_ROW_H - _DEL_W) // 2,
                                    _DEL_W, _DEL_W)

            row_key = f"row_{idx}"
            del_key = f"del_{idx}"
            self._btn_rects[row_key] = row_rect
            self._btn_rects[del_key] = del_rect

            hov_row = self._hovered == row_key
            hov_del = self._hovered == del_key

            # Row background
            pygame.draw.rect(screen, _ROW_HOV if hov_row else _ROW_NRM,
                             row_rect, border_radius=4)
            pygame.draw.rect(screen, _ROW_BDR_H if hov_row else _ROW_BDR,
                             row_rect, 1, border_radius=4)

            # Profile info
            profile = load_profile(name)
            diff_label = ""
            last_label = ""
            wins_label = ""
            if profile:
                diff_map = {"easy": t("menu.easy"), "normal": t("menu.normal"), "hard": t("menu.hard")}
                diff_label = diff_map.get(profile.difficulty, profile.difficulty)
                # Parse ISO date to short display
                try:
                    date_str = profile.updated_at[:10]
                except Exception:
                    date_str = "?"
                last_label = t("loadpicker.last_played").format(date=date_str)
                wins_label = t("loadpicker.runs_won").format(n=profile.stats.runs_won)

            name_surf = self._font_name.render(name, True,
                                               _COL_ACCENT if hov_row else _COL_NAME)
            screen.blit(name_surf, (row_rect.x + 10,
                                     row_rect.y + (row_rect.height - name_surf.get_height()) // 2 - 8))

            meta_str = f"{diff_label}   {last_label}   {wins_label}"
            meta_surf = self._font_meta.render(meta_str, True, _COL_META)
            screen.blit(meta_surf, (row_rect.x + 10,
                                     row_rect.y + (row_rect.height + meta_surf.get_height()) // 2 - 2))

            # Delete button [x]
            pygame.draw.rect(screen, _DEL_HOV if hov_del else _DEL_NRM, del_rect, border_radius=3)
            pygame.draw.rect(screen, _DEL_BDR, del_rect, 1, border_radius=3)
            x_s = self._font_meta.render("x", True, (200, 80, 80))
            screen.blit(x_s, (del_rect.centerx - x_s.get_width() // 2,
                               del_rect.centery - x_s.get_height() // 2 + 1))

        return cy + len(visible_names) * _ROW_H

    def _draw_empty_state(self, screen: pygame.Surface, ox: int, cy: int, ph: int) -> int:
        empty_surf = self._font_empty.render(t("loadpicker.empty"), True, _COL_LBL)
        ey = cy + (ph // 2 - cy - empty_surf.get_height()) // 2
        screen.blit(empty_surf, (ox + (_W - empty_surf.get_width()) // 2, ey))
        # CTA button
        cta_w = 200
        cta_rect = pygame.Rect(ox + (_W - cta_w) // 2, ey + empty_surf.get_height() + 16,
                               cta_w, 32)
        self._btn_rects["new_game"] = cta_rect
        hov = self._hovered == "new_game"
        pygame.draw.rect(screen, _BTN_HOV if hov else _BTN_NRM, cta_rect, border_radius=4)
        pygame.draw.rect(screen, _COL_BDR_HOV if hov else _COL_BDR_NRM, cta_rect, 2, border_radius=4)
        cta_s = self._font_btn.render(t("loadpicker.new_cta"), True,
                                      _COL_BTN_HOV if hov else _COL_BTN_NRM)
        screen.blit(cta_s, (cta_rect.centerx - cta_s.get_width() // 2,
                             cta_rect.centery - cta_s.get_height() // 2 + 1))
        return cy

    def _draw_delete_confirm(self, screen: pygame.Surface, ox: int, cy: int) -> int:
        q_surf = self._font_btn.render(
            t("profile.delete.question").replace(". ", ".\n"),
            True, (220, 200, 180),
        )
        screen.blit(q_surf, (ox + (_W - q_surf.get_width()) // 2, cy + 10))
        cy += q_surf.get_height() + 20

        btn_w = 140
        gap = 16
        total = btn_w * 2 + gap
        bx = ox + (_W - total) // 2

        yes_rect = pygame.Rect(bx, cy, btn_w, 32)
        no_rect  = pygame.Rect(bx + btn_w + gap, cy, btn_w, 32)
        self._btn_rects["del_yes"] = yes_rect
        self._btn_rects["del_no"]  = no_rect

        for rect, key, label, accent in (
            (yes_rect, "del_yes", t("profile.delete.yes"), True),
            (no_rect,  "del_no",  t("profile.delete.no"),  False),
        ):
            hov = self._hovered == key
            bg  = (80, 25, 25) if (hov and accent) else (_BTN_HOV if hov else _BTN_NRM)
            bdr = (200, 60, 60) if accent else _COL_BDR_NRM
            col = (220, 100, 100) if accent else _COL_BTN_NRM
            pygame.draw.rect(screen, bg, rect, border_radius=4)
            pygame.draw.rect(screen, bdr, rect, 2, border_radius=4)
            s = self._font_btn.render(label, True, col)
            screen.blit(s, (rect.centerx - s.get_width() // 2,
                            rect.centery - s.get_height() // 2 + 1))

        return cy + 40

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _hit_test(self, pos: tuple) -> str | None:
        for key, rect in self._btn_rects.items():
            if rect.collidepoint(pos):
                return key
        return None

    def _dispatch(self, hit: str) -> bool:
        """Return True to close picker."""
        if hit == "close":
            return True
        if hit == "new_game":
            self._scene._open_wizard()
            return True
        if hit.startswith("del_"):
            try:
                idx = int(hit[4:])
                self._delete_target = self._profiles[idx]
            except (ValueError, IndexError):
                pass
            return False
        if hit.startswith("row_"):
            try:
                idx = int(hit[4:])
                name = self._profiles[idx]
                self._scene._load_game_done(name)
                return True
            except (ValueError, IndexError):
                pass
        return False

    def _do_delete(self) -> None:
        if self._delete_target:
            delete_profile(self._delete_target)
            self._delete_target = None
            self.refresh()
