"""Data model for the grid-based hacking minigame (maze-grid variant).

Physical grid uses a 2× scaling of a logical node grid:
  - Even physical coordinates  → node positions (rendered as circles)
  - Odd  physical coordinates  → corridor cells  (rendered as line segments)

Movement is edge-based: only cells with an explicit connection in `connections`
can be traversed between.  This prevents jumping between parallel corridors.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import auto, Enum
from typing import Dict, List, Optional, Set, Tuple

from dungeoneer.minigame.hack_node import LootKind, SecurityKind


class GridCellType(Enum):
    ENTRY    = auto()
    PATH     = auto()   # corridor segment (not a node)
    EMPTY    = auto()   # waypoint / junction node — no loot
    LOOT     = auto()
    SECURITY = auto()


Pos = Tuple[int, int]  # (col, row) — physical grid coordinates


@dataclass
class GridCell:
    col: int
    row: int
    cell_type: GridCellType

    loot_kind:     Optional[LootKind]     = None
    security_kind: Optional[SecurityKind] = None

    hacked:   bool  = False   # LOOT collected; or SECURITY triggered
    revealed: bool  = True    # SECURITY: False = hidden (looks like EMPTY)
    active:   bool  = True    # LOOT: False = destroyed by ICE (still walkable)

    flash_timer: float = 0.0  # >0 → red flash (BLOCKED)


@dataclass
class HackGridMap:
    """The complete grid map for the maze-grid hack minigame."""

    logical_cols: int           # number of logical node columns  (e.g. 11)
    logical_rows: int           # number of logical node rows     (e.g. 7)
    cells:        Dict[Pos, GridCell]       # all walkable cells
    connections:  Dict[Pos, Set[Pos]]       # movement graph (explicit edges)
    entry_pos:    Pos                       # physical position of entry node
    loot_positions:     List[Pos]           # physical positions of loot nodes
    security_positions: List[Pos]           # physical positions of security cells
    node_positions:     Set[Pos]            # physical positions rendered as circles

    @property
    def phys_cols(self) -> int:
        """Total physical columns (0 .. 2*(logical_cols-1))."""
        return self.logical_cols * 2 - 1

    @property
    def phys_rows(self) -> int:
        return self.logical_rows * 2 - 1

    def is_walkable(self, col: int, row: int) -> bool:
        return (col, row) in self.cells

    def neighbors(self, col: int, row: int) -> List[Pos]:
        """Return only explicitly connected adjacent cells."""
        return list(self.connections.get((col, row), set()))

    def active_loot_remaining(self) -> int:
        return sum(
            1 for p in self.loot_positions
            if p in self.cells
            and self.cells[p].active
            and not self.cells[p].hacked
        )
