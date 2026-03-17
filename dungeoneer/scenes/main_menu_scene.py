"""Main menu — shown between runs.

Lets the player configure:
  - Difficulty  (Easy / Normal / Hard)
  - Loot mode   (Hack Minigame / Random Loot)
  - Language    (English / Czech / Spanish)

Then start a new run or quit.
"""
from __future__ import annotations

import os
from typing import List, TYPE_CHECKING

import pygame

from dungeoneer.core.scene import Scene
from dungeoneer.core import settings
from dungeoneer.core.i18n import t, set_language, get_language
from dungeoneer.core.difficulty import EASY, NORMAL, HARD, Difficulty

if TYPE_CHECKING:
    from dungeoneer.core.game import GameApp

# ---------------------------------------------------------------------------
# Visual constants
# ---------------------------------------------------------------------------

_BG           = (8, 8, 16)
_COL_ACCENT   = (0, 220, 180)
_COL_LABEL    = (90, 120, 110)
_COL_HINT     = (45, 65, 58)

_BTN_W_SM  = 130
_BTN_W_MED = 170
_BTN_W_LG  = 210
_BTN_H     = 40

_BTN_NRM       = (20, 40, 35)
_BTN_SEL       = (10, 80, 65)
_BTN_HOV       = (35, 90, 70)
_COL_BORDER        = (60, 200, 160)
_COL_BORDER_SEL    = (0, 240, 200)
_COL_BORDER_HOV    = (100, 240, 200)

_COL_BTN_NRM   = (140, 180, 160)
_COL_BTN_SEL   = (220, 255, 240)
_COL_BTN_HOV   = (200, 240, 220)

_GAP_SECTION   = 80   # vertical space between option rows


