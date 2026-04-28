"""Between-runs hub scene.

Shown after profile selection (Continue / New Game / Load / Quick Game) before
starting a run.  Provides top-level navigation and a prominent Start Run button.

Layout:
  Top nav bar:  [Game v]  [Preferences]  [Help]  [Statistics]
  Main area:    AGENT label + profile name + difficulty + [START RUN]
"""
from __future__ import annotations

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
    load_global, save_global, load_profile, save_profile, delete_profile,
)
from dungeoneer.rendering.ui.quit_confirm import QuitConfirmDialog
from dungeoneer.rendering.ui.settings_overlay import SettingsOverlay
from dungeoneer.rendering.ui.help_catalog import HelpCatalogOverlay
from dungeoneer.rendering.ui.new_game_wizard import NewGameWizard
from dungeoneer.rendering.ui.load_game_picker import LoadGamePicker
from dungeoneer.rendering.ui.statistics_overlay import StatisticsOverlay

if TYPE_CHECKING:
    from dungeoneer.core.game import GameApp

_DIFF_MAP: dict[str, Difficulty] = {"easy": EASY, "normal": NORMAL, "hard": HARD}

# ---------------------------------------------------------------------------
# Visual constants
# ---------------------------------------------------------------------------

_BG           = (8, 8, 16)
_COL_ACCENT   = (0, 220, 180)
_COL_LABEL    = (70, 100, 90)
_COL_PROFILE  = (190, 245, 225)
_COL_DIFF     = (60, 140, 120)

_NAV_BG       = (11, 16, 26)
_NAV_BDR      = (28, 52, 48)
_NAV_NRM      = (110, 145, 135)
_NAV_HOV      = (200, 240, 220)
_NAV_SEL      = (0, 220, 180)
_NAV_H        = 44

_DROP_BG      = (10, 16, 24, 245)
_DROP_BDR     = (55, 190, 155)
_DROP_ROW_H   = 32
_DROP_TXT     = (155, 185, 175)
_DROP_HOV_BG  = (22, 52, 42, 210)
_DROP_HOV_TXT = (220, 255, 240)
_DROP_DNG     = (195, 75, 75)
_DROP_DNG_HOV = (250, 115, 95)
_DROP_SEP     = (28, 52, 48)

_BTN_BG       = (14, 68, 54)
_BTN_HOV      = (18, 95, 72)
_BTN_BDR      = (0, 195, 158)
_BTN_BDR_HOV  = (55, 235, 195)
_BTN_TXT      = (215, 255, 240)

_DROP_W = 190
_DROP_PAD = 8


