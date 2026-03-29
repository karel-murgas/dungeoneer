"""Main menu — shown between runs.

Clean hub screen:  Start Run  |  Quit
Two icon buttons top-right:  ⚙ Settings  |  ? Help

Settings overlay holds all gameplay + audio + language config.
Help catalog overlay holds all in-game help articles by topic.
"""
from __future__ import annotations

import math
import os
from typing import List, TYPE_CHECKING

import pygame

from dungeoneer.core.scene import Scene
from dungeoneer.core import settings
from dungeoneer.core.i18n import t, set_language, get_language
from dungeoneer.core.difficulty import EASY, NORMAL, HARD, Difficulty
from dungeoneer.rendering.ui.quit_confirm import QuitConfirmDialog
from dungeoneer.rendering.ui.settings_overlay import SettingsOverlay
from dungeoneer.rendering.ui.help_catalog import HelpCatalogOverlay

if TYPE_CHECKING:
    from dungeoneer.core.game import GameApp

# ---------------------------------------------------------------------------
# Visual constants
# ---------------------------------------------------------------------------

_BG           = (8, 8, 16)
_COL_ACCENT   = (0, 220, 180)
_COL_LABEL    = (90, 120, 110)
_COL_HINT     = (45, 65, 58)

_BTN_NRM       = (20, 40, 35)
_BTN_SEL       = (10, 80, 65)
_BTN_HOV       = (35, 90, 70)
_COL_BORDER        = (60, 200, 160)
_COL_BORDER_SEL    = (0, 240, 200)
_COL_BORDER_HOV    = (100, 240, 200)

_COL_BTN_NRM   = (140, 180, 160)
_COL_BTN_SEL   = (220, 255, 240)
_COL_BTN_HOV   = (200, 240, 220)

_ICON_SIZE     = 36   # square icon button side length
_ICON_GAP      = 8    # gap between icon buttons


def _scale_to(value: int, scale: float, minimum: int) -> int:
    return max(minimum, round(value * scale))


