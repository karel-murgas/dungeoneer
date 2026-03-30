"""Procedural generation of the maze-grid hacking minigame map.

Coordinate system
-----------------
Logical grid  (LC × LR): node positions, indices 0..LC-1 × 0..LR-1.
Physical grid (PC × PR): LC*2-1 × LR*2-1 cells.

Mapping:  logical (lc, lr)  →  physical (lc*2, lr*2)
Corridor between logical neighbours (lc,lr) and (lc±1,lr):
    physical cells (lc*2 ± 1, lr*2) — exactly one corridor cell.
Corridor between logical neighbours (lc,lr) and (lc,lr±1):
    physical cells (lc*2, lr*2 ± 1) — exactly one corridor cell.

Only directly adjacent logical nodes (manhattan distance == 1) can share a
single-cell corridor.  Longer straight runs are built by chaining multiple
single-step corridors through intermediate corridor cells (no intermediate
*node* is required; the corridor just passes through PATH cells).

This structure guarantees that no two corridors run parallel and adjacent —
all parallel corridors are at least 2 physical cells apart.
"""
from __future__ import annotations

import random
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Set, Tuple, TYPE_CHECKING

from dungeoneer.minigame.hack_node import LootKind, SecurityKind
from dungeoneer.minigame.hack_grid_map import GridCell, GridCellType, HackGridMap, Pos

if TYPE_CHECKING:
    from dungeoneer.core.difficulty import Difficulty


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_LC = 11   # logical columns
_LR = 7    # logical rows

_loot_pool = (
    [LootKind.AMMO]         * 3 +
    [LootKind.RIFLE_AMMO]   * 2 +
    [LootKind.SHOTGUN_AMMO] * 2 +
    [LootKind.HEAL]         * 3 +
    [LootKind.MEDKIT]       * 1 +
    [LootKind.WEAPON]       * 1 +
    [LootKind.CREDITS]      * 3 +
    [LootKind.BONUS_TIME]   * 1 +
    [LootKind.ARMOR]        * 1 +
    [LootKind.COOLANT]      * 1 +
    [LootKind.MYSTERY]      * 2
)


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class HackGridParams:
    """Parameters for the maze-grid hacking minigame."""
    logical_cols:   int   = _LC
    logical_rows:   int   = _LR
    loot_count:     int   = 5
    security_count: int   = 3
    empty_count:    int   = 14   # total non-entry nodes placed; loot_count of these become LOOT
    time_limit:     float = 10.0
    step_time:      float = 0.13  # seconds per tile step
    hack_time:      float = 0.60  # seconds to collect a loot node

    @classmethod
    def for_difficulty(cls, difficulty: "Difficulty") -> "HackGridParams":
        name = difficulty.name.lower()
        if name == "easy":
            return cls(loot_count=5, security_count=1, empty_count=16,
                       time_limit=12.0, step_time=0.10, hack_time=0.50)
        if name == "hard":
            return cls(loot_count=3, security_count=4, empty_count=10,
                       time_limit=7.0, step_time=0.15, hack_time=0.70)
        return cls(loot_count=4, empty_count=13, time_limit=9.0)


# ---------------------------------------------------------------------------
# Coordinate helpers
# ---------------------------------------------------------------------------

def _l2p(lc: int, lr: int) -> Pos:
    """Logical → physical."""
    return (lc * 2, lr * 2)


def _corridor_cell(a_logical: Pos, b_logical: Pos) -> Pos:
    """
    Return the single corridor cell between two logically adjacent nodes.
    Precondition: manhattan distance == 1.
    """
    ac, ar = a_logical
    bc, br = b_logical
    return ((ac + bc), (ar + br))   # midpoint in physical coords = (ac*2+bc*2)/2 etc.


# ---------------------------------------------------------------------------
# Node placement helpers
# ---------------------------------------------------------------------------

