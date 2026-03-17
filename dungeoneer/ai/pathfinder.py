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
    ) -> list[tuple[int, int]]:
        """Return list of (x,y) tiles from start (exclusive) to goal (inclusive).

        Returns empty list if no path found.
        """
        cost = dungeon_map.walkable.astype(np.int8)
        # Allow diagonal movement if requested
        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3 if diagonal else 0)
        pf = tcod.path.Pathfinder(graph)
        pf.add_root((start[1], start[0]))   # tcod uses (row, col)
        path_rc = pf.path_to((goal[1], goal[0]))
        # Convert back to (x, y) and skip the start tile
        return [(c, r) for r, c in path_rc[1:]]