def _draw_gear(surface: pygame.Surface, cx: int, cy: int, r: int,
               color: tuple, teeth: int = 8, tooth_h: int = 3) -> None:
    """Draw a gear icon using pygame primitives (no font needed)."""
    # Teeth — rectangles radiating from center
    tooth_w = max(2, r // 3)
    for i in range(teeth):
        angle = math.radians(i * 360 / teeth)
        tx = cx + math.cos(angle) * (r + tooth_h // 2)
        ty = cy + math.sin(angle) * (r + tooth_h // 2)
        pts = []
        for da, dr in ((-0.22, r - 1), (-0.22, r + tooth_h),
                       (0.22, r + tooth_h), (0.22, r - 1)):
            pts.append((
                cx + math.cos(angle + da) * dr,
                cy + math.sin(angle + da) * dr,
            ))
        pygame.draw.polygon(surface, color, pts)
    # Outer ring
    pygame.draw.circle(surface, color, (cx, cy), r, 2)
    # Inner hole
    hole = max(2, r - 4)
    pygame.draw.circle(surface, color, (cx, cy), hole, 2)


class MainMenuScene(Scene):
    def __init__(
        self,
        app: "GameApp",
        *,
        difficulty: Difficulty = NORMAL,
        use_minigame: bool = True,
        use_aim_minigame: bool = True,
        use_heal_minigame: bool = True,
        use_melee_minigame: bool = True,
        heal_threshold_pct: int = 100,
        use_tutorial: bool = False,
        map_size: str = "large",
        language: str = "en",
    ) -> None:
        super().__init__(app)
        self._difficulty          = difficulty
        self._use_minigame        = use_minigame
        self._use_aim_minigame    = use_aim_minigame
        self._use_heal_minigame   = use_heal_minigame
        self._use_melee_minigame  = use_melee_minigame
        self._heal_threshold_pct  = heal_threshold_pct
        self._use_tutorial        = use_tutorial
        self._map_size            = map_size
        self._language            = language

        # Scale fonts and button sizes to screen height (baseline: 720 px)
        _s = min(1.0, settings.SCREEN_HEIGHT / 720)
        self._font_title  = pygame.font.SysFont("consolas", _scale_to(56, _s, 28), bold=True)
        self._font_sub    = pygame.font.SysFont("consolas", _scale_to(20, _s, 13))
        self._font_start  = pygame.font.SysFont("consolas", _scale_to(18, _s, 12), bold=True)
        self._font_hint   = pygame.font.SysFont("consolas", _scale_to(13, _s, 10))
        self._font_icon      = pygame.font.SysFont("consolas", _scale_to(15, _s, 11), bold=True)
        self._font_icon_lg   = pygame.font.SysFont("consolas", _scale_to(22, _s, 16), bold=True)

        # Scaled button geometry
        self._btn_w_lg  = _scale_to(210, _s, 150)
        self._btn_h     = _scale_to(44, _s, 30)

        # Button rects — populated in render(), used for hit-testing
        self._btn_start:    pygame.Rect | None = None
        self._btn_quit:     pygame.Rect | None = None
        self._btn_settings: pygame.Rect | None = None
        self._btn_help:     pygame.Rect | None = None

        self._hovered: str | None = None

        # Overlays
        self._settings_open      = False
        self._settings_overlay   = SettingsOverlay(self)
        self._help_open          = False
        self._help_overlay       = HelpCatalogOverlay()
        self._exit_confirm_open  = False
        self._exit_confirm       = QuitConfirmDialog("exit_confirm")

    # ------------------------------------------------------------------
    # Scene lifecycle
    # ------------------------------------------------------------------

    def on_enter(self) -> None:
        set_language(self._language)
        _music_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "audio", "music", "menu.mp3"
        )
        pygame.mixer.music.load(_music_path)
        pygame.mixer.music.set_volume(settings.MASTER_VOLUME * settings.MUSIC_VOLUME)
        pygame.mixer.music.play(-1)

    def on_exit(self) -> None:
        pygame.mixer.music.fadeout(500)

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self._exit_confirm_open:
                    result = self._exit_confirm.handle_key(event.key)
                    if result == "confirm":
                        self.app.quit()
                    elif result == "cancel":
                        self._exit_confirm_open = False
                elif self._settings_open:
                    if self._settings_overlay.handle_key(event.key):
                        self._settings_open = False
                elif self._help_open:
                    if self._help_overlay.handle_key(event.key):
                        self._help_open = False
                else:
                    self._handle_key(event.key)

            elif event.type == pygame.MOUSEMOTION:
                if self._exit_confirm_open:
                    self._exit_confirm.handle_mouse_motion(event.pos)
                elif self._settings_open:
                    self._settings_overlay.handle_motion(event.pos)
                elif self._help_open:
                    self._help_overlay.handle_motion(event.pos)
                else:
                    self._hovered = self._hit_test(event.pos)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._exit_confirm_open:
                    result = self._exit_confirm.handle_mouse_button(event)
                    if result == "confirm":
                        self.app.quit()
                    elif result == "cancel":
                        self._exit_confirm_open = False
                elif self._settings_open:
                    if self._settings_overlay.handle_click(event.pos):
                        self._settings_open = False
                elif self._help_open:
                    if self._help_overlay.handle_click(event.pos):
                        self._help_open = False
                else:
                    self._handle_click(self._hit_test(event.pos))

    def update(self, dt: float) -> None:
        pass

    def render(self, screen: pygame.Surface) -> None:
        screen.fill(_BG)
        sw, sh = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        cx = sw // 2

        # --- Icon buttons (top-right corner) ---
        _PAD   = 14
        icon_y = 12
        # Help icon  [?]
        self._btn_help = pygame.Rect(
            sw - _PAD - _ICON_SIZE, icon_y, _ICON_SIZE, _ICON_SIZE
        )
        # Settings icon  [⚙]
        self._btn_settings = pygame.Rect(
            sw - _PAD - _ICON_SIZE * 2 - _ICON_GAP, icon_y, _ICON_SIZE, _ICON_SIZE
        )

        for rect, key in (
            (self._btn_settings, "settings"),
            (self._btn_help,     "help"),
        ):
            hov = self._hovered == key and not self._settings_open and not self._help_open
            bg  = _BTN_HOV if hov else _BTN_NRM
            bdr = _COL_BORDER_HOV if hov else _COL_BORDER
            col = _COL_BTN_HOV if hov else _COL_BTN_NRM
            pygame.draw.rect(screen, bg,  rect, border_radius=4)
            pygame.draw.rect(screen, bdr, rect, 2, border_radius=4)
            if key == "settings":
                _draw_gear(screen, rect.centerx, rect.centery, 10, col)
            else:
                lbl = self._font_icon_lg.render("?", True, col)
                screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                                   rect.centery - self._font_icon_lg.get_height() // 2 + 3))

        # --- Title block ---
        title_surf = self._font_title.render(t("menu.title"), True, _COL_ACCENT)
        title_y = max(10, sh // 12)
        screen.blit(title_surf, (cx - title_surf.get_width() // 2, title_y))

        sub_surf = self._font_sub.render(t("menu.subtitle"), True, _COL_LABEL)
        sub_y = title_y + title_surf.get_height() + 4
        screen.blit(sub_surf, (cx - sub_surf.get_width() // 2, sub_y))

        line_y = sub_y + sub_surf.get_height() + 10
        line_hw = min(290, sw // 2 - 20)
        pygame.draw.line(screen, (25, 55, 50),
                         (cx - line_hw, line_y), (cx + line_hw, line_y), 1)

        # --- Hint footer ---
        hint_surf = self._font_hint.render(t("menu.hints"), True, _COL_HINT)
        hint_y = sh - hint_surf.get_height() - 6
        screen.blit(hint_surf, (cx - hint_surf.get_width() // 2, hint_y))

        # --- Start / Quit buttons ---
        btn_gap = 20
        start_quit_y = hint_y - 12 - self._btn_h
        self._btn_start = pygame.Rect(cx - self._btn_w_lg - btn_gap // 2,
                                      start_quit_y, self._btn_w_lg, self._btn_h)
        self._btn_quit  = pygame.Rect(cx + btn_gap // 2,
                                      start_quit_y, self._btn_w_lg, self._btn_h)

        for rect, key, label in (
            (self._btn_start, "start", t("menu.start")),
            (self._btn_quit,  "quit",  t("menu.quit")),
        ):
            hov      = self._hovered == key and not self._settings_open and not self._help_open
            is_start = key == "start"
            bg     = _BTN_HOV if hov else (_BTN_SEL if is_start else _BTN_NRM)
            border = _COL_BORDER_HOV if hov else (_COL_BORDER_SEL if is_start else _COL_BORDER)
            col    = _COL_BTN_SEL if (hov or is_start) else _COL_BTN_NRM
            pygame.draw.rect(screen, bg, rect, border_radius=4)
            pygame.draw.rect(screen, border, rect, 2, border_radius=4)
            lbl = self._font_start.render(label, True, col)
            screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                               rect.centery - self._font_start.get_height() // 2 + 2))

        # --- Overlays (drawn on top) ---
        if self._settings_open:
            self._settings_overlay.draw(screen)
        elif self._help_open:
            self._help_overlay.draw(screen)
        elif self._exit_confirm_open:
            self._exit_confirm.draw(screen)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _hit_test(self, pos) -> str | None:
        checks = [
            ("settings", self._btn_settings),
            ("help",     self._btn_help),
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
            self._exit_confirm_open = True
        elif key == pygame.K_F1:
            self._help_open = True

    def _handle_click(self, hit: str | None) -> None:
        if hit == "start":    self._start()
        elif hit == "quit":   self._exit_confirm_open = True
        elif hit == "settings": self._settings_open = True
        elif hit == "help":     self._help_open = True

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
                use_aim_minigame=self._use_aim_minigame,
                use_heal_minigame=self._use_heal_minigame,
                use_melee_minigame=self._use_melee_minigame,
                heal_threshold_pct=self._heal_threshold_pct,
                use_tutorial=self._use_tutorial,
                map_size=self._map_size,
            )
        )