class MetaScene(Scene):
    def __init__(
        self,
        app: "GameApp",
        profile: Profile | None,
        global_cfg: GlobalConfig,
    ) -> None:
        super().__init__(app)
        self._profile        = profile
        self._global_cfg     = global_cfg
        self._active_profile = profile   # alias consumed by SettingsOverlay / StatisticsOverlay

        # Fonts
        self._font_nav   = pygame.font.SysFont("consolas", 14, bold=True)
        self._font_drop  = pygame.font.SysFont("consolas", 14)
        self._font_label = pygame.font.SysFont("consolas", 13)
        self._font_name  = pygame.font.SysFont("consolas", 38, bold=True)
        self._font_diff  = pygame.font.SysFont("consolas", 14)
        self._font_btn   = pygame.font.SysFont("consolas", 18, bold=True)

        # Overlay / menu flags
        self._game_menu_open      = False
        self._settings_open       = False
        self._help_open           = False
        self._statistics_open     = False
        self._wizard_open         = False
        self._load_open           = False
        self._delete_confirm_open = False
        self._quit_confirm_open   = False

        # Overlay instances
        self._settings_overlay   = SettingsOverlay(self)
        self._help_overlay       = HelpCatalogOverlay()
        self._statistics_overlay = StatisticsOverlay(self)
        self._wizard             = NewGameWizard(self)
        self._load_picker        = LoadGamePicker(self)
        self._delete_confirm     = QuitConfirmDialog("meta.delete")
        self._quit_confirm       = QuitConfirmDialog("exit_confirm")

        # Hit-test rects (populated each render pass)
        self._nav_rects:  dict[str, pygame.Rect] = {}
        self._drop_rects: dict[str, pygame.Rect] = {}
        self._btn_rects:  dict[str, pygame.Rect] = {}
        self._hovered: str | None = None

    # ------------------------------------------------------------------
    # Scene lifecycle
    # ------------------------------------------------------------------

    def on_enter(self) -> None:
        self._global_cfg = load_global()
        settings.MASTER_VOLUME = self._global_cfg.master_volume
        settings.MUSIC_VOLUME  = self._global_cfg.music_volume
        settings.SFX_VOLUME    = self._global_cfg.sfx_volume
        if self._profile:
            set_language(self._profile.language)
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
        if self._quit_confirm_open:
            result = self._quit_confirm.handle_key(key)
            if result == "confirm":
                self.app.quit()
            elif result == "cancel":
                self._quit_confirm_open = False
            return
        if self._delete_confirm_open:
            result = self._delete_confirm.handle_key(key)
            if result == "confirm":
                self._do_delete()
            elif result == "cancel":
                self._delete_confirm_open = False
            return
        if self._wizard_open:
            if self._wizard.handle_key(key):
                self._close_wizard()
            return
        if self._load_open:
            if self._load_picker.handle_key(key):
                self._load_open = False
            return
        if self._settings_open:
            if self._settings_overlay.handle_key(key):
                self._settings_open = False
            return
        if self._help_open:
            if self._help_overlay.handle_key(key):
                self._help_open = False
            return
        if self._statistics_open:
            if self._statistics_overlay.handle_key(key):
                self._statistics_open = False
            return
        if key == pygame.K_ESCAPE:
            self._game_menu_open = False
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            if not self._game_menu_open:
                self._start_run()
        elif key == pygame.K_F3 and self._profile is not None:
            self._close_soft_overlays()
            self._statistics_overlay.open()
            self._statistics_open = True
        elif key == pygame.K_F1:
            self._close_soft_overlays()
            self._help_open = True

    def _handle_motion(self, pos: tuple) -> None:
        if self._quit_confirm_open:
            self._quit_confirm.handle_mouse_motion(pos)
        elif self._delete_confirm_open:
            self._delete_confirm.handle_mouse_motion(pos)
        elif self._wizard_open:
            self._wizard.handle_motion(pos)
        elif self._load_open:
            self._load_picker.handle_motion(pos)
        elif self._settings_open:
            self._settings_overlay.handle_motion(pos)
            self._hovered = self._hit_test_nav(pos)
        elif self._help_open:
            self._help_overlay.handle_motion(pos)
            self._hovered = self._hit_test_nav(pos)
        elif self._statistics_open:
            self._statistics_overlay.handle_motion(pos)
            self._hovered = self._hit_test_nav(pos)
        else:
            self._hovered = self._hit_test(pos)

    def _handle_click(self, event: pygame.event.Event) -> None:
        pos = event.pos
        # Hard modals consume all input
        if self._quit_confirm_open:
            result = self._quit_confirm.handle_mouse_button(event)
            if result == "confirm":
                self.app.quit()
            elif result == "cancel":
                self._quit_confirm_open = False
            return
        if self._delete_confirm_open:
            result = self._delete_confirm.handle_mouse_button(event)
            if result == "confirm":
                self._do_delete()
            elif result == "cancel":
                self._delete_confirm_open = False
            return
        if self._wizard_open:
            if self._wizard.handle_click(pos):
                self._close_wizard()
            return
        if self._load_open:
            if self._load_picker.handle_click(pos):
                self._load_open = False
            return
        # Nav click always takes priority over soft overlays
        nav_hit = self._hit_test_nav(pos)
        if nav_hit:
            self._close_soft_overlays()
            self._dispatch(nav_hit)
            return
        # Soft overlay handling
        if self._settings_open:
            if self._settings_overlay.handle_click(pos):
                self._settings_open = False
            return
        if self._help_open:
            if self._help_overlay.handle_click(pos):
                self._help_open = False
            return
        if self._statistics_open:
            if self._statistics_overlay.handle_click(pos):
                self._statistics_open = False
            return
        if self._game_menu_open:
            hit = self._drop_hit(pos)
            if hit:
                self._dispatch_drop(hit)
            else:
                self._game_menu_open = False
            return
        hit = self._hit_test(pos)
        if hit:
            self._dispatch(hit)

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
        self._nav_rects  = {}
        self._drop_rects = {}
        self._btn_rects  = {}

        any_modal = (self._settings_open or self._help_open or self._statistics_open
                     or self._wizard_open or self._load_open or self._delete_confirm_open
                     or self._quit_confirm_open)
        hard_modal = (self._wizard_open or self._load_open
                      or self._delete_confirm_open or self._quit_confirm_open)

        # ── Nav bar ──────────────────────────────────────────────────
        pygame.draw.rect(screen, _NAV_BG, (0, 0, sw, _NAV_H))
        pygame.draw.line(screen, _NAV_BDR, (0, _NAV_H), (sw, _NAV_H))

        nav_items = [
            ("nav_game",  t("meta.nav.game")),
            ("nav_prefs", t("meta.nav.prefs")),
            ("nav_help",  t("meta.nav.help")),
            ("nav_stats", t("meta.nav.stats")),
        ]
        nx = 20
        for key, label in nav_items:
            active = (
                (key == "nav_game"  and self._game_menu_open)
                or (key == "nav_prefs" and self._settings_open)
                or (key == "nav_help"  and self._help_open)
                or (key == "nav_stats" and self._statistics_open)
            )
            hov = self._hovered == key and not hard_modal
            col = _NAV_SEL if active else (_NAV_HOV if hov else _NAV_NRM)
            surf = self._font_nav.render(label, True, col)
            rect = pygame.Rect(nx, (_NAV_H - surf.get_height()) // 2,
                               surf.get_width() + 18, surf.get_height() + 6)
            self._nav_rects[key] = rect
            screen.blit(surf, (rect.x + 9, rect.y + 3))
            if active:
                pygame.draw.line(screen, _NAV_SEL,
                                 (rect.x, _NAV_H - 2),
                                 (rect.right, _NAV_H - 2), 2)
            nx += rect.width + 4

        # ── Main content ─────────────────────────────────────────────
        cx = sw // 2
        area_top = _NAV_H + 20
        area_h   = sh - area_top
        mid_y    = area_top + area_h // 2

        btn_h = 54
        btn_w = 280

        if self._profile:
            diff_map = {
                "easy":   t("menu.easy"),
                "normal": t("menu.normal"),
                "hard":   t("menu.hard"),
            }
            diff_str = diff_map.get(self._profile.difficulty,
                                    self._profile.difficulty).upper()

            lbl_surf     = self._font_label.render(t("meta.agent"), True, _COL_LABEL)
            name_surf    = self._font_name.render(self._profile.name, True, _COL_PROFILE)
            diff_surf    = self._font_diff.render(diff_str, True, _COL_DIFF)
            credits_surf = self._font_diff.render(
                t("meta.credits").format(n=self._profile.credits), True, _COL_DIFF
            )

            block_h = (lbl_surf.get_height() + 4
                       + name_surf.get_height() + 6
                       + diff_surf.get_height() + 4
                       + credits_surf.get_height())
            total_h = block_h + 28 + btn_h
            y = mid_y - total_h // 2

            screen.blit(lbl_surf,     (cx - lbl_surf.get_width()     // 2, y))
            y += lbl_surf.get_height() + 4
            screen.blit(name_surf,    (cx - name_surf.get_width()    // 2, y))
            y += name_surf.get_height() + 6
            screen.blit(diff_surf,    (cx - diff_surf.get_width()    // 2, y))
            y += diff_surf.get_height() + 4
            screen.blit(credits_surf, (cx - credits_surf.get_width() // 2, y))
            y += credits_surf.get_height() + 28
        else:
            guest_surf = self._font_name.render(t("meta.guest"), True, _COL_LABEL)
            total_h = guest_surf.get_height() + 28 + btn_h
            y = mid_y - total_h // 2
            screen.blit(guest_surf, (cx - guest_surf.get_width() // 2, y))
            y += guest_surf.get_height() + 28

        btn_rect = pygame.Rect(cx - btn_w // 2, y, btn_w, btn_h)
        self._btn_rects["start_run"] = btn_rect
        hov_btn = self._hovered == "start_run" and not any_modal and not self._game_menu_open
        pygame.draw.rect(screen, _BTN_HOV if hov_btn else _BTN_BG, btn_rect, border_radius=6)
        pygame.draw.rect(screen, _BTN_BDR_HOV if hov_btn else _BTN_BDR, btn_rect, 2, border_radius=6)
        lbl_s = self._font_btn.render(t("meta.start_run"), True, _BTN_TXT)
        screen.blit(lbl_s, (btn_rect.centerx - lbl_s.get_width() // 2,
                             btn_rect.centery - lbl_s.get_height() // 2 + 1))

        # ── Game dropdown ─────────────────────────────────────────────
        if self._game_menu_open:
            self._draw_game_dropdown(screen)

        # ── Overlays ──────────────────────────────────────────────────
        if self._quit_confirm_open:
            self._quit_confirm.draw(screen)
        elif self._delete_confirm_open:
            self._delete_confirm.draw(screen)
        elif self._wizard_open:
            self._wizard.draw(screen)
        elif self._load_open:
            self._load_picker.draw(screen)
        elif self._settings_open:
            self._settings_overlay.draw(screen)
        elif self._help_open:
            self._help_overlay.draw(screen)
        elif self._statistics_open:
            self._statistics_overlay.draw(screen)

    def _draw_game_dropdown(self, screen: pygame.Surface) -> None:
        self._drop_rects = {}
        items: list[tuple[str, str, tuple]] = [
            ("drop_new",    t("meta.game.new"),    _DROP_TXT),
            ("drop_load",   t("meta.game.load"),   _DROP_TXT),
            None,   # separator
            ("drop_delete", t("meta.game.delete"), _DROP_DNG),
            ("drop_quit",   t("meta.game.quit"),   _DROP_TXT),
        ]
        if not self._profile:
            items = [i for i in items if i is None or i[0] != "drop_delete"]

        sep_h = 9
        row_count = sum(1 for i in items if i is not None)
        sep_count = sum(1 for i in items if i is None)
        drop_h = _DROP_PAD + row_count * _DROP_ROW_H + sep_count * sep_h + _DROP_PAD

        nav_rect = self._nav_rects.get("nav_game")
        dx = nav_rect.x if nav_rect else 20
        dy = _NAV_H + 1

        panel = pygame.Surface((_DROP_W, drop_h), pygame.SRCALPHA)
        panel.fill(_DROP_BG)
        screen.blit(panel, (dx, dy))
        pygame.draw.rect(screen, _DROP_BDR, (dx, dy, _DROP_W, drop_h), 1, border_radius=3)

        iy = dy + _DROP_PAD
        for item in items:
            if item is None:
                pygame.draw.line(screen, _DROP_SEP,
                                 (dx + 12, iy + sep_h // 2),
                                 (dx + _DROP_W - 12, iy + sep_h // 2))
                iy += sep_h
                continue
            key, label, base_col = item
            rect = pygame.Rect(dx + 1, iy, _DROP_W - 2, _DROP_ROW_H)
            self._drop_rects[key] = rect
            hov = self._hovered == key
            if hov:
                hov_s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                hov_s.fill(_DROP_HOV_BG)
                screen.blit(hov_s, rect.topleft)
            if base_col == _DROP_DNG:
                col = _DROP_DNG_HOV if hov else _DROP_DNG
            else:
                col = _DROP_HOV_TXT if hov else base_col
            lbl = self._font_drop.render(label, True, col)
            screen.blit(lbl, (rect.x + 12,
                               rect.centery - lbl.get_height() // 2 + 1))
            iy += _DROP_ROW_H

    # ------------------------------------------------------------------
    # Hit testing
    # ------------------------------------------------------------------

    def _hit_test(self, pos: tuple) -> str | None:
        for key, rect in self._nav_rects.items():
            if rect.collidepoint(pos):
                return key
        if self._game_menu_open:
            for key, rect in self._drop_rects.items():
                if rect.collidepoint(pos):
                    return key
        for key, rect in self._btn_rects.items():
            if rect.collidepoint(pos):
                return key
        return None

    def _hit_test_nav(self, pos: tuple) -> str | None:
        for key, rect in self._nav_rects.items():
            if rect.collidepoint(pos):
                return key
        return None

    def _close_soft_overlays(self) -> None:
        self._settings_open   = False
        self._help_open       = False
        self._statistics_open = False
        self._game_menu_open  = False

    def _drop_hit(self, pos: tuple) -> str | None:
        for key, rect in self._drop_rects.items():
            if rect.collidepoint(pos):
                return key
        return None

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def _dispatch(self, hit: str) -> None:
        # _close_soft_overlays() is already called before nav dispatches from _handle_click,
        # so we just open the requested panel (if not already active — toggling is handled
        # by _close_soft_overlays having already cleared the flag before we set it again).
        if hit == "nav_game":
            self._game_menu_open = not self._game_menu_open
        elif hit == "nav_prefs":
            self._settings_open = True
        elif hit == "nav_help":
            self._help_open = True
        elif hit == "nav_stats":
            if self._profile:
                self._statistics_overlay.open()
                self._statistics_open = True
        elif hit == "start_run":
            self._start_run()

    def _dispatch_drop(self, hit: str) -> None:
        self._game_menu_open = False
        if hit == "drop_new":
            self._open_wizard()
        elif hit == "drop_load":
            self._load_picker.refresh()
            self._load_open = True
        elif hit == "drop_delete" and self._profile:
            self._delete_confirm_open = True
        elif hit == "drop_quit":
            self._quit_confirm_open = True

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _start_run(self) -> None:
        from dungeoneer.scenes.game_scene import GameScene
        if self._profile:
            set_language(self._profile.language)
            diff_obj = _DIFF_MAP.get(self._profile.difficulty, NORMAL)
            flags    = self._profile.flags
            self.app.scenes.replace(GameScene(
                self.app,
                difficulty=diff_obj,
                use_minigame=flags.use_minigame,
                use_aim_minigame=flags.use_aim_minigame,
                use_heal_minigame=flags.use_heal_minigame,
                use_melee_minigame=flags.use_melee_minigame,
                heal_threshold_pct=flags.heal_threshold_pct,
                use_tutorial=self._profile.tutorial_enabled,
                map_size="large",
                player_name=self._profile.name,
                tutorial_seen=list(self._profile.tutorial_seen),
                profile=self._profile,
            ))
        else:
            qc = self._global_cfg.last_quick_config
            diff_obj = _DIFF_MAP.get(qc.get("difficulty", "normal"), NORMAL)
            self.app.scenes.replace(GameScene(
                self.app,
                difficulty=diff_obj,
                use_minigame=qc.get("use_minigame", True),
                use_aim_minigame=qc.get("use_aim_minigame", True),
                use_heal_minigame=qc.get("use_heal_minigame", True),
                use_melee_minigame=qc.get("use_melee_minigame", True),
                heal_threshold_pct=qc.get("heal_threshold_pct", 100),
                use_tutorial=qc.get("tutorial", False),
                map_size="large",
                player_name=None,
                profile=None,
            ))

    def _go_to_menu(self) -> None:
        from dungeoneer.scenes.main_menu_scene import MainMenuScene
        self.app.scenes.replace(MainMenuScene(self.app))

    def _do_delete(self) -> None:
        if self._profile:
            delete_profile(self._profile.name)
            if self._global_cfg.last_active_profile == self._profile.name:
                self._global_cfg.last_active_profile = None
                save_global(self._global_cfg)
        self._delete_confirm_open = False
        self._go_to_menu()

    # ------------------------------------------------------------------
    # Wizard / picker callbacks (called by overlay instances)
    # ------------------------------------------------------------------

    def _open_wizard(self) -> None:
        self._wizard.reset()
        self._wizard_open = True
        pygame.key.start_text_input()

    def _close_wizard(self) -> None:
        self._wizard_open = False
        pygame.key.stop_text_input()

    def _wizard_done(self, profile: Profile) -> None:
        """NewGameWizard callback — switch to the newly created profile."""
        self._global_cfg.last_active_profile = profile.name
        save_global(self._global_cfg)
        self._close_wizard()
        self._profile        = profile
        self._active_profile = profile

    def _load_game_done(self, name: str) -> None:
        """LoadGamePicker callback — switch to the loaded profile."""
        profile = load_profile(name)
        if profile is None:
            return
        self._global_cfg.last_active_profile = name
        save_global(self._global_cfg)
        self._load_open      = False
        self._profile        = profile
        self._active_profile = profile
        set_language(profile.language)

    # ------------------------------------------------------------------
    # SettingsOverlay helpers
    # ------------------------------------------------------------------

    def _effective_flags(self) -> GameplayFlags:
        if self._profile:
            return self._profile.flags
        qc = self._global_cfg.last_quick_config
        return GameplayFlags(
            use_minigame=qc.get("use_minigame", True),
            use_aim_minigame=qc.get("use_aim_minigame", True),
            use_heal_minigame=qc.get("use_heal_minigame", True),
            use_melee_minigame=qc.get("use_melee_minigame", True),
            heal_threshold_pct=qc.get("heal_threshold_pct", 100),
        )

    def _effective_language(self) -> str:
        if self._profile:
            return self._profile.language
        return self._global_cfg.last_quick_config.get("language", get_language())

    def _set_flag(self, name: str, value) -> None:
        if self._profile:
            setattr(self._profile.flags, name, value)
            save_profile(self._profile)
        else:
            self._global_cfg.last_quick_config[name] = value
            save_global(self._global_cfg)

    def _set_language(self, lang: str) -> None:
        set_language(lang)
        if self._profile:
            self._profile.language = lang
            save_profile(self._profile)
        else:
            self._global_cfg.last_quick_config["language"] = lang
            save_global(self._global_cfg)

    def _save_audio(self) -> None:
        self._global_cfg.master_volume = settings.MASTER_VOLUME
        self._global_cfg.music_volume  = settings.MUSIC_VOLUME
        self._global_cfg.sfx_volume    = settings.SFX_VOLUME
        save_global(self._global_cfg)
        try:
            pygame.mixer.music.set_volume(settings.MASTER_VOLUME * settings.MUSIC_VOLUME)
        except Exception:
            pass
