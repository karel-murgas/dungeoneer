"""Game over / run summary screen."""
from __future__ import annotations

from typing import List, TYPE_CHECKING

import pygame

from dungeoneer.core.scene import Scene
from dungeoneer.core import settings

if TYPE_CHECKING:
    from dungeoneer.core.game import GameApp


class GameOverScene(Scene):
    def __init__(
        self, app: "GameApp", *, victory: bool, floor_depth: int,
        difficulty=None, credits_earned: int = 0,
    ) -> None:
        super().__init__(app)
        self.victory         = victory
        self.floor_depth     = floor_depth
        self._difficulty     = difficulty
        self._credits_earned = credits_earned
        self._font_big       = pygame.font.SysFont("consolas", 52, bold=True)
        self._font_med       = pygame.font.SysFont("consolas", 26)
        self._font_small     = pygame.font.SysFont("consolas", 18)

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_r, pygame.K_RETURN, pygame.K_SPACE):
                    self._restart()
                elif event.key == pygame.K_ESCAPE:
                    self.app.quit()

    def update(self, dt: float) -> None:
        pass

    def render(self, screen: pygame.Surface) -> None:
        screen.fill((8, 8, 16))
        sw, sh = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT

        if self.victory:
            title = "EXTRACTION COMPLETE"
            colour = (0, 220, 180)
            sub = "You made it out alive."
        else:
            title = "KILLED IN ACTION"
            colour = (220, 60, 60)
            sub = "Your signal has gone dark."

        t_surf = self._font_big.render(title, True, colour)
        screen.blit(t_surf, (sw // 2 - t_surf.get_width() // 2, sh // 3))

        s_surf = self._font_med.render(sub, True, (180, 180, 180))
        screen.blit(s_surf, (sw // 2 - s_surf.get_width() // 2, sh // 3 + 70))

        depth_surf = self._font_small.render(
            f"Floors cleared: {self.floor_depth - 1}", True, (120, 120, 140)
        )
        screen.blit(depth_surf, (sw // 2 - depth_surf.get_width() // 2, sh // 3 + 110))

        cr_colour = (80, 220, 120) if self._credits_earned > 0 else (100, 100, 120)
        cr_surf = self._font_med.render(
            f"Credits earned: {self._credits_earned} cr", True, cr_colour
        )
        screen.blit(cr_surf, (sw // 2 - cr_surf.get_width() // 2, sh // 3 + 148))

        hint = self._font_small.render(
            "[R / Enter] Run again    [Esc] Quit", True, (80, 80, 100)
        )
        screen.blit(hint, (sw // 2 - hint.get_width() // 2, sh * 2 // 3))

    def _restart(self) -> None:
        from dungeoneer.scenes.game_scene import GameScene
        self.app.scenes.replace(GameScene(self.app, difficulty=self._difficulty) if self._difficulty else GameScene(self.app))
