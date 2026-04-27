"""Game over / run summary screen."""
from __future__ import annotations

from typing import List, TYPE_CHECKING

import pygame

from dungeoneer.core.scene import Scene
from dungeoneer.core import settings
from dungeoneer.core.i18n import t
from dungeoneer.core.difficulty import Difficulty

if TYPE_CHECKING:
    from dungeoneer.core.game import GameApp

_BTN_W  = 230
_BTN_H  = 44
_BTN_NRM = (20, 40, 35)
_BTN_HOV = (35, 90, 70)
_COL_BORDER     = (60, 200, 160)
_COL_BORDER_HOV = (100, 240, 200)


class GameOverScene(Scene):
    def __init__(
        self, app: "GameApp", *, victory: bool, floor_depth: int,
        difficulty: Difficulty | None = None,
        use_minigame: bool = True,
        use_aim_minigame: bool = True,
        use_melee_minigame: bool = True,
        credits_earned: int = 0,
        credits_before: int = 0,
        profile=None,
        audio=None,
        map_size: str = "large",
    ) -> None:
        super().__init__(app)
        self.victory             = victory
        self.floor_depth         = floor_depth
        self._difficulty         = difficulty
        self._use_minigame       = use_minigame
        self._use_aim_minigame   = use_aim_minigame
        self._use_melee_minigame = use_melee_minigame
        self._map_size           = map_size
        self._credits_earned  = credits_earned
        self._credits_before  = credits_before
        self._profile         = profile
        self._audio           = audio
        self._font_big   = pygame.font.SysFont("consolas", 52, bold=True)
        self._font_med   = pygame.font.SysFont("consolas", 26)
        self._font_small = pygame.font.SysFont("consolas", 18)
        self._font_btn   = pygame.font.SysFont("consolas", 18, bold=True)
        # Button rects populated in render(); used for mouse hit-testing
        self._btn_menu: pygame.Rect | None = None
        self._btn_quit: pygame.Rect | None = None
        self._hovered: str | None = None   # "menu" | "quit" | None

    def on_enter(self) -> None:
        if self._audio:
            self._audio.play("victory" if self.victory else "defeat", volume=0.85)

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_r, pygame.K_RETURN, pygame.K_SPACE):
                    self._go_to_menu()
                elif event.key == pygame.K_ESCAPE:
                    self.app.quit()

            elif event.type == pygame.MOUSEMOTION:
                hov = None
                if self._btn_menu and self._btn_menu.collidepoint(event.pos):
                    hov = "menu"
                elif self._btn_quit and self._btn_quit.collidepoint(event.pos):
                    hov = "quit"
                self._hovered = hov

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._btn_menu and self._btn_menu.collidepoint(event.pos):
                    self._go_to_menu()
                elif self._btn_quit and self._btn_quit.collidepoint(event.pos):
                    self.app.quit()

    def update(self, dt: float) -> None:
        pass

    def render(self, screen: pygame.Surface) -> None:
        screen.fill((8, 8, 16))
        sw, sh = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT

        if self.victory:
            title  = t("gameover.victory")
            colour = (0, 220, 180)
            sub    = t("gameover.victory_sub")
        else:
            title  = t("gameover.defeat")
            colour = (220, 60, 60)
            sub    = t("gameover.defeat_sub")

        t_surf = self._font_big.render(title, True, colour)
        screen.blit(t_surf, (sw // 2 - t_surf.get_width() // 2, sh // 3))

        s_surf = self._font_med.render(sub, True, (180, 180, 180))
        screen.blit(s_surf, (sw // 2 - s_surf.get_width() // 2, sh // 3 + 70))

        depth_surf = self._font_small.render(
            t("gameover.floors").format(n=self.floor_depth), True, (120, 120, 140)
        )
        screen.blit(depth_surf, (sw // 2 - depth_surf.get_width() // 2, sh // 3 + 110))

        cr_colour = (80, 220, 120) if self._credits_earned > 0 else (100, 100, 120)
        cr_surf = self._font_med.render(
            t("gameover.credits").format(n=self._credits_earned), True, cr_colour
        )
        screen.blit(cr_surf, (sw // 2 - cr_surf.get_width() // 2, sh // 3 + 148))

        if self._profile is not None:
            pool = self._credits_before + self._credits_earned
            pool_surf = self._font_small.render(
                t("gameover.credits_pool").format(n=pool), True, (100, 160, 130)
            )
            screen.blit(pool_surf, (sw // 2 - pool_surf.get_width() // 2, sh // 3 + 186))

        # --- Buttons ---
        btn_y = sh * 2 // 3
        gap   = 24

        self._btn_menu = pygame.Rect(
            sw // 2 - _BTN_W - gap // 2, btn_y, _BTN_W, _BTN_H
        )
        self._btn_quit = pygame.Rect(
            sw // 2 + gap // 2, btn_y, _BTN_W, _BTN_H
        )

        for btn, key, label in (
            (self._btn_menu, "menu", t("gameover.menu")),
            (self._btn_quit, "quit", t("gameover.quit")),
        ):
            is_hov = self._hovered == key
            pygame.draw.rect(screen, _BTN_HOV if is_hov else _BTN_NRM, btn, border_radius=4)
            pygame.draw.rect(screen, _COL_BORDER_HOV if is_hov else _COL_BORDER,
                             btn, 2, border_radius=4)
            lbl = self._font_btn.render(label, True,
                                        (220, 255, 240) if is_hov else (140, 180, 160))
            screen.blit(lbl, (btn.centerx - lbl.get_width() // 2,
                               btn.centery - lbl.get_height() // 2))

    def _go_to_menu(self) -> None:
        if self._profile is not None:
            from dungeoneer.meta.storage import load_global
            from dungeoneer.scenes.meta_scene import MetaScene
            self.app.scenes.replace(MetaScene(self.app, self._profile, load_global()))
        else:
            from dungeoneer.scenes.main_menu_scene import MainMenuScene
            self.app.scenes.replace(MainMenuScene(self.app))
