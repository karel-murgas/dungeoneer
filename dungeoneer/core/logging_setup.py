"""Configure file-based logging for Dungeoneer."""
from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path


LOG_FILE = Path(__file__).resolve().parents[2] / "dungeoneer.log"


def setup_logging(level: int = logging.DEBUG) -> None:
    root = logging.getLogger()
    if root.handlers:
        return   # already configured

    root.setLevel(level)
    fmt = logging.Formatter(
        "%(asctime)s.%(msecs)03d  %(levelname)-7s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )

    # Rotating file handler — keeps last 2 MB so the file doesn't grow forever
    fh = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=1, encoding="utf-8"
    )
    fh.setLevel(level)
    fh.setFormatter(fmt)
    root.addHandler(fh)

    # Brief console handler (warnings and above only — don't spam the terminal)
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    ch.setFormatter(fmt)
    root.addHandler(ch)

    root.info("=== Dungeoneer started ===  log → %s", LOG_FILE)
