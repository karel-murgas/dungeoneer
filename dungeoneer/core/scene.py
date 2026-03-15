"""Abstract base class for all game scenes."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

import pygame

if TYPE_CHECKING:
    from dungeoneer.core.game import GameApp


class Scene(ABC):
    def __init__(self, app: "GameApp") -> None:
        self.app = app

    @abstractmethod
    def handle_events(self, events: List[pygame.event.Event]) -> None:
        """Process raw pygame events."""

    @abstractmethod
    def update(self, dt: float) -> None:
        """Update logic. dt is seconds since last frame."""

    @abstractmethod
    def render(self, screen: pygame.Surface) -> None:
        """Draw everything to screen."""

    def on_enter(self) -> None:
        """Called when this scene becomes the active scene."""

    def on_exit(self) -> None:
        """Called when this scene is removed from the stack."""

    def on_pause(self) -> None:
        """Called when a scene is pushed on top of this one."""

    def on_resume(self) -> None:
        """Called when the scene above this one is popped."""
