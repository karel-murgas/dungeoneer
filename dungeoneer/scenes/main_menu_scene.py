"""Main menu — profile hub shown between runs.

Hub layout:
  Title + active profile name (large, top-centre)
  2x2 button grid: Continue | Load Game / New Game | Quick Game
  Full-width Quit below
  Icon buttons top-right: Settings (gear) | Help (?)

Profile state is loaded from GlobalConfig.last_active_profile on on_enter.
All gameplay flags are read from the active profile (or quick-game defaults).
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
from dungeoneer.meta.global_config import GlobalConfig
from dungeoneer.meta.profile import Profile, GameplayFlags
from dungeoneer.meta.storage import (
    load_global, save_global, load_profile, save_profile,
    list_profiles, profile_exists,
)
from dungeoneer.rendering.ui.quit_confirm import QuitConfirmDialog
from dungeoneer.rendering.ui.settings_overlay import SettingsOverlay
from dungeoneer.rendering.ui.help_catalog import HelpCatalogOverlay
from dungeoneer.rendering.ui.new_game_wizard import NewGameWizard
from dungeoneer.rendering.ui.load_game_picker import LoadGamePicker
from dungeoneer.rendering.ui.quick_game_overlay import QuickGameOverlay
if TYPE_CHECKING:
    from dungeoneer.core.game import GameApp

# ---------------------------------------------------------------------------
# Difficulty string → object mapping
# ---------------------------------------------------------------------------

_DIFF_MAP: dict[str, Difficulty] = {
    "easy":   EASY,
    "normal": NORMAL,
    "hard":   HARD,
}

# ---------------------------------------------------------------------------
# Visual constants
# ---------------------------------------------------------------------------

_BG           = (8, 8, 16)
_COL_ACCENT   = (0, 220, 180)
_COL_LABEL    = (90, 120, 110)
_COL_HINT     = (45, 65, 58)
_COL_DIM      = (55, 70, 65)

_BTN_NRM           = (20, 40, 35)
_BTN_SEL           = (10, 80, 65)
_BTN_HOV           = (35, 90, 70)
_BTN_DIS           = (15, 28, 24)
_COL_BORDER        = (60, 200, 160)
_COL_BORDER_SEL    = (0, 240, 200)
_COL_BORDER_HOV    = (100, 240, 200)
_COL_BORDER_DIS    = (30, 55, 48)

_COL_BTN_NRM   = (140, 180, 160)
_COL_BTN_SEL   = (220, 255, 240)
_COL_BTN_HOV   = (200, 240, 220)
_COL_BTN_DIS   = (60, 80, 72)

_ICON_SIZE     = 36
_ICON_GAP      = 8


def _scale_to(value: int, scale: float, minimum: int) -> int:
    return max(minimum, round(value * scale))


def _draw_gear(surface: pygame.Surface, cx: int, cy: int, r: int,
               color: tuple, teeth: int = 8, tooth_h: int = 3) -> None:
    tooth_w = max(2, r // 3)
    for i in range(teeth):
        angle = math.radians(i * 360 / teeth)
        pts = []
        for da, dr in ((-0.22, r - 1), (-0.22, r + tooth_h),
                       (0.22, r + tooth_h), (0.22, r - 1)):
            pts.append((cx + math.cos(angle + da) * dr,
                        cy + math.sin(angle + da) * dr))
        pygame.draw.polygon(surface, color, pts)
    pygame.draw.circle(surface, color, (cx, cy), r, 2)
    pygame.draw.circle(surface, color, (cx, cy), max(2, r - 4), 2)


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------

class MainMenuScene(Scene):
    def __init__(self, app: "GameApp") -> None:
        super().__init__(app)

        self._active_profile: Profile | None = None
        self._global_cfg: GlobalConfig = GlobalConfig()

        _s = min(1.0, settings.SCREEN_HEIGHT / 720)
        self._font_title   = pygame.font.SysFont("consolas", _scale_to(52, _s, 26), bold=True)
        self._font_profile = pygame.font.SysFont("consolas", _scale_to(22, _s, 14), bold=True)
        self._font_diff    = pygame.font.SysFont("consolas", _scale_to(13, _s, 10))
        self._font_btn     = pygame.font.SysFont("consolas", _scale_to(16, _s, 11), bold=True)
        self._font_hint    = pygame.font.SysFont("consolas", _scale_to(12, _s, 9))
        self._font_icon_lg = pygame.font.SysFont("consolas", _scale_to(22, _s, 16), bold=True)

        self._btn_w = _scale_to(190, _s, 130)
        self._btn_h = _scale_to(44, _s, 30)

        # Button rects — populated in render()
        self._btn_rects: dict[str, pygame.Rect] = {}
        self._hovered: str | None = None

        # Overlay flags
        self._settings_open   = False
        self._help_open       = False
        self._exit_confirm_open = False
        self._wizard_open     = False
        self._load_open       = False
        self._quick_open      = False
        # Overlay instances
        self._settings_overlay  = SettingsOverlay(self)
        self._help_overlay      = HelpCatalogOverlay()
        self._exit_confirm      = QuitConfirmDialog("exit_confirm")
        self._wizard            = NewGameWizard(self)
        self._load_picker       = LoadGamePicker(self)
        self._quick_overlay     = QuickGameOverlay(self)

    # ------------------------------------------------------------------
    # Scene lifecycle
    # ------------------------------------------------------------------

    def on_enter(self) -> None:
        self._global_cfg = load_global()
        # Restore audio volumes from global config
        settings.MASTER_VOLUME = self._global_cfg.master_volume
        settings.MUSIC_VOLUME  = self._global_cfg.music_volume
        settings.SFX_VOLUME    = self._global_cfg.sfx_volume

        # Load active profile
        self._active_profile = None
        if self._global_cfg.last_active_profile:
            self._active_profile = load_profile(self._global_cfg.last_active_profile)
            if self._active_profile is None:
                # Profile file gone; clear the stale reference
                self._global_cfg.last_active_profile = None
                save_global(self._global_cfg)

        # Set language from profile, or from quick config, or keep current
        if self._active_profile:
            set_language(self._active_profile.language)
        else:
            lang = self._global_cfg.last_quick_config.get("language", get_language())
            set_language(lang)

        # Start menu music
        _music_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "audio", "music", "menu.mp3"
        )
        try:
            pygame.mixer.music.load(_music_path)
            pygame.mixer.music.set_volume(settings.MASTER_VOLUME * settings.MUSIC_VOLUME)
            pygame.mixer.music.play(-1)
        except Exception:
            pass

    def on_exit(self) -> None:
        pygame.mixer.music.fadeout(500)

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
            elif event.type == pygame.TEXTINPUT:
                if self._wizard_open:
                    self._wizard.handle_text(event.text)
            elif event.type == pygame.MOUSEMOTION:
                self._handle_motion(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event)
            elif event.type == pygame.MOUSEWHEEL:
                if self._load_open:
                    self._load_picker.handle_scroll(event.y)

    def _handle_keydown(self, event: pygame.event.Event) -> None:
        key = event.key
        if self._exit_confirm_open:
            result = self._exit_confirm.handle_key(key)
            if result == "confirm":   self.app.quit()
            elif result == "cancel":  self._exit_confirm_open = False
        elif self._wizard_open:
            if self._wizard.handle_key(key):
                self._close_wizard()
        elif self._load_open:
            if self._load_picker.handle_key(key):
                self._load_open = False
        elif self._quick_open:
            if self._quick_overlay.handle_key(key):
                self._quick_open = False
        elif self._settings_open:
            if self._settings_overlay.handle_key(key):
                self._settings_open = False
        elif self._help_open:
            if self._help_overlay.handle_key(key):
                self._help_open = False
        else:
            if key == pygame.K_ESCAPE:
                self._exit_confirm_open = True
            elif key == pygame.K_F1:
                self._help_open = True

    def _handle_motion(self, pos: tuple) -> None:
        if self._exit_confirm_open:
            self._exit_confirm.handle_mouse_motion(pos)
        elif self._wizard_open:
            self._wizard.handle_motion(pos)
        elif self._load_open:
            self._load_picker.handle_motion(pos)
        elif self._quick_open:
            self._quick_overlay.handle_motion(pos)
        elif self._settings_open:
            self._settings_overlay.handle_motion(pos)
        elif self._help_open:
            self._help_overlay.handle_motion(pos)
        else:
            self._hovered = self._hit_test(pos)

    def _handle_click(self, event: pygame.event.Event) -> None:
        pos = event.pos
        if self._exit_confirm_open:
            result = self._exit_confirm.handle_mouse_button(event)
            if result == "confirm":   self.app.quit()
            elif result == "cancel":  self._exit_confirm_open = False
        elif self._wizard_open:
            if self._wizard.handle_click(pos):
                self._close_wizard()
        elif self._load_open:
            if self._load_picker.handle_click(pos):
                self._load_open = False
        elif self._quick_open:
            if self._quick_overlay.handle_click(pos):
                self._quick_open = False
        elif self._settings_open:
            if self._settings_overlay.handle_click(pos):
                self._settings_open = False
        elif self._help_open:
            if self._help_overlay.handle_click(pos):
                self._help_open = False
        else:
            hit = self._hit_test(pos)
            self._dispatch_hub(hit)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        if self._wizard_open:
            self._wizard.update(dt)

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(self, screen: pygame.Surface) -> None:
        screen.fill(_BG)
        sw, sh = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        cx = sw // 2

        _PAD = 14

        # --- Icon buttons top-right ---
        icon_y = 12
        self._btn_rects["help"] = pygame.Rect(
            sw - _PAD - _ICON_SIZE, icon_y, _ICON_SIZE, _ICON_SIZE
        )
        self._btn_rects["settings"] = pygame.Rect(
            sw - _PAD - _ICON_SIZE * 2 - _ICON_GAP, icon_y, _ICON_SIZE, _ICON_SIZE
        )

        any_overlay = (self._settings_open or self._help_open or self._exit_confirm_open
                       or self._wizard_open or self._load_open or self._quick_open)

        for key in ("settings", "help"):
            rect = self._btn_rects[key]
            hov = self._hovered == key and not any_overlay
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
        title_y = max(10, sh // 12)
        title_surf = self._font_title.render(t("menu.title"), True, _COL_ACCENT)
        screen.blit(title_surf, (cx - title_surf.get_width() // 2, title_y))

        # Sub / profile name line
        sub_y = title_y + title_surf.get_height() + 6
        if self._active_profile:
            profile_surf = self._font_profile.render(
                t("menu.profile.active").format(name=self._active_profile.name),
                True, _COL_BTN_SEL,
            )
            screen.blit(profile_surf, (cx - profile_surf.get_width() // 2, sub_y))
            diff_map = {"easy": t("menu.easy"), "normal": t("menu.normal"), "hard": t("menu.hard")}
            diff_name = diff_map.get(self._active_profile.difficulty, self._active_profile.difficulty)
            diff_surf = self._font_diff.render(
                t("menu.profile.difficulty").format(name=diff_name), True, _COL_LABEL
            )
            screen.blit(diff_surf, (cx - diff_surf.get_width() // 2,
                                     sub_y + profile_surf.get_height() + 2))
        else:
            na_surf = self._font_profile.render(t("menu.profile.no_active"), True, _COL_DIM)
            screen.blit(na_surf, (cx - na_surf.get_width() // 2, sub_y))

        # Separator line
        line_y = sub_y + self._font_profile.get_height() + (
            self._font_diff.get_height() + 6 if self._active_profile else 10
        )
        line_hw = min(280, sw // 2 - 20)
        pygame.draw.line(screen, (25, 55, 50),
                         (cx - line_hw, line_y), (cx + line_hw, line_y), 1)

        # --- Hub button grid ---
        has_profile = self._active_profile is not None
        gap_x = 20
        gap_y = 14

        grid_w = self._btn_w * 2 + gap_x
        grid_x = cx - grid_w // 2
        grid_y = line_y + 20

        _buttons = [
            # (key, i18n_key, col, row, enabled)
            ("continue", "menu.continue", 0, 0, has_profile),
            ("load",     "menu.load",     1, 0, True),
            ("new_game", "menu.new_game", 0, 1, True),
            ("quick",    "menu.quick",    1, 1, True),
        ]

        for key, i18n_key, col, row, enabled in _buttons:
            rx = grid_x + col * (self._btn_w + gap_x)
            ry = grid_y + row * (self._btn_h + gap_y)
            rect = pygame.Rect(rx, ry, self._btn_w, self._btn_h)
            self._btn_rects[key] = rect

            hov = self._hovered == key and not any_overlay and enabled
            is_primary = key in ("continue", "new_game")

            if not enabled:
                bg, bdr, col_txt = _BTN_DIS, _COL_BORDER_DIS, _COL_BTN_DIS
            elif hov:
                bg, bdr, col_txt = _BTN_HOV, _COL_BORDER_HOV, _COL_BTN_HOV
            elif is_primary:
                bg, bdr, col_txt = _BTN_SEL, _COL_BORDER_SEL, _COL_BTN_SEL
            else:
                bg, bdr, col_txt = _BTN_NRM, _COL_BORDER, _COL_BTN_NRM

            pygame.draw.rect(screen, bg, rect, border_radius=4)
            pygame.draw.rect(screen, bdr, rect, 2, border_radius=4)
            lbl = self._font_btn.render(t(i18n_key), True, col_txt)
            screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                               rect.centery - self._font_btn.get_height() // 2 + 2))

        # Quit — full-width centred below the 2×2 grid
        quit_rect = pygame.Rect(grid_x, grid_y + 2 * (self._btn_h + gap_y), grid_w, self._btn_h)
        self._btn_rects["quit"] = quit_rect
        hov_quit = self._hovered == "quit" and not any_overlay
        bg_q  = _BTN_HOV       if hov_quit else _BTN_NRM
        bdr_q = _COL_BORDER_HOV if hov_quit else _COL_BORDER
        txt_q = _COL_BTN_HOV   if hov_quit else _COL_BTN_NRM
        pygame.draw.rect(screen, bg_q, quit_rect, border_radius=4)
        pygame.draw.rect(screen, bdr_q, quit_rect, 2, border_radius=4)
        lbl_q = self._font_btn.render(t("menu.quit"), True, txt_q)
        screen.blit(lbl_q, (quit_rect.centerx - lbl_q.get_width() // 2,
                             quit_rect.centery - self._font_btn.get_height() // 2 + 2))

        # Hint footer
        hint_surf = self._font_hint.render("[F1] Help   [Esc] Quit", True, _COL_HINT)
        screen.blit(hint_surf, (cx - hint_surf.get_width() // 2,
                                 sh - hint_surf.get_height() - 6))

        # --- Overlays ---
        if self._exit_confirm_open:
            self._exit_confirm.draw(screen)
        elif self._wizard_open:
            self._wizard.draw(screen)
        elif self._load_open:
            self._load_picker.draw(screen)
        elif self._quick_open:
            self._quick_overlay.draw(screen)
        elif self._settings_open:
            self._settings_overlay.draw(screen)
        elif self._help_open:
            self._help_overlay.draw(screen)

    # ------------------------------------------------------------------
    # Hub dispatch
    # ------------------------------------------------------------------

    def _hit_test(self, pos: tuple) -> str | None:
        for key, rect in self._btn_rects.items():
            if rect and rect.collidepoint(pos):
                return key
        return None

    def _dispatch_hub(self, hit: str | None) -> None:
        if hit == "continue":
            if self._active_profile:
                self._go_to_meta(self._active_profile)
        elif hit == "new_game":
            self._open_wizard()
        elif hit == "load":
            self._load_picker.refresh()
            self._load_open = True
        elif hit == "quick":
            self._quick_overlay.refresh()
            self._quick_open = True
        elif hit == "quit":
            self._exit_confirm_open = True
        elif hit == "settings":
            self._settings_open = True
        elif hit == "help":
            self._help_open = True

    # ------------------------------------------------------------------
    # Overlay callbacks
    # ------------------------------------------------------------------

    def _open_wizard(self) -> None:
        self._wizard.reset()
        self._wizard_open = True
        pygame.key.start_text_input()

    def _close_wizard(self) -> None:
        self._wizard_open = False
        pygame.key.stop_text_input()

    def _wizard_done(self, profile: Profile) -> None:
        """Called by NewGameWizard when profile is created; go to between-runs hub."""
        self._global_cfg.last_active_profile = profile.name
        save_global(self._global_cfg)
        self._active_profile = profile
        self._wizard_open = False
        pygame.key.stop_text_input()
        self._go_to_meta(profile)

    def _load_game_done(self, name: str) -> None:
        """Called by LoadGamePicker when a profile row is selected."""
        profile = load_profile(name)
        if profile is None:
            return
        self._global_cfg.last_active_profile = name
        save_global(self._global_cfg)
        self._active_profile = profile
        self._load_open = False
        self._go_to_meta(profile)

    def _quick_game_start(self, config: dict) -> None:
        """Called by QuickGameOverlay on Start; go to between-runs hub with no profile."""
        self._quick_open = False
        self._global_cfg.last_quick_config = config
        save_global(self._global_cfg)
        self._go_to_meta(None)

    # ------------------------------------------------------------------
    # Navigation to MetaScene
    # ------------------------------------------------------------------

    def _go_to_meta(self, profile: Profile | None) -> None:
        if profile:
            set_language(profile.language)
        from dungeoneer.scenes.meta_scene import MetaScene
        self.app.scenes.replace(MetaScene(self.app, profile, self._global_cfg))

    # ------------------------------------------------------------------
    # Settings overlay helpers
    # ------------------------------------------------------------------

    def _effective_flags(self) -> GameplayFlags:
        if self._active_profile:
            return self._active_profile.flags
        qc = self._global_cfg.last_quick_config
        return GameplayFlags(
            use_minigame=qc.get("use_minigame", True),
            use_aim_minigame=qc.get("use_aim_minigame", True),
            use_heal_minigame=qc.get("use_heal_minigame", True),
            use_melee_minigame=qc.get("use_melee_minigame", True),
            heal_threshold_pct=qc.get("heal_threshold_pct", 100),
        )

    def _effective_language(self) -> str:
        if self._active_profile:
            return self._active_profile.language
        return self._global_cfg.last_quick_config.get("language", get_language())

    def _set_flag(self, name: str, value) -> None:
        if self._active_profile:
            setattr(self._active_profile.flags, name, value)
            save_profile(self._active_profile)
        else:
            self._global_cfg.last_quick_config[name] = value
            save_global(self._global_cfg)

    def _set_language(self, lang: str) -> None:
        set_language(lang)
        if self._active_profile:
            self._active_profile.language = lang
            save_profile(self._active_profile)
        else:
            self._global_cfg.last_quick_config["language"] = lang
            save_global(self._global_cfg)

    def _save_audio(self) -> None:
        self._global_cfg.master_volume = settings.MASTER_VOLUME
        self._global_cfg.music_volume  = settings.MUSIC_VOLUME
        self._global_cfg.sfx_volume    = settings.SFX_VOLUME
        save_global(self._global_cfg)
