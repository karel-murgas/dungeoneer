"""Settings overlay — opened from main menu gear icon.

Gameplay minigames + language + audio.  Difficulty/tutorial/map_size have been
moved to the New Game Wizard and are no longer editable here.

Auto-save: any gameplay/language change is written back to the active profile
(if one is loaded) or to GlobalConfig.last_quick_config (Quick Game / no
profile).  Audio changes always update GlobalConfig.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from dungeoneer.core import settings
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

_W        = 540
_PAD      = 22
_BTN_H    = 30
_BTN_W_SM = 76
_BTN_W_MD = 110
_ROW_H    = 36
_HINT_H   = 16
_LBL_W    = 96
_VOL_STEP = 0.1
_THR_VALS = [80, 90, 100, 110, 120]


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
        self._panel_rect: pygame.Rect | None = None

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
        if self._panel_rect and not self._panel_rect.collidepoint(pos):
            return True
        hit = self._hit_test(pos)
        if hit is None:
            return False
        self._dispatch(hit)
        return hit == "close"

    def draw(self, screen: pygame.Surface) -> None:
        sw, sh = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        s = self._scene
        self._btn_rects = {}

        # Effective gameplay flags (from profile or quick config)
        flags = s._effective_flags()
        lang  = s._effective_language()

        # Compute panel height
        sec_h  = self._font_sec.get_height() + 4
        rows_game = 4   # loot + aim + heal + melee
        thr_extra = (_ROW_H + _HINT_H) if flags.use_heal_minigame else 0
        rows_lang = 1
        rows_audio = 3
        inner_h = (
            30 + 8           # title
            + 1 + 8          # sep (difficulty display line)
            + self._font_lbl.get_height() + 10    # read-only difficulty
            + 1 + 8
            + sec_h + rows_game * _ROW_H + thr_extra + 10
            + 1 + 8
            + sec_h + rows_lang * _ROW_H + 10
            + 1 + 8
            + sec_h + rows_audio * _ROW_H + 8
            + 22
        )
        ph = inner_h + _PAD * 2
        pw = _W
        ox = (sw - pw) // 2
        oy = (sh - ph) // 2

        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill(_BG)
        screen.blit(panel, (ox, oy))
        pygame.draw.rect(screen, _BORDER, (ox, oy, pw, ph), 2, border_radius=6)
        self._panel_rect = pygame.Rect(ox, oy, pw, ph)

        cy = oy + _PAD

        # Close button ✕
        close_size = 20
        close_rect = pygame.Rect(ox + pw - _PAD - close_size, oy + _PAD // 2, close_size, close_size)
        self._btn_rects["close"] = close_rect
        is_hov_close = self._hovered == "close"
        if is_hov_close:
            pygame.draw.rect(screen, (60, 30, 30), close_rect, border_radius=3)
            pygame.draw.rect(screen, (180, 60, 60), close_rect, 1, border_radius=3)
        x_surf = self._font_btn.render("x", True, (180, 60, 60) if is_hov_close else _COL_LBL)
        screen.blit(x_surf, (close_rect.centerx - x_surf.get_width() // 2,
                              close_rect.centery - self._font_btn.get_height() // 2 + 1))

        # Title
        title = self._font_title.render(t("settings.title"), True, _COL_ACCENT)
        screen.blit(title, (ox + (pw - title.get_width()) // 2, cy))
        cy += title.get_height() + 6
        self._draw_sep(screen, ox, cy, pw)
        cy += 10

        # --- Read-only difficulty ---
        diff_key = s._active_profile.difficulty if s._active_profile else None
        if diff_key:
            diff_map = {"easy": t("menu.easy"), "normal": t("menu.normal"), "hard": t("menu.hard")}
            diff_label = t("settings.difficulty.current").format(name=diff_map.get(diff_key, diff_key))
        else:
            diff_label = t("settings.difficulty.none")
        diff_surf = self._font_lbl.render(diff_label, True, _COL_LBL)
        screen.blit(diff_surf, (ox + _PAD, cy))
        cy += diff_surf.get_height() + 8
        self._draw_sep(screen, ox, cy, pw)
        cy += 10

        # --- GAMEPLAY ---
        cy = self._draw_section_label(screen, ox, cy, pw, t("settings.section.gameplay"))
        self._draw_labeled_row(screen, ox, cy, pw, t("settings.gameplay.loot"),
            [("minigame", t("menu.loot.minigame"), flags.use_minigame),
             ("random",   t("menu.loot.random"),   not flags.use_minigame)],
            btn_w=_BTN_W_MD)
        cy += _ROW_H
        self._draw_labeled_row(screen, ox, cy, pw, t("settings.gameplay.aim"),
            [("aim_on",  t("menu.aim_minigame_on"),  flags.use_aim_minigame),
             ("aim_off", t("menu.aim_minigame_off"), not flags.use_aim_minigame)],
            btn_w=_BTN_W_SM)
        cy += _ROW_H
        self._draw_labeled_row(screen, ox, cy, pw, t("settings.gameplay.heal"),
            [("heal_on",  t("menu.aim_minigame_on"),  flags.use_heal_minigame),
             ("heal_off", t("menu.aim_minigame_off"), not flags.use_heal_minigame)],
            btn_w=_BTN_W_SM)
        cy += _ROW_H
        self._draw_labeled_row(screen, ox, cy, pw, t("settings.gameplay.melee"),
            [("melee_on",  t("menu.aim_minigame_on"),  flags.use_melee_minigame),
             ("melee_off", t("menu.aim_minigame_off"), not flags.use_melee_minigame)],
            btn_w=_BTN_W_SM)
        cy += _ROW_H
        if flags.use_heal_minigame:
            cy = self._draw_threshold_row(screen, ox, cy, pw,
                                          t("settings.gameplay.heal_threshold"),
                                          flags.heal_threshold_pct)
        cy += 8
        self._draw_sep(screen, ox, cy, pw)
        cy += 10

        # --- LANGUAGE ---
        cy = self._draw_section_label(screen, ox, cy, pw, t("settings.section.language"))
        self._draw_labeled_row(screen, ox, cy, pw, "",
            [("en", "English", lang == "en"),
             ("cs", "Česky",   lang == "cs"),
             ("es", "Español", lang == "es")],
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
        bx = ox + _PAD
        by = cy + (_ROW_H - _BTN_H) // 2
        if label:
            lbl_surf = self._font_lbl.render(label, True, _COL_LBL)
            screen.blit(lbl_surf, (bx, by + (_BTN_H - self._font_lbl.get_height()) // 2 + 1))
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
                               rect.centery - self._font_btn.get_height() // 2 + 1))
            self._btn_rects[key] = rect
            bx += btn_w + gap

    def _draw_volume_row(self, screen: pygame.Surface, ox: int, cy: int, pw: int,
                          label: str, key: str, value: float) -> int:
        bx  = ox + _PAD
        by  = cy + (_ROW_H - _BTN_H) // 2
        lbl_surf = self._font_lbl.render(label, True, _COL_LBL)
        screen.blit(lbl_surf, (bx, by + (_BTN_H - self._font_lbl.get_height()) // 2 + 1))
        bx += _LBL_W + 8
        arrow_w = 28
        val_w   = 52
        # [◄]
        dn_rect = pygame.Rect(bx, by, arrow_w, _BTN_H)
        dn_key  = f"{key}_dn"
        hov_dn  = self._hovered == dn_key
        _bg  = _BTN_HOV if hov_dn else _BTN_NRM
        _brd = _COL_BORDER_HOV if hov_dn else _COL_BORDER_NRM
        pygame.draw.rect(screen, _bg,  dn_rect, border_radius=4)
        pygame.draw.rect(screen, _brd, dn_rect, 2, border_radius=4)
        arr = self._font_btn.render("◄", True, _COL_BTN_NRM)
        screen.blit(arr, (dn_rect.centerx - arr.get_width() // 2,
                          dn_rect.centery - self._font_btn.get_height() // 2 + 1))
        self._btn_rects[dn_key] = dn_rect
        bx += arrow_w + 4
        # pct value
        pct = f"{int(round(value * 100))}%"
        val_surf = self._font_vol.render(pct, True, _COL_BTN_SEL)
        screen.blit(val_surf, (bx + (val_w - val_surf.get_width()) // 2,
                                by + (_BTN_H - self._font_vol.get_height()) // 2 + 1))
        bx += val_w + 4
        # [►]
        up_rect = pygame.Rect(bx, by, arrow_w, _BTN_H)
        up_key  = f"{key}_up"
        hov_up  = self._hovered == up_key
        _bg2  = _BTN_HOV if hov_up else _BTN_NRM
        _brd2 = _COL_BORDER_HOV if hov_up else _COL_BORDER_NRM
        pygame.draw.rect(screen, _bg2,  up_rect, border_radius=4)
        pygame.draw.rect(screen, _brd2, up_rect, 2, border_radius=4)
        arr2 = self._font_btn.render("►", True, _COL_BTN_NRM)
        screen.blit(arr2, (up_rect.centerx - arr2.get_width() // 2,
                           up_rect.centery - self._font_btn.get_height() // 2 + 1))
        self._btn_rects[up_key] = up_rect
        return cy + _ROW_H

    def _draw_threshold_row(self, screen: pygame.Surface, ox: int, cy: int,
                             pw: int, label: str, value: int) -> int:
        bx = ox + _PAD
        by = cy + (_ROW_H - _BTN_H) // 2
        lbl_surf = self._font_lbl.render(label, True, _COL_LBL)
        screen.blit(lbl_surf, (bx, by + (_BTN_H - self._font_lbl.get_height()) // 2 + 1))
        bx += _LBL_W + 8
        arrow_w = 28
        val_w   = 52
        # [◄]
        dn_rect = pygame.Rect(bx, by, arrow_w, _BTN_H)
        hov_dn  = self._hovered == "heal_thr_dn"
        _bg  = _BTN_HOV if hov_dn else _BTN_NRM
        _brd = _COL_BORDER_HOV if hov_dn else _COL_BORDER_NRM
        pygame.draw.rect(screen, _bg,  dn_rect, border_radius=4)
        pygame.draw.rect(screen, _brd, dn_rect, 2, border_radius=4)
        arr = self._font_btn.render("◄", True, _COL_BTN_NRM)
        screen.blit(arr, (dn_rect.centerx - arr.get_width() // 2,
                          dn_rect.centery - self._font_btn.get_height() // 2 + 1))
        self._btn_rects["heal_thr_dn"] = dn_rect
        bx += arrow_w + 4
        # pct %
        pct_surf = self._font_vol.render(f"{value}%", True, _COL_BTN_SEL)
        screen.blit(pct_surf, (bx + (val_w - pct_surf.get_width()) // 2,
                                by + (_BTN_H - self._font_vol.get_height()) // 2 + 1))
        bx += val_w + 4
        # [►]
        up_rect = pygame.Rect(bx, by, arrow_w, _BTN_H)
        hov_up  = self._hovered == "heal_thr_up"
        _bg2  = _BTN_HOV if hov_up else _BTN_NRM
        _brd2 = _COL_BORDER_HOV if hov_up else _COL_BORDER_NRM
        pygame.draw.rect(screen, _bg2,  up_rect, border_radius=4)
        pygame.draw.rect(screen, _brd2, up_rect, 2, border_radius=4)
        arr2 = self._font_btn.render("►", True, _COL_BTN_NRM)
        screen.blit(arr2, (up_rect.centerx - arr2.get_width() // 2,
                           up_rect.centery - self._font_btn.get_height() // 2 + 1))
        self._btn_rects["heal_thr_up"] = up_rect
        bx += arrow_w + 8
        sfx_surf = self._font_lbl.render(t("settings.gameplay.heal_threshold_suffix"), True, _COL_LBL)
        screen.blit(sfx_surf, (bx, by + (_BTN_H - self._font_lbl.get_height()) // 2 + 1))
        # hint line
        hint_surf = self._font_foot.render(t(f"menu.heal.thr.{value}"), True, _COL_LBL)
        hint_x = ox + _PAD + _LBL_W + 8 + arrow_w + 4 + (val_w - hint_surf.get_width()) // 2
        screen.blit(hint_surf, (hint_x, cy + _ROW_H))
        return cy + _ROW_H + _HINT_H

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
        flags = s._effective_flags()

        if hit == "minigame":       s._set_flag("use_minigame", True)
        elif hit == "random":       s._set_flag("use_minigame", False)
        elif hit == "aim_on":       s._set_flag("use_aim_minigame", True)
        elif hit == "aim_off":      s._set_flag("use_aim_minigame", False)
        elif hit == "heal_on":      s._set_flag("use_heal_minigame", True)
        elif hit == "heal_off":     s._set_flag("use_heal_minigame", False)
        elif hit == "melee_on":     s._set_flag("use_melee_minigame", True)
        elif hit == "melee_off":    s._set_flag("use_melee_minigame", False)
        elif hit == "heal_thr_dn":
            idx = _THR_VALS.index(flags.heal_threshold_pct) if flags.heal_threshold_pct in _THR_VALS else 2
            s._set_flag("heal_threshold_pct", _THR_VALS[max(0, idx - 1)])
        elif hit == "heal_thr_up":
            idx = _THR_VALS.index(flags.heal_threshold_pct) if flags.heal_threshold_pct in _THR_VALS else 2
            s._set_flag("heal_threshold_pct", _THR_VALS[min(len(_THR_VALS) - 1, idx + 1)])
        elif hit in ("en", "cs", "es"):
            s._set_language(hit)
        elif hit == "master_dn":
            settings.MASTER_VOLUME = max(0.0, round(settings.MASTER_VOLUME - _VOL_STEP, 1))
            self._apply_audio()
            s._save_audio()
        elif hit == "master_up":
            settings.MASTER_VOLUME = min(1.0, round(settings.MASTER_VOLUME + _VOL_STEP, 1))
            self._apply_audio()
            s._save_audio()
        elif hit == "music_dn":
            settings.MUSIC_VOLUME = max(0.0, round(settings.MUSIC_VOLUME - _VOL_STEP, 1))
            self._apply_audio()
            s._save_audio()
        elif hit == "music_up":
            settings.MUSIC_VOLUME = min(1.0, round(settings.MUSIC_VOLUME + _VOL_STEP, 1))
            self._apply_audio()
            s._save_audio()
        elif hit == "sfx_dn":
            settings.SFX_VOLUME = max(0.0, round(settings.SFX_VOLUME - _VOL_STEP, 1))
            self._apply_audio()
            s._save_audio()
        elif hit == "sfx_up":
            settings.SFX_VOLUME = min(1.0, round(settings.SFX_VOLUME + _VOL_STEP, 1))
            self._apply_audio()
            s._save_audio()

    def _apply_audio(self) -> None:
        pygame.mixer.music.set_volume(settings.MASTER_VOLUME * settings.MUSIC_VOLUME)