def _spread_logical(
    cols: int,
    rows: int,
    count: int,
    exclude: Set[Pos],
    rng: random.Random,
    margin_c: int = 1,
    margin_r: int = 1,
    min_dist: int = 3,
) -> List[Pos]:
    """Pick spread-out logical positions not in *exclude*."""
    candidates = [
        (c, r)
        for c in range(margin_c, cols - margin_c)
        for r in range(margin_r, rows - margin_r)
        if (c, r) not in exclude
    ]
    rng.shuffle(candidates)

    chosen: List[Pos] = []
    for _ in range(count):
        if not candidates:
            break
        if not chosen:
            pick = candidates[0]
        else:
            ok = [
                c for c in candidates
                if all(abs(c[0]-p[0]) + abs(c[1]-p[1]) >= min_dist for p in chosen)
            ]
            if ok:
                pick = rng.choice(ok)
            else:
                pick = max(
                    candidates,
                    key=lambda c: min(abs(c[0]-p[0]) + abs(c[1]-p[1]) for p in chosen),
                )
        chosen.append(pick)
        candidates = [c for c in candidates if c != pick]

    return chosen


# ---------------------------------------------------------------------------
# Connection graph builder (logical edges → physical corridor cells)
# ---------------------------------------------------------------------------

def _build_logical_connections(
    all_nodes: Set[Pos],
    rng: random.Random,
    extra_chance: float = 0.65,
    max_extra_dist: int = 4,
) -> List[Tuple[Pos, Pos]]:
    """
    Return a list of logical edges (pairs of node positions).

    Rules
    -----
    - Edges may only exist between nodes in the SAME logical row OR column
      (so corridors are always straight H or V).
    - The spanning tree is built using Kruskal's on a "closest-in-row/col" graph.
    - Extra edges are added between nearby (≤ max_extra_dist) row/col neighbours
      with probability extra_chance, creating loops for maze feel.
    """
    nodes = list(all_nodes)

    # All possible straight (H or V) edges, weighted by logical distance
    possible: List[Tuple[int, Pos, Pos]] = []
    for i, a in enumerate(nodes):
        for j, b in enumerate(nodes):
            if j <= i:
                continue
            ac, ar = a
            bc, br = b
            if ar == br or ac == bc:   # same row or column
                dist = abs(ac - bc) + abs(ar - br)
                possible.append((dist, a, b))
    possible.sort()

    # Kruskal's spanning tree
    parent: Dict[Pos, Pos] = {n: n for n in nodes}

    def find(x: Pos) -> Pos:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: Pos, b: Pos) -> bool:
        pa, pb = find(a), find(b)
        if pa == pb:
            return False
        parent[pa] = pb
        return True

    mst_edges: List[Tuple[Pos, Pos]] = []
    for _, a, b in possible:
        if union(a, b):
            mst_edges.append((a, b))

    # Extra edges for loops
    mst_set: Set[FrozenSet] = {frozenset({a, b}) for a, b in mst_edges}
    extra_edges: List[Tuple[Pos, Pos]] = []
    for dist, a, b in possible:
        if dist > max_extra_dist:
            continue
        if frozenset({a, b}) in mst_set:
            continue
        if rng.random() < extra_chance:
            extra_edges.append((a, b))

    return mst_edges + extra_edges


def _build_physical_corridor(
    a_logical: Pos,
    b_logical: Pos,
    cells: Dict[Pos, GridCell],
    connections: Dict[Pos, Set[Pos]],
) -> None:
    """
    Carve a straight corridor from logical node A to logical node B.

    Both A and B must be in the same logical row OR column.
    Adds physical corridor cells and bidirectional connections.
    """
    ac, ar = a_logical
    bc, br = b_logical

    if ar == br:
        # Horizontal corridor
        row = ar * 2
        c1, c2 = min(ac, bc) * 2, max(ac, bc) * 2
        prev: Optional[Pos] = None
        for pc in range(c1, c2 + 1):
            pos: Pos = (pc, row)
            if pos not in cells:
                cells[pos] = GridCell(pc, row, GridCellType.PATH)
            if prev is not None:
                connections[prev].add(pos)
                connections[pos].add(prev)
            prev = pos

    else:
        # Vertical corridor (same logical column)
        col = ac * 2
        r1, r2 = min(ar, br) * 2, max(ar, br) * 2
        prev = None
        for pr in range(r1, r2 + 1):
            pos = (col, pr)
            if pos not in cells:
                cells[pos] = GridCell(col, pr, GridCellType.PATH)
            if prev is not None:
                connections[prev].add(pos)
                connections[pos].add(prev)
            prev = pos


