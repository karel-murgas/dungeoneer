"""Settings overlay — opened from main menu gear icon.

Shows all gameplay options (moved from main menu), language, and audio volume
controls.  Closes on Esc / Enter.  Mutates settings.py audio globals directly
and writes back to the MainMenuScene instance for gameplay options.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from dungeoneer.core import settings
from dungeoneer.core.difficulty import EASY, NORMAL, HARD
from dungeoneer.core.i18n import t, set_language

if TYPE_CHECKING:
    from dungeoneer.scenes.main_menu_scene import MainMenuScene

# ---------------------------------------------------------------------------
# Visual constants (reuse main-menu palette)
# ---------------------------------------------------------------------------

_BG           = (8, 8, 20, 235)
_BORDER       = (60, 200, 160)
_COL_ACCENT   = (0, 220, 180)
_COL_SEC      = (60, 160, 140)
_COL_LBL      = (120, 150, 140)

_BTN_NRM       = (20, 40, 35)
_BTN_SEL       = (10, 80, 65)
_BTN_HOV       = (35, 90, 70)
_COL_BORDER_NRM   = (60, 200, 160)
_COL_BORDER_SEL   = (0, 240, 200)
_COL_BORDER_HOV   = (100, 240, 200)
_COL_BTN_NRM   = (140, 180, 160)
_COL_BTN_SEL   = (220, 255, 240)
_COL_BTN_HOV   = (200, 240, 220)

_W        = 580   # panel width
_PAD      = 22
_BTN_H    = 30
_BTN_W_SM = 76
_BTN_W_MD = 110
_ROW_H    = 36    # height of a labeled toggle row
_LBL_W    = 96    # width of the row label column
_VOL_STEP = 0.1


class SettingsOverlay:
    """Floating settings panel for the main menu."""

    def __init__(self, scene: "MainMenuScene") -> None:
        self._scene = scene
        self._font_title = pygame.font.SysFont("consolas", 19, bold=True)
        self._font_sec   = pygame.font.SysFont("consolas", 12, bold=True)
        self._font_lbl   = pygame.font.SysFont("consolas", 13, bold=True)
        self._font_btn   = pygame.font.SysFont("consolas", 12, bold=True)
        self._font_vol   = pygame.font.SysFont("consolas", 13)
        self._font_foot  = pygame.font.SysFont("consolas", 12)

        self._hovered: str | None = None
        self._btn_rects: dict[str, pygame.Rect] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def handle_key(self, key: int) -> bool:
        """Return True to close overlay."""
        return key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER)

    def handle_motion(self, pos: tuple) -> None:
        self._hovered = self._hit_test(pos)

    def handle_click(self, pos: tuple) -> bool:
        """Return True to close overlay."""
        hit = self._hit_test(pos)
        if hit is None:
            return False
        self._dispatch(hit)
        return hit == "close"

    def draw(self, screen: pygame.Surface) -> None:
        sw, sh = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        s = self._scene
        self._btn_rects = {}

        # --- Compute panel height ---
        # title + sep + DIFFICULTY(sec+row) + sep + GAMEPLAY(sec+3rows) +
        # sep + LANGUAGE(sec+row) + sep + AUDIO(sec+3rows) + footer + pads
        sec_h  = self._font_sec.get_height() + 4
        rows_diff = 1
        rows_game = 2 if not s._use_minigame else 3
        rows_lang = 1
        rows_audio = 3
        inner_h = (
            30 + 8           # title + gap
            + sec_h + rows_diff * _ROW_H + 10   # DIFFICULTY
            + 1 + 8          # separator
            + sec_h + rows_game * _ROW_H + 10   # GAMEPLAY
            + 1 + 8          # separator
            + sec_h + rows_lang * _ROW_H + 10   # LANGUAGE
            + 1 + 8          # separator
            + sec_h + rows_audio * _ROW_H + 8   # AUDIO
            + 22             # footer
        )
        ph = inner_h + _PAD * 2
        pw = _W
        ox = (sw - pw) // 2
        oy = (sh - ph) // 2

        # Background
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill(_BG)
        screen.blit(panel, (ox, oy))
        pygame.draw.rect(screen, _BORDER, (ox, oy, pw, ph), 2, border_radius=6)

        cy = oy + _PAD

        # Title
        title = self._font_title.render(t("settings.title"), True, _COL_ACCENT)
        screen.blit(title, (ox + (pw - title.get_width()) // 2, cy))
        cy += title.get_height() + 6
        self._draw_sep(screen, ox, cy, pw)
        cy += 10

        # --- DIFFICULTY ---
        cy = self._draw_section_label(screen, ox, cy, pw, t("settings.section.difficulty"))
        self._draw_labeled_row(screen, ox, cy, pw, "",
            [("easy",   t("menu.easy"),   s._difficulty is EASY),
             ("normal", t("menu.normal"), s._difficulty is NORMAL),
             ("hard",   t("menu.hard"),   s._difficulty is HARD)],
            btn_w=_BTN_W_SM)
        cy += _ROW_H + 8
        self._draw_sep(screen, ox, cy, pw)
        cy += 10

        # --- GAMEPLAY ---
        cy = self._draw_section_label(screen, ox, cy, pw, t("settings.section.gameplay"))
        self._draw_labeled_row(screen, ox, cy, pw, t("settings.gameplay.loot"),
            [("minigame", t("menu.loot.minigame"), s._use_minigame),
             ("random",   t("menu.loot.random"),   not s._use_minigame)],
            btn_w=_BTN_W_MD)
        cy += _ROW_H
        if s._use_minigame:
            self._draw_labeled_row(screen, ox, cy, pw, t("settings.gameplay.hack"),
                [("grid",    t("menu.hack.grid"),    s._hack_variant == "grid"),
                 ("classic", t("menu.hack.classic"), s._hack_variant == "classic")],
                btn_w=_BTN_W_MD)
            cy += _ROW_H
        self._draw_labeled_row(screen, ox, cy, pw, t("settings.gameplay.aim"),
            [("aim_on",  t("menu.aim_minigame_on"),  s._use_aim_minigame),
             ("aim_off", t("menu.aim_minigame_off"), not s._use_aim_minigame)],
            btn_w=_BTN_W_SM)
        cy += _ROW_H + 8
        self._draw_sep(screen, ox, cy, pw)
        cy += 10

        # --- LANGUAGE ---
        cy = self._draw_section_label(screen, ox, cy, pw, t("settings.section.language"))
        self._draw_labeled_row(screen, ox, cy, pw, "",
            [("en", "English", s._language == "en"),
             ("cs", "Česky",   s._language == "cs"),
             ("es", "Español", s._language == "es")],
            btn_w=_BTN_W_MD)
        cy += _ROW_H + 8
        self._draw_sep(screen, ox, cy, pw)
        cy += 10

        # --- AUDIO ---
        cy = self._draw_section_label(screen, ox, cy, pw, t("settings.section.audio"))
        cy = self._draw_volume_row(screen, ox, cy, pw, t("settings.audio.master"),
                                   "master", settings.MASTER_VOLUME)
        cy = self._draw_volume_row(screen, ox, cy, pw, t("settings.audio.music"),
                                   "music", settings.MUSIC_VOLUME)
        cy = self._draw_volume_row(screen, ox, cy, pw, t("settings.audio.sfx"),
                                   "sfx", settings.SFX_VOLUME)
        cy += 4

        # Footer
        foot = self._font_foot.render(t("settings.footer"), True, _COL_LBL)
        screen.blit(foot, (ox + pw - foot.get_width() - _PAD, cy))

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _draw_sep(self, screen: pygame.Surface, ox: int, cy: int, pw: int) -> None:
        pygame.draw.line(screen, (30, 55, 50),
                         (ox + _PAD, cy), (ox + pw - _PAD, cy))

    def _draw_section_label(self, screen: pygame.Surface, ox: int, cy: int,
                             pw: int, text: str) -> int:
        surf = self._font_sec.render(text, True, _COL_SEC)
        screen.blit(surf, (ox + _PAD, cy))
        return cy + surf.get_height() + 4

    def _draw_labeled_row(self, screen: pygame.Surface, ox: int, cy: int, pw: int,
                           label: str, buttons: list, btn_w: int) -> None:
        """Draw an optional text label then a row of toggle buttons."""
        bx = ox + _PAD
        by = cy + (_ROW_H - _BTN_H) // 2

        if label:
            lbl_surf = self._font_lbl.render(label, True, _COL_LBL)
            screen.blit(lbl_surf, (bx, by + (_BTN_H - lbl_surf.get_height()) // 2))
            bx += _LBL_W + 8

        gap = 8
        for key, text, selected in buttons:
            rect = pygame.Rect(bx, by, btn_w, _BTN_H)
            hov  = self._hovered == key
            if selected:
                bg, border, col = _BTN_SEL, _COL_BORDER_SEL, _COL_BTN_SEL
            elif hov:
                bg, border, col = _BTN_HOV, _COL_BORDER_HOV, _COL_BTN_HOV
            else:
                bg, border, col = _BTN_NRM, _COL_BORDER_NRM, _COL_BTN_NRM
            pygame.draw.rect(screen, bg, rect, border_radius=4)
            pygame.draw.rect(screen, border, rect, 2, border_radius=4)
            lbl = self._font_btn.render(text, True, col)
            screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                               rect.centery - lbl.get_height() // 2))
            self._btn_rects[key] = rect
            bx += btn_w + gap

    def _draw_volume_row(self, screen: pygame.Surface, ox: int, cy: int, pw: int,
                          label: str, key: str, value: float) -> int:
        """Draw a  Label  [◄]  pct%  [►]  row; register arrow button rects."""
        bx  = ox + _PAD
        by  = cy + (_ROW_H - _BTN_H) // 2

        lbl_surf = self._font_lbl.render(label, True, _COL_LBL)
        screen.blit(lbl_surf, (bx, by + (_BTN_H - lbl_surf.get_height()) // 2))
        bx += _LBL_W + 8

        arrow_w = 28
        val_w   = 52

        # [◄] button
        dn_rect = pygame.Rect(bx, by, arrow_w, _BTN_H)
        dn_key  = f"{key}_dn"
        hov_dn  = self._hovered == dn_key
        _bg  = _BTN_HOV if hov_dn else _BTN_NRM
        _brd = _COL_BORDER_HOV if hov_dn else _COL_BORDER_NRM
        pygame.draw.rect(screen, _bg,  dn_rect, border_radius=4)
        pygame.draw.rect(screen, _brd, dn_rect, 2, border_radius=4)
        arr = self._font_btn.render("\u25c4", True, _COL_BTN_NRM)
        screen.blit(arr, (dn_rect.centerx - arr.get_width() // 2,
                          dn_rect.centery - arr.get_height() // 2))
        self._btn_rects[dn_key] = dn_rect
        bx += arrow_w + 4

        # percentage value
        pct = f"{int(round(value * 100))}%"
        val_surf = self._font_vol.render(pct, True, _COL_BTN_SEL)
        screen.blit(val_surf, (bx + (val_w - val_surf.get_width()) // 2,
                                by + (_BTN_H - val_surf.get_height()) // 2))
        bx += val_w + 4

        # [►] button
        up_rect = pygame.Rect(bx, by, arrow_w, _BTN_H)
        up_key  = f"{key}_up"
        hov_up  = self._hovered == up_key
        _bg2  = _BTN_HOV if hov_up else _BTN_NRM
        _brd2 = _COL_BORDER_HOV if hov_up else _COL_BORDER_NRM
        pygame.draw.rect(screen, _bg2,  up_rect, border_radius=4)
        pygame.draw.rect(screen, _brd2, up_rect, 2, border_radius=4)
        arr2 = self._font_btn.render("\u25ba", True, _COL_BTN_NRM)
        screen.blit(arr2, (up_rect.centerx - arr2.get_width() // 2,
                           up_rect.centery - arr2.get_height() // 2))
        self._btn_rects[up_key] = up_rect

        return cy + _ROW_H

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _hit_test(self, pos: tuple) -> str | None:
        for key, rect in self._btn_rects.items():
            if rect.collidepoint(pos):
                return key
        return None

    def _dispatch(self, hit: str) -> None:
        s = self._scene
        if hit == "easy":        s._difficulty = EASY
        elif hit == "normal":    s._difficulty = NORMAL
        elif hit == "hard":      s._difficulty = HARD
        elif hit == "minigame":  s._use_minigame = True
        elif hit == "random":    s._use_minigame = False
        elif hit == "grid":      s._hack_variant = "grid"
        elif hit == "classic":   s._hack_variant = "classic"
        elif hit == "aim_on":    s._use_aim_minigame = True
        elif hit == "aim_off":   s._use_aim_minigame = False
        elif hit == "en":        s._set_language("en")
        elif hit == "cs":        s._set_language("cs")
        elif hit == "es":        s._set_language("es")
        elif hit == "master_dn": settings.MASTER_VOLUME = max(0.0, round(settings.MASTER_VOLUME - _VOL_STEP, 1)); self._apply_audio()
        elif hit == "master_up": settings.MASTER_VOLUME = min(1.0, round(settings.MASTER_VOLUME + _VOL_STEP, 1)); self._apply_audio()
        elif hit == "music_dn":  settings.MUSIC_VOLUME  = max(0.0, round(settings.MUSIC_VOLUME  - _VOL_STEP, 1)); self._apply_audio()
        elif hit == "music_up":  settings.MUSIC_VOLUME  = min(1.0, round(settings.MUSIC_VOLUME  + _VOL_STEP, 1)); self._apply_audio()
        elif hit == "sfx_dn":    settings.SFX_VOLUME    = max(0.0, round(settings.SFX_VOLUME    - _VOL_STEP, 1)); self._apply_audio()
        elif hit == "sfx_up":    settings.SFX_VOLUME    = min(1.0, round(settings.SFX_VOLUME    + _VOL_STEP, 1)); self._apply_audio()

    def _apply_audio(self) -> None:
        """Apply current volume settings to the running menu music."""
        pygame.mixer.music.set_volume(settings.MASTER_VOLUME * settings.MUSIC_VOLUME)