class MainMenuScene(Scene):
    def __init__(
        self,
        app: "GameApp",
        *,
        difficulty: Difficulty = NORMAL,
        use_minigame: bool = True,
        language: str = "en",
    ) -> None:
        super().__init__(app)
        self._difficulty   = difficulty
        self._use_minigame = use_minigame
        self._language     = language

        self._font_title  = pygame.font.SysFont("consolas", 56, bold=True)
        self._font_sub    = pygame.font.SysFont("consolas", 20)
        self._font_label  = pygame.font.SysFont("consolas", 15, bold=True)
        self._font_btn    = pygame.font.SysFont("consolas", 15, bold=True)
        self._font_start  = pygame.font.SysFont("consolas", 18, bold=True)
        self._font_hint   = pygame.font.SysFont("consolas", 14)

        # Button rects — populated in render(), used for hit-testing
        self._btn_easy:     pygame.Rect | None = None
        self._btn_normal:   pygame.Rect | None = None
        self._btn_hard:     pygame.Rect | None = None
        self._btn_minigame: pygame.Rect | None = None
        self._btn_random:   pygame.Rect | None = None
        self._btn_en:       pygame.Rect | None = None
        self._btn_cs:       pygame.Rect | None = None
        self._btn_es:       pygame.Rect | None = None
        self._btn_start:    pygame.Rect | None = None
        self._btn_quit:     pygame.Rect | None = None

        self._hovered: str | None = None

    # ------------------------------------------------------------------
    # Scene lifecycle
    # ------------------------------------------------------------------

    def on_enter(self) -> None:
        set_language(self._language)
        _music_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "audio", "music", "menu.mp3"
        )
        pygame.mixer.music.load(_music_path)
        pygame.mixer.music.set_volume(0.30)
        pygame.mixer.music.play(-1)

    def on_exit(self) -> None:
        pygame.mixer.music.fadeout(500)

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                self._handle_key(event.key)
            elif event.type == pygame.MOUSEMOTION:
                self._hovered = self._hit_test(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(self._hit_test(event.pos))

    def update(self, dt: float) -> None:
        pass

    def render(self, screen: pygame.Surface) -> None:
        screen.fill(_BG)
        sw, sh = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        cx = sw // 2

        # --- Title ---
        title_surf = self._font_title.render(t("menu.title"), True, _COL_ACCENT)
        screen.blit(title_surf, (cx - title_surf.get_width() // 2, 55))

        sub_surf = self._font_sub.render(t("menu.subtitle"), True, _COL_LABEL)
        screen.blit(sub_surf, (cx - sub_surf.get_width() // 2, 124))

        pygame.draw.line(screen, (25, 55, 50), (cx - 290, 158), (cx + 290, 158), 1)

        # --- Option rows ---
        row_y = 182

        # Difficulty
        row_y = self._draw_option_row(
            screen, cx, row_y, t("menu.difficulty"),
            [
                ("easy",   t("menu.easy"),   self._difficulty is EASY),
                ("normal", t("menu.normal"), self._difficulty is NORMAL),
                ("hard",   t("menu.hard"),   self._difficulty is HARD),
            ],
            btn_w=_BTN_W_SM,
        )
        row_y += _GAP_SECTION

        # Loot mode
        row_y = self._draw_option_row(
            screen, cx, row_y, t("menu.loot_mode"),
            [
                ("minigame", t("menu.loot.minigame"), self._use_minigame),
                ("random",   t("menu.loot.random"),   not self._use_minigame),
            ],
            btn_w=_BTN_W_MED,
        )
        row_y += _GAP_SECTION

        # Language — labels always shown in the native language
        row_y = self._draw_option_row(
            screen, cx, row_y, t("menu.language"),
            [
                ("en", "English", self._language == "en"),
                ("cs", "Česky",   self._language == "cs"),
                ("es", "Español", self._language == "es"),
            ],
            btn_w=_BTN_W_SM,
        )

        # --- Start / Quit ---
        btn_y = sh - 115
        self._btn_start = pygame.Rect(cx - _BTN_W_LG - 14, btn_y, _BTN_W_LG, _BTN_H + 8)
        self._btn_quit  = pygame.Rect(cx + 14,              btn_y, _BTN_W_LG, _BTN_H + 8)

        for rect, key, label in (
            (self._btn_start, "start", t("menu.start")),
            (self._btn_quit,  "quit",  t("menu.quit")),
        ):
            is_hov = self._hovered == key
            is_start = key == "start"
            bg     = _BTN_HOV if is_hov else (_BTN_SEL if is_start else _BTN_NRM)
            border = _COL_BORDER_HOV if is_hov else (_COL_BORDER_SEL if is_start else _COL_BORDER)
            col    = _COL_BTN_SEL if (is_hov or is_start) else _COL_BTN_NRM
            pygame.draw.rect(screen, bg, rect, border_radius=4)
            pygame.draw.rect(screen, border, rect, 2, border_radius=4)
            lbl = self._font_start.render(label, True, col)
            screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                               rect.centery - lbl.get_height() // 2))

        # --- Keyboard hints ---
        hint_surf = self._font_hint.render(t("menu.hints"), True, _COL_HINT)
        screen.blit(hint_surf, (cx - hint_surf.get_width() // 2, sh - 38))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _draw_option_row(
        self, screen, cx: int, y: int, label: str,
        buttons: list[tuple[str, str, bool]],
        btn_w: int,
    ) -> int:
        """Draw a labelled row of toggle buttons; return the y after the row."""
        lbl_surf = self._font_label.render(label, True, _COL_LABEL)
        screen.blit(lbl_surf, (cx - lbl_surf.get_width() // 2, y))

        gap   = 10
        total = len(buttons) * btn_w + (len(buttons) - 1) * gap
        bx    = cx - total // 2
        by    = y + 22

        for key, text, selected in buttons:
            rect = pygame.Rect(bx, by, btn_w, _BTN_H)
            self._draw_toggle_btn(screen, rect, text, selected, self._hovered == key)
            setattr(self, f"_btn_{key}", rect)
            bx += btn_w + gap

        return by + _BTN_H

    def _draw_toggle_btn(
        self, screen, rect: pygame.Rect, label: str, selected: bool, hovered: bool
    ) -> None:
        if selected:
            bg, border, col = _BTN_SEL, _COL_BORDER_SEL, _COL_BTN_SEL
        elif hovered:
            bg, border, col = _BTN_HOV, _COL_BORDER_HOV, _COL_BTN_HOV
        else:
            bg, border, col = _BTN_NRM, _COL_BORDER, _COL_BTN_NRM
        pygame.draw.rect(screen, bg, rect, border_radius=4)
        pygame.draw.rect(screen, border, rect, 2, border_radius=4)
        lbl = self._font_btn.render(label, True, col)
        screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                           rect.centery - lbl.get_height() // 2))

    def _hit_test(self, pos) -> str | None:
        checks = [
            ("easy",     self._btn_easy),
            ("normal",   self._btn_normal),
            ("hard",     self._btn_hard),
            ("minigame", self._btn_minigame),
            ("random",   self._btn_random),
            ("en",       self._btn_en),
            ("cs",       self._btn_cs),
            ("es",       self._btn_es),
            ("start",    self._btn_start),
            ("quit",     self._btn_quit),
        ]
        for key, rect in checks:
            if rect and rect.collidepoint(pos):
                return key
        return None

    def _handle_key(self, key: int) -> None:
        if key == pygame.K_RETURN:
            self._start()
        elif key == pygame.K_ESCAPE:
            self.app.quit()
        elif key == pygame.K_1:
            self._set_difficulty(EASY)
        elif key == pygame.K_2:
            self._set_difficulty(NORMAL)
        elif key == pygame.K_3:
            self._set_difficulty(HARD)
        elif key == pygame.K_m:
            self._use_minigame = not self._use_minigame
        elif key == pygame.K_l:
            langs = ["en", "cs", "es"]
            idx = langs.index(self._language) if self._language in langs else 0
            self._set_language(langs[(idx + 1) % len(langs)])

    def _handle_click(self, hit: str | None) -> None:
        if hit == "easy":       self._set_difficulty(EASY)
        elif hit == "normal":   self._set_difficulty(NORMAL)
        elif hit == "hard":     self._set_difficulty(HARD)
        elif hit == "minigame": self._use_minigame = True
        elif hit == "random":   self._use_minigame = False
        elif hit == "en":       self._set_language("en")
        elif hit == "cs":       self._set_language("cs")
        elif hit == "es":       self._set_language("es")
        elif hit == "start":    self._start()
        elif hit == "quit":     self.app.quit()

    def _set_difficulty(self, diff: Difficulty) -> None:
        self._difficulty = diff

    def _set_language(self, lang: str) -> None:
        self._language = lang
        set_language(lang)

    def _start(self) -> None:
        from dungeoneer.scenes.game_scene import GameScene
        self.app.scenes.replace(
            GameScene(
                self.app,
                difficulty=self._difficulty,
                use_minigame=self._use_minigame,
            )
        )
