"""Standalone launcher for the hacking minigame.

Run from the project root:
    python main_hack.py

Optional difficulty flag:
    python main_hack.py easy
    python main_hack.py normal   (default)
    python main_hack.py hard
"""
from dungeoneer.core.logging_setup import setup_logging
setup_logging()

import sys
import traceback

import pygame

from dungeoneer.core import settings
from dungeoneer.core.game import GameApp
from dungeoneer.core.difficulty import EASY, NORMAL, HARD
from dungeoneer.minigame.hack_scene import HackScene
from dungeoneer.minigame.hack_generator import HackParams


class HackApp(GameApp):
    """Thin subclass that pushes HackScene instead of GameScene."""

    def __init__(self, difficulty_name: str = "normal") -> None:
        super().__init__()
        _map = {"easy": EASY, "normal": NORMAL, "hard": HARD}
        self._difficulty = _map.get(difficulty_name.lower(), NORMAL)

    def run(self) -> None:
        import logging
        log = logging.getLogger(__name__)

        params = HackParams.for_difficulty(self._difficulty)
        log.info("Starting hack minigame  difficulty=%s  params=%s",
                 self._difficulty.name, params)

        def on_complete(success: bool, items: list, credits: int) -> None:
            names = [i.name for i in items]
            print(f"\n=== HACK RESULT ===")
            print(f"  success : {success}")
            print(f"  items   : {names}")
            print(f"  credits : {credits}")
            self.running = False

        self.scenes.push(HackScene(self, params=params, on_complete=on_complete))
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
                    "UNHANDLED EXCEPTION in frame %d:\n%s",
                    frame, traceback.format_exc(),
                )
                raise

            pygame.display.flip()

        pygame.quit()
        sys.exit(0)


def main() -> None:
    difficulty = sys.argv[1] if len(sys.argv) > 1 else "normal"
    HackApp(difficulty).run()


if __name__ == "__main__":
    main()