# ---------------------------------------------------------------------------
# Connectivity check
# ---------------------------------------------------------------------------

def _reachable(start: Pos, connections: Dict[Pos, Set[Pos]]) -> Set[Pos]:
    visited = {start}
    queue = deque([start])
    while queue:
        cur = queue.popleft()
        for nb in connections.get(cur, set()):
            if nb not in visited:
                visited.add(nb)
                queue.append(nb)
    return visited


# ---------------------------------------------------------------------------
# Entry fan-out helper
# ---------------------------------------------------------------------------

def _boost_entry_degree(
    entry: Pos,
    all_nodes: Set[Pos],
    edges: List[Tuple[Pos, Pos]],
    min_degree: int = 3,
) -> None:
    """
    Ensure the entry node has at least *min_degree* logical connections.
    Adds extra same-row/column edges (shortest first) until the requirement
    is met.  Modifies *edges* in place.
    """
    existing = {frozenset(e) for e in edges}

    def _degree() -> int:
        return sum(1 for e in edges if entry in e)

    if _degree() >= min_degree:
        return

    # Candidates: nodes on the same row or column, not yet connected
    candidates = sorted(
        (abs(n[0] - entry[0]) + abs(n[1] - entry[1]), n)
        for n in all_nodes
        if n != entry
        and (n[0] == entry[0] or n[1] == entry[1])
        and frozenset({entry, n}) not in existing
    )

    for _, n in candidates:
        if _degree() >= min_degree:
            break
        edges.append((entry, n))
        existing.add(frozenset({entry, n}))


# ---------------------------------------------------------------------------
# Loot placement helpers (graph-distance based)
# ---------------------------------------------------------------------------

def _iter_node_neighbors(
    node_pos: Pos,
    node_positions: Set[Pos],
    connections: Dict[Pos, Set[Pos]],
) -> List[Pos]:
    """Follow corridors outward from *node_pos* and yield the first node reached
    in each direction (skipping corridor cells)."""
    result: List[Pos] = []
    for start_nb in connections.get(node_pos, set()):
        prev, cur = node_pos, start_nb
        while True:
            if cur in node_positions:
                result.append(cur)
                break
            nexts = [n for n in connections.get(cur, set()) if n != prev]
            if not nexts:
                break
            prev, cur = cur, nexts[0]
    return result


def _node_graph_distances(
    entry_phys: Pos,
    node_positions: Set[Pos],
    connections: Dict[Pos, Set[Pos]],
) -> Dict[Pos, int]:
    """BFS from *entry_phys* counting node-to-node hops (corridor cells ignored).
    Returns {node_pos: hop_count}."""
    dist: Dict[Pos, int] = {entry_phys: 0}
    queue: deque = deque([entry_phys])
    while queue:
        cur_node = queue.popleft()
        for nb in _iter_node_neighbors(cur_node, node_positions, connections):
            if nb not in dist:
                dist[nb] = dist[cur_node] + 1
                queue.append(nb)
    return dist


