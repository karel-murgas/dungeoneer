"""Standalone launcher for the hacking minigame.

Run from the project root:
    python main_hack.py

Optional flags (positional, any order):
    python main_hack.py easy
    python main_hack.py normal   (default)
    python main_hack.py hard

    python main_hack.py grid     (grid-traversal variant, default)
    python main_hack.py classic  (node-graph variant)

Examples:
    python main_hack.py hard grid
    python main_hack.py easy classic
"""
from dungeoneer.core.logging_setup import setup_logging
setup_logging()

import sys
import traceback

import pygame

from dungeoneer.core import settings
from dungeoneer.core.game import GameApp
from dungeoneer.core.difficulty import EASY, NORMAL, HARD


class HackApp(GameApp):
    """Thin subclass that pushes the chosen HackScene variant."""

    def __init__(self, difficulty_name: str = "normal", variant: str = "grid") -> None:
        super().__init__()
        _diff_map = {"easy": EASY, "normal": NORMAL, "hard": HARD}
        self._difficulty = _diff_map.get(difficulty_name.lower(), NORMAL)
        self._variant    = variant.lower()

    def run(self) -> None:
        import logging
        log = logging.getLogger(__name__)

        def on_complete(success: bool, items: list, credits: int) -> None:
            names = [i.name for i in items]
            print(f"\n=== HACK RESULT ===")
            print(f"  variant : {self._variant}")
            print(f"  success : {success}")
            print(f"  items   : {names}")
            print(f"  credits : {credits}")
            self.running = False

        if self._variant == "classic":
            from dungeoneer.minigame.hack_scene import HackScene
            from dungeoneer.minigame.hack_generator import HackParams
            params = HackParams.for_difficulty(self._difficulty)
            log.info("Starting CLASSIC hack  difficulty=%s  params=%s",
                     self._difficulty.name, params)
            self.scenes.push(HackScene(self, params=params, on_complete=on_complete))
        else:
            from dungeoneer.minigame.hack_scene_grid import HackGridScene
            from dungeoneer.minigame.hack_grid_generator import HackGridParams
            params = HackGridParams.for_difficulty(self._difficulty)
            log.info("Starting GRID hack  difficulty=%s  params=%s",
                     self._difficulty.name, params)
            self.scenes.push(HackGridScene(self, params=params, on_complete=on_complete))

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
    _diff_names    = {"easy", "normal", "hard"}
    _variant_names = {"classic", "grid"}

    difficulty = "normal"
    variant    = "grid"

    for arg in sys.argv[1:]:
        a = arg.lower()
        if a in _diff_names:
            difficulty = a
        elif a in _variant_names:
            variant = a

    HackApp(difficulty, variant).run()


if __name__ == "__main__":
    main()
