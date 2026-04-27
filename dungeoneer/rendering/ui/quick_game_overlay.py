"""Quick Game overlay — compact pre-run config without saving a profile.

Pre-fills from GlobalConfig.last_quick_config.  On Start, writes back to
last_quick_config and signals ``scene._quick_game_start(config)`` with a dict
of gameplay params.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from dungeoneer.core import settings
from dungeoneer.core.i18n import t, set_language, get_language
from dungeoneer.meta.global_config import GlobalConfig
from dungeoneer.meta.storage import load_global, save_global

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

_BTN_NRM     = (20, 40, 35)
_BTN_SEL     = (10, 80, 65)
_BTN_HOV     = (35, 90, 70)
_COL_BDR_NRM = (60, 200, 160)
_COL_BDR_SEL = (0, 240, 200)
_COL_BDR_HOV = (100, 240, 200)
_COL_BTN_NRM = (140, 180, 160)
_COL_BTN_SEL = (220, 255, 240)
_COL_BTN_HOV = (200, 240, 220)

_W      = 480
_PAD    = 22
_BTN_H  = 30
_ROW_H  = 38
_BTN_W_SM = 74
_BTN_W_MD = 106
_LBL_W    = 90


class QuickGameOverlay:
    """Compact quick-game config panel."""

    def __init__(self, scene: "MainMenuScene") -> None:
        self._scene = scene
        self._cfg: GlobalConfig = GlobalConfig()

        # Local mutable copies of config fields
        self._lang       = "en"
        self._difficulty = "normal"
        self._tutorial   = False
        self._use_minigame       = True
        self._use_aim_minigame   = True
        self._use_heal_minigame  = True
        self._use_melee_minigame = True

        self._hovered: str | None = None
        self._btn_rects: dict[str, pygame.Rect] = {}
        self._panel_rect: pygame.Rect | None = None

        self._font_title = pygame.font.SysFont("consolas", 19, bold=True)
        self._font_sec   = pygame.font.SysFont("consolas", 12, bold=True)
        self._font_lbl   = pygame.font.SysFont("consolas", 13, bold=True)
        self._font_btn   = pygame.font.SysFont("consolas", 12, bold=True)
        self._font_foot  = pygame.font.SysFont("consolas", 12)

    def refresh(self) -> None:
        """Reload from GlobalConfig.last_quick_config."""
        self._cfg = load_global()
        qc = self._cfg.last_quick_config
        self._lang             = qc.get("language", get_language())
        self._difficulty       = qc.get("difficulty", "normal")
        self._tutorial         = qc.get("tutorial", False)
        self._use_minigame       = qc.get("use_minigame", True)
        self._use_aim_minigame   = qc.get("use_aim_minigame", True)
        self._use_heal_minigame  = qc.get("use_heal_minigame", True)
        self._use_melee_minigame = qc.get("use_melee_minigame", True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def handle_key(self, key: int) -> bool:
        """Return True to close overlay."""
        if key == pygame.K_ESCAPE:
            return True
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._start()
            return True
        return False

    def handle_motion(self, pos: tuple) -> None:
        self._hovered = self._hit_test(pos)

    def handle_click(self, pos: tuple) -> bool:
        """Return True to close overlay."""
        if self._panel_rect and not self._panel_rect.collidepoint(pos):
            return True
        hit = self._hit_test(pos)
        if hit is None:
            return False
        return self._dispatch(hit)

    def draw(self, screen: pygame.Surface) -> None:
        sw, sh = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        self._btn_rects = {}

        sec_h = self._font_sec.get_height() + 4
        rows_lang = 1
        rows_diff = 1
        rows_tut  = 1
        rows_game = 4  # loot + aim + heal + melee
        inner_h = (
            32 + 8                              # title
            + sec_h + rows_lang * _ROW_H + 8
            + 1 + 8
            + sec_h + rows_diff * _ROW_H + 8
            + 1 + 8
            + sec_h + rows_tut * _ROW_H + 8
            + 1 + 8
            + sec_h + rows_game * _ROW_H + 8
            + 1 + 8
            + 32                                # Start button
            + 8
        )
        ph = inner_h + _PAD * 2
        ox = (sw - _W) // 2
        oy = (sh - ph) // 2

        panel = pygame.Surface((_W, ph), pygame.SRCALPHA)
        panel.fill(_BG)
        screen.blit(panel, (ox, oy))
        pygame.draw.rect(screen, _BORDER, (ox, oy, _W, ph), 2, border_radius=6)
        self._panel_rect = pygame.Rect(ox, oy, _W, ph)

        cy = oy + _PAD

        # Close button
        close_w = 22
        close_rect = pygame.Rect(ox + _W - _PAD - close_w, oy + _PAD // 2, close_w, close_w)
        self._btn_rects["close"] = close_rect
        hov_close = self._hovered == "close"
        pygame.draw.rect(screen, (60, 30, 30) if hov_close else _BTN_NRM, close_rect, border_radius=3)
        pygame.draw.rect(screen, (180, 60, 60), close_rect, 1, border_radius=3)
        x_s = self._font_btn.render("x", True, (180, 60, 60) if hov_close else _COL_LBL)
        screen.blit(x_s, (close_rect.centerx - x_s.get_width() // 2,
                          close_rect.centery - self._font_btn.get_height() // 2 + 1))

        # Title
        title = self._font_title.render(t("quick.title"), True, _COL_ACCENT)
        screen.blit(title, (ox + (_W - title.get_width()) // 2, cy))
        cy += title.get_height() + 6
        self._draw_sep(screen, ox, cy)
        cy += 10

        # Language
        cy = self._draw_sec(screen, ox, cy, t("settings.section.language"))
        self._draw_row(screen, ox, cy, "",
            [("qlang_en", "English", self._lang == "en"),
             ("qlang_cs", "Česky",   self._lang == "cs"),
             ("qlang_es", "Español", self._lang == "es")],
            _BTN_W_MD)
        cy += _ROW_H + 6
        self._draw_sep(screen, ox, cy)
        cy += 10

        # Difficulty
        cy = self._draw_sec(screen, ox, cy, t("menu.difficulty"))
        self._draw_row(screen, ox, cy, "",
            [("qdiff_easy",   t("menu.easy"),   self._difficulty == "easy"),
             ("qdiff_normal", t("menu.normal"), self._difficulty == "normal"),
             ("qdiff_hard",   t("menu.hard"),   self._difficulty == "hard")],
            _BTN_W_SM)
        cy += _ROW_H + 6
        self._draw_sep(screen, ox, cy)
        cy += 10

        # Tutorial
        cy = self._draw_sec(screen, ox, cy, t("quick.tutorial"))
        self._draw_row(screen, ox, cy, "",
            [("qtut_on",  t("wizard.tutorial.on"),  self._tutorial),
             ("qtut_off", t("wizard.tutorial.off"), not self._tutorial)],
            _BTN_W_SM)
        cy += _ROW_H + 6
        self._draw_sep(screen, ox, cy)
        cy += 10

        # Gameplay
        cy = self._draw_sec(screen, ox, cy, t("settings.section.gameplay"))
        self._draw_row(screen, ox, cy, t("settings.gameplay.loot"),
            [("qmg_on",  t("menu.loot.minigame"), self._use_minigame),
             ("qmg_off", t("menu.loot.random"),   not self._use_minigame)],
            _BTN_W_MD)
        cy += _ROW_H
        self._draw_row(screen, ox, cy, t("settings.gameplay.aim"),
            [("qaim_on",  t("menu.aim_minigame_on"),  self._use_aim_minigame),
             ("qaim_off", t("menu.aim_minigame_off"), not self._use_aim_minigame)],
            _BTN_W_SM)
        cy += _ROW_H
        self._draw_row(screen, ox, cy, t("settings.gameplay.heal"),
            [("qheal_on",  t("menu.aim_minigame_on"),  self._use_heal_minigame),
             ("qheal_off", t("menu.aim_minigame_off"), not self._use_heal_minigame)],
            _BTN_W_SM)
        cy += _ROW_H
        self._draw_row(screen, ox, cy, t("settings.gameplay.melee"),
            [("qmelee_on",  t("menu.aim_minigame_on"),  self._use_melee_minigame),
             ("qmelee_off", t("menu.aim_minigame_off"), not self._use_melee_minigame)],
            _BTN_W_SM)
        cy += _ROW_H + 6
        self._draw_sep(screen, ox, cy)
        cy += 10

        # Start button
        start_w = _W - _PAD * 2
        start_rect = pygame.Rect(ox + _PAD, cy, start_w, 34)
        self._btn_rects["start"] = start_rect
        hov = self._hovered == "start"
        pygame.draw.rect(screen, _BTN_HOV if hov else _BTN_SEL, start_rect, border_radius=4)
        pygame.draw.rect(screen, _COL_BDR_HOV if hov else _COL_BDR_SEL, start_rect, 2, border_radius=4)
        s_lbl = self._font_lbl.render(t("quick.start"), True,
                                      _COL_BTN_HOV if hov else _COL_BTN_SEL)
        screen.blit(s_lbl, (start_rect.centerx - s_lbl.get_width() // 2,
                             start_rect.centery - s_lbl.get_height() // 2 + 1))

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _draw_sep(self, screen: pygame.Surface, ox: int, cy: int) -> None:
        pygame.draw.line(screen, (30, 55, 50),
                         (ox + _PAD, cy), (ox + _W - _PAD, cy))

    def _draw_sec(self, screen: pygame.Surface, ox: int, cy: int, text: str) -> int:
        surf = self._font_sec.render(text, True, _COL_SEC)
        screen.blit(surf, (ox + _PAD, cy))
        return cy + surf.get_height() + 4

    def _draw_row(self, screen: pygame.Surface, ox: int, cy: int,
                  label: str, buttons: list, btn_w: int) -> None:
        bx = ox + _PAD
        by = cy + (_ROW_H - _BTN_H) // 2
        if label:
            lbl_s = self._font_lbl.render(label, True, _COL_LBL)
            screen.blit(lbl_s, (bx, by + (_BTN_H - lbl_s.get_height()) // 2 + 1))
            bx += _LBL_W + 8
        gap = 6
        for key, text, selected in buttons:
            rect = pygame.Rect(bx, by, btn_w, _BTN_H)
            hov = self._hovered == key
            bg, bdr, col = (
                (_BTN_SEL, _COL_BDR_SEL, _COL_BTN_SEL) if selected else
                (_BTN_HOV, _COL_BDR_HOV, _COL_BTN_HOV) if hov else
                (_BTN_NRM, _COL_BDR_NRM, _COL_BTN_NRM)
            )
            pygame.draw.rect(screen, bg, rect, border_radius=4)
            pygame.draw.rect(screen, bdr, rect, 2, border_radius=4)
            lbl = self._font_btn.render(text, True, col)
            screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                               rect.centery - lbl.get_height() // 2 + 1))
            self._btn_rects[key] = rect
            bx += btn_w + gap

    # ------------------------------------------------------------------
    # Hit test + dispatch
    # ------------------------------------------------------------------

    def _hit_test(self, pos: tuple) -> str | None:
        for key, rect in self._btn_rects.items():
            if rect.collidepoint(pos):
                return key
        return None

    def _dispatch(self, hit: str) -> bool:
        if hit == "close":
            return True
        if hit == "start":
            self._start()
            return True
        if hit.startswith("qlang_"):
            code = hit[6:]
            self._lang = code
            set_language(code)
        elif hit == "qdiff_easy":   self._difficulty = "easy"
        elif hit == "qdiff_normal": self._difficulty = "normal"
        elif hit == "qdiff_hard":   self._difficulty = "hard"
        elif hit == "qtut_on":      self._tutorial = True
        elif hit == "qtut_off":     self._tutorial = False
        elif hit == "qmg_on":       self._use_minigame = True
        elif hit == "qmg_off":      self._use_minigame = False
        elif hit == "qaim_on":      self._use_aim_minigame = True
        elif hit == "qaim_off":     self._use_aim_minigame = False
        elif hit == "qheal_on":     self._use_heal_minigame = True
        elif hit == "qheal_off":    self._use_heal_minigame = False
        elif hit == "qmelee_on":    self._use_melee_minigame = True
        elif hit == "qmelee_off":   self._use_melee_minigame = False
        return False

    def _start(self) -> None:
        # Save config back to global
        qc = {
            "language":           self._lang,
            "difficulty":         self._difficulty,
            "tutorial":           self._tutorial,
            "use_minigame":       self._use_minigame,
            "use_aim_minigame":   self._use_aim_minigame,
            "use_heal_minigame":  self._use_heal_minigame,
            "use_melee_minigame": self._use_melee_minigame,
        }
        self._cfg.last_quick_config = qc
        save_global(self._cfg)
        self._scene._quick_game_start(qc)