def _assign_loot_positions(
    count: int,
    entry_phys: Pos,
    node_positions: Set[Pos],
    cells: Dict[Pos, GridCell],
    reachable: Set[Pos],
    node_dists: Dict[Pos, int],
    rng: random.Random,
    min_hops: int = 3,
) -> List[Pos]:
    """Pick *count* EMPTY node positions for loot.

    Strategy
    --------
    1. Candidates: EMPTY nodes with node-graph distance >= min_hops from entry.
    2. If too few, fall back to min_hops-1, min_hops-2, …
    3. Greedy spread: start with the node farthest from entry (by hop count),
       then iteratively pick the one with maximum minimum Manhattan distance
       to already-chosen loot nodes.
    """
    candidates: List[Pos] = []
    for fallback in range(min_hops, 0, -1):
        candidates = [
            p for p in node_positions
            if p in reachable
            and p != entry_phys
            and p in cells
            and cells[p].cell_type == GridCellType.EMPTY
            and node_dists.get(p, 0) >= fallback
        ]
        if len(candidates) >= count:
            break

    if not candidates:
        return []

    # Shuffle first to break ties, then stable-sort by descending hop count
    rng.shuffle(candidates)
    candidates.sort(key=lambda p: -node_dists.get(p, 0))

    chosen = [candidates[0]]
    remaining = candidates[1:]
    while len(chosen) < count and remaining:
        best = max(
            remaining,
            key=lambda p: min(abs(p[0] - c[0]) + abs(p[1] - c[1]) for c in chosen),
        )
        chosen.append(best)
        remaining = [p for p in remaining if p != best]

    return chosen


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_grid_map(
    params: HackGridParams,
    rng: random.Random | None = None,
) -> HackGridMap:
    """Generate a procedural maze-grid map for the grid hacking minigame."""
    if rng is None:
        rng = random.Random()

    LC = params.logical_cols
    LR = params.logical_rows

    # ------------------------------------------------------------------
    # Phase 1: Place all nodes as EMPTY (loot is assigned later by graph dist)
    # ------------------------------------------------------------------
    # Entry at col 1 (not col 0) so it's away from the visual edge
    entry_logical: Pos = (1, rng.randint(LR // 3, 2 * LR // 3))
    used: Set[Pos] = {entry_logical}
    entry_c, entry_r = entry_logical

    # Guarantee ≥1 node in entry's column and ≥1 in entry's row so the MST
    # always gives the entry ≥ 2 connections (two escape routes from the start).
    forced_branches: List[Pos] = []

    col_cands = [(entry_c, r) for r in range(1, LR - 1) if (entry_c, r) not in used]
    if col_cands:
        b = rng.choice(col_cands)
        forced_branches.append(b)
        used.add(b)

    row_cands = [(c, entry_r) for c in range(entry_c + 1, LC - 1)
                 if (c, entry_r) not in used]
    if row_cands:
        b = rng.choice(row_cands)
        forced_branches.append(b)
        used.add(b)

    # Remaining empty waypoints
    remaining_empty = max(0, params.empty_count - len(forced_branches))
    extra_empties = _spread_logical(
        LC, LR, remaining_empty, used, rng,
        margin_c=1, margin_r=1, min_dist=2,
    )
    all_empty_logicals: List[Pos] = forced_branches + extra_empties
    used |= set(all_empty_logicals)

    all_nodes: Set[Pos] = {entry_logical} | set(all_empty_logicals)

    # ------------------------------------------------------------------
    # Phase 2: Build logical connections (spanning tree + extras)
    # ------------------------------------------------------------------
    logical_edges = _build_logical_connections(all_nodes, rng)

    # Ensure entry node has at least 3 connections (more escape routes)
    _boost_entry_degree(entry_logical, all_nodes, logical_edges, min_degree=3)

    # ------------------------------------------------------------------
    # Phase 3: Build physical cells and connections
    # ------------------------------------------------------------------
    cells: Dict[Pos, GridCell] = {}
    connections: Dict[Pos, Set[Pos]] = defaultdict(set)
    node_positions: Set[Pos] = set()

    for lpos in all_nodes:
        pc, pr = _l2p(*lpos)
        node_positions.add((pc, pr))
        ct = GridCellType.ENTRY if lpos == entry_logical else GridCellType.EMPTY
        cells[(pc, pr)] = GridCell(pc, pr, ct)

    for a_log, b_log in logical_edges:
        _build_physical_corridor(a_log, b_log, cells, connections)

    # Upgrade intersection PATH cells (≥3 connections) to EMPTY nodes so the
    # scene can use node_positions as the single "stop here" set.
    for pos in list(cells):
        if pos not in node_positions and len(connections.get(pos, set())) >= 3:
            cells[pos].cell_type = GridCellType.EMPTY
            node_positions.add(pos)

    # ------------------------------------------------------------------
    # Phase 4: Connectivity check — add emergency bridge if needed
    # ------------------------------------------------------------------
    entry_phys: Pos = _l2p(*entry_logical)
    reachable = _reachable(entry_phys, connections)
    isolated = [p for p in node_positions if p not in reachable]

    if isolated:
        # Connect each isolated node to the nearest reachable node
        # using an L-shaped path through an emergency waypoint node
        for iso_phys in isolated:
            iso_log = (iso_phys[0] // 2, iso_phys[1] // 2)
            nearest_log: Optional[Pos] = None
            best_d = 99999
            for n_phys in reachable & node_positions:
                n_log = (n_phys[0] // 2, n_phys[1] // 2)
                d = abs(iso_log[0] - n_log[0]) + abs(iso_log[1] - n_log[1])
                if d < best_d:
                    best_d = d
                    nearest_log = n_log
            if nearest_log is None:
                continue
            # Add an L-shaped bridge via a corner waypoint
            corner_log: Pos = (nearest_log[0], iso_log[1])
            if corner_log not in all_nodes:
                cp, crp = _l2p(*corner_log)
                node_positions.add((cp, crp))
                cells[(cp, crp)] = GridCell(cp, crp, GridCellType.EMPTY)
                all_nodes.add(corner_log)
            _build_physical_corridor(nearest_log, corner_log, cells, connections)
            _build_physical_corridor(corner_log, iso_log, cells, connections)
            reachable = _reachable(entry_phys, connections)

    # ------------------------------------------------------------------
    # Phase 5: Assign loot positions by node-graph distance from entry
    #
    # BFS on the node graph (skipping corridor cells) → pick nodes that are
    # ≥ 3 hops from entry and spread as far from each other as possible.
    # ------------------------------------------------------------------
    node_dists = _node_graph_distances(entry_phys, node_positions, dict(connections))
    loot_positions: List[Pos] = _assign_loot_positions(
        params.loot_count, entry_phys, node_positions,
        cells, reachable, node_dists, rng, min_hops=3,
    )
    for p in loot_positions:
        cells[p].cell_type = GridCellType.LOOT
        cells[p].loot_kind = rng.choice(_loot_pool)

    # ------------------------------------------------------------------
    # Phase 6: Place security cells (hidden)
    #
    # Security goes ONLY on EMPTY nodes — never on corridor cells or loot/entry.
    # ------------------------------------------------------------------
    all_sec_kinds = list(SecurityKind)

    security_candidates: List[Pos] = [
        p for p in node_positions
        if p in reachable
        and p != entry_phys
        and p not in loot_positions
        and p in cells
        and cells[p].cell_type == GridCellType.EMPTY
    ]

    sec_count = min(params.security_count, len(security_candidates))
    security_positions: List[Pos] = (
        rng.sample(security_candidates, sec_count) if security_candidates else []
    )

    for pos in security_positions:
        cells[pos].cell_type     = GridCellType.SECURITY
        cells[pos].security_kind = rng.choice(all_sec_kinds)
        cells[pos].revealed      = False

    return HackGridMap(
        logical_cols=LC,
        logical_rows=LR,
        cells=cells,
        connections=dict(connections),
        entry_pos=entry_phys,
        loot_positions=loot_positions,
        security_positions=security_positions,
        node_positions=node_positions,
    )
