"""Scene stack manager."""
from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from dungeoneer.core.scene import Scene


class SceneManager:
    def __init__(self) -> None:
        self._stack: List["Scene"] = []

    @property
    def current(self) -> Optional["Scene"]:
        return self._stack[-1] if self._stack else None

    def push(self, scene: "Scene") -> None:
        if self.current:
            self.current.on_pause()
        self._stack.append(scene)
        scene.on_enter()

    def pop(self) -> None:
        if not self._stack:
            return
        self._stack.pop().on_exit()
        if self.current:
            self.current.on_resume()

    def replace(self, scene: "Scene") -> None:
        if self._stack:
            self._stack.pop().on_exit()
        self._stack.append(scene)
        scene.on_enter()

    def clear(self) -> None:
        while self._stack:
            self._stack.pop().on_exit()

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        if self.current:
            self.current.handle_events(events)

    def update(self, dt: float) -> None:
        if self.current:
            self.current.update(dt)

    def render(self, screen: pygame.Surface) -> None:
        if self.current:
            self.current.render(screen)
