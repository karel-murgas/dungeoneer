"""Base Entity class."""
from __future__ import annotations

import itertools

_id_counter = itertools.count(1)


class Entity:
    def __init__(self, x: int, y: int, name: str, render_colour: tuple) -> None:
        self.uid = next(_id_counter)
        self.x = x
        self.y = y
        self.name = name
        self.render_colour = render_colour  # fallback placeholder colour
