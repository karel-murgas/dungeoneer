"""Room dataclass used by the dungeon generator."""
from __future__ import annotations
from dataclasses import dataclass
import random


@dataclass
class Room:
    x: int          # top-left tile column
    y: int          # top-left tile row
    w: int          # width in tiles (including walls)
    h: int          # height in tiles (including walls)

    @property
    def inner_x(self) -> int:
        return self.x + 1

    @property
    def inner_y(self) -> int:
        return self.y + 1

    @property
    def inner_w(self) -> int:
        return self.w - 2

    @property
    def inner_h(self) -> int:
        return self.h - 2

    @property
    def cx(self) -> int:
        return self.x + self.w // 2

    @property
    def cy(self) -> int:
        return self.y + self.h // 2

    def random_inner_point(self) -> tuple[int, int]:
        return (
            random.randint(self.inner_x, self.inner_x + self.inner_w - 1),
            random.randint(self.inner_y, self.inner_y + self.inner_h - 1),
        )

    def intersects(self, other: "Room") -> bool:
        return (
            self.x < other.x + other.w
            and self.x + self.w > other.x
            and self.y < other.y + other.h
            and self.y + self.h > other.y
        )
