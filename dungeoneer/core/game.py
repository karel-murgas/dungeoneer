"""Main game application — window, loop, scene dispatch."""
from __future__ import annotations

import logging
import sys
import traceback

import pygame

from dungeoneer.core import settings
from dungeoneer.core.scene_manager import SceneManager

log = logging.getLogger(__name__)


class GameApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(settings.TITLE)
        self.screen = pygame.display.set_mode(
            (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
        )
        self.clock = pygame.time.Clock()
        self.scenes = SceneManager()
        self.running = False

    # ------------------------------------------------------------------
    # Public helpers used by scenes
    # ------------------------------------------------------------------

    def quit(self) -> None:
        log.info("GameApp.quit() called")
        self.running = False

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        from dungeoneer.scenes.game_scene import GameScene  # avoid circular

        log.info("Starting game loop")
        self.scenes.push(GameScene(self))
        self.running = True
        frame = 0

        while self.running:
            dt = self.clock.tick(settings.FPS) / 1000.0
            frame += 1

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            if not self.running:
                break

            try:
                self.scenes.handle_events(events)
                self.scenes.update(dt)
                self.scenes.render(self.screen)
            except Exception:
                log.critical(
                    "UNHANDLED EXCEPTION in frame %d (scene=%s):\n%s",
                    frame,
                    type(self.scenes.current).__name__,
                    traceback.format_exc(),
                )
                raise   # still crash visibly so the user sees it

            pygame.display.flip()

        log.info("Game loop ended after %d frames", frame)
        pygame.quit()
        sys.exit(0)
