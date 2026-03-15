"""Entry point for Dungeoneer."""
from dungeoneer.core.logging_setup import setup_logging
setup_logging()

from dungeoneer.core.game import GameApp


def main() -> None:
    app = GameApp()
    app.run()


if __name__ == "__main__":
    main()
