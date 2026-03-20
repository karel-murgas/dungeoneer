"""A* pathfinder using tcod."""
from __future__ import annotations

import numpy as np
import tcod

from dungeoneer.world.map import DungeonMap


class Pathfinder:
    def find_path(
        self,
        start: tuple[int, int],
        goal: tuple[int, int],
        dungeon_map: DungeonMap,
        *,
        diagonal: bool = False,
        extra_blocked: list[tuple[int, int]] | None = None,
    ) -> list[tuple[int, int]]:
        """Return list of (x,y) tiles from start (exclusive) to goal (inclusive).

        Returns empty list if no path found.
        extra_blocked: additional (x,y) positions to treat as impassable (e.g. containers).
        """
        cost = dungeon_map.walkable.astype(np.int8)
        if extra_blocked:
            for bx, by in extra_blocked:
                if 0 <= by < cost.shape[0] and 0 <= bx < cost.shape[1]:
                    cost[by, bx] = 0
        # Allow diagonal movement if requested
        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3 if diagonal else 0)
        pf = tcod.path.Pathfinder(graph)
        pf.add_root((start[1], start[0]))   # tcod uses (row, col)
        path_rc = pf.path_to((goal[1], goal[0]))
        # Convert back to (x, y) and skip the start tile
        return [(c, r) for r, c in path_rc[1:]]
