"""Procedural generation of the hacking minigame node graph."""
from __future__ import annotations

import math
import random
from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Tuple

from dungeoneer.minigame.hack_node import (
    HackMap, HackNode, LootKind, NodeType, SecurityKind,
)

if TYPE_CHECKING:
    from dungeoneer.core.difficulty import Difficulty

_MIN_LOOT_DIST = 3   # minimum BFS hops from entry for loot nodes


@dataclass
class HackParams:
    node_count:     int   = 15
    loot_count:     int   = 4
    security_count: int   = 3
    time_limit:     float = 9.0
    move_time:      float = 0.30
    hack_time:      float = 0.60
    loot_spread:    int   = 3   # minimum BFS hops between any two loot nodes

    @classmethod
    def for_difficulty(cls, difficulty: "Difficulty") -> "HackParams":
        name = difficulty.name.lower()
        if name == "easy":
            return cls(node_count=12, loot_count=5, security_count=1,
                       time_limit=12.0, move_time=0.25, hack_time=0.50,
                       loot_spread=2)
        if name == "hard":
            return cls(node_count=18, loot_count=3, security_count=4,
                       time_limit=7.0,  move_time=0.35, hack_time=0.70,
                       loot_spread=3)
        return cls()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _dist(a: HackNode, b: HackNode) -> float:
    return math.hypot(a.sx - b.sx, a.sy - b.sy)


def _add_edge(nodes: List[HackNode], i: int, j: int) -> None:
    if j not in nodes[i].neighbors:
        nodes[i].neighbors.append(j)
    if i not in nodes[j].neighbors:
        nodes[j].neighbors.append(i)


def _prim_mst(nodes: List[HackNode]) -> List[Tuple[int, int]]:
    """Return MST edges using Prim's algorithm (O(n²) — fine for n ≤ 20)."""
    n = len(nodes)
    in_tree = [False] * n
    min_dist = [math.inf] * n
    parent   = [-1] * n
    min_dist[0] = 0.0
    edges = []

    for _ in range(n):
        u = min((i for i in range(n) if not in_tree[i]), key=lambda i: min_dist[i])
        in_tree[u] = True
        if parent[u] != -1:
            edges.append((parent[u], u))
        for v in range(n):
            if not in_tree[v]:
                d = _dist(nodes[u], nodes[v])
                if d < min_dist[v]:
                    min_dist[v] = d
                    parent[v] = u

    return edges


def _bfs_distances(nodes: List[HackNode], entry_id: int) -> Dict[int, int]:
    """BFS from entry_id; returns {node_id: hop_distance}."""
    dist: Dict[int, int] = {entry_id: 0}
    queue: deque[int] = deque([entry_id])
    while queue:
        curr = queue.popleft()
        for nb_id in nodes[curr].neighbors:
            if nb_id not in dist:
                dist[nb_id] = dist[curr] + 1
                queue.append(nb_id)
    return dist


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_hack_map(params: HackParams, rng: random.Random | None = None) -> HackMap:
    """Generate a procedural node graph for the hacking minigame."""
    if rng is None:
        rng = random.Random()

    n = params.node_count

    # ------------------------------------------------------------------
    # Phase 1: Grid layout with jitter
    # ------------------------------------------------------------------
    grid_cols = math.ceil(math.sqrt(n * 1.6))
    grid_rows = math.ceil(n / grid_cols) + 1

    all_cells    = [(c, r) for r in range(grid_rows) for c in range(grid_cols)]
    chosen_cells = rng.sample(all_cells, n)

    nodes: List[HackNode] = []
    for i, (col, row) in enumerate(chosen_cells):
        jx = rng.uniform(-0.15, 0.15)
        jy = rng.uniform(-0.15, 0.15)
        sx = (col + 0.5 + jx) / grid_cols
        sy = (row + 0.5 + jy) / grid_rows
        nodes.append(HackNode(node_id=i, ntype=NodeType.EMPTY, sx=sx, sy=sy))

    # ------------------------------------------------------------------
    # Phase 2: Build MST for guaranteed connectivity
    # ------------------------------------------------------------------
    for a, b in _prim_mst(nodes):
        _add_edge(nodes, a, b)

    # ------------------------------------------------------------------
    # Phase 3: Extra edges for multiple paths (added NOW so BFS below
    # measures actual traversal distances the player will experience).
    # ------------------------------------------------------------------
    dist_threshold = 0.45
    max_degree     = 4
    for i in range(n):
        for j in range(i + 1, n):
            if j in nodes[i].neighbors:
                continue
            if len(nodes[i].neighbors) >= max_degree:
                continue
            if len(nodes[j].neighbors) >= max_degree:
                continue
            if _dist(nodes[i], nodes[j]) < dist_threshold:
                if rng.random() < 0.45:
                    _add_edge(nodes, i, j)

    # ------------------------------------------------------------------
    # Phase 4: Pick ENTRY as the node that maximises the number of nodes
    # at BFS distance >= _MIN_LOOT_DIST on the FULL graph.
    # Ties broken randomly.
    # ------------------------------------------------------------------
    best_candidates: list[int] = []
    best_far_count = -1
    for candidate in range(n):
        d = _bfs_distances(nodes, candidate)
        far_count = sum(1 for i, dist in d.items()
                        if i != candidate and dist >= _MIN_LOOT_DIST)
        if far_count > best_far_count:
            best_far_count = far_count
            best_candidates = [candidate]
        elif far_count == best_far_count:
            best_candidates.append(candidate)

    entry_idx = rng.choice(best_candidates)
    nodes[entry_idx].ntype = NodeType.ENTRY

    # ------------------------------------------------------------------
    # Phase 5: BFS distances from chosen entry + pairwise distances
    # (pairwise used for spread-aware loot placement)
    # ------------------------------------------------------------------
    hop_dist  = _bfs_distances(nodes, entry_idx)
    pairwise  = {i: _bfs_distances(nodes, i) for i in range(n)}

    # ------------------------------------------------------------------
    # Phase 6: Assign node types
    # Loot nodes must be at least _MIN_LOOT_DIST hops from entry AND
    # at least params.loot_spread hops from every other loot node so
    # that the player must make route decisions instead of chaining
    # nearby nodes.
    # ------------------------------------------------------------------
    non_entry = [i for i in range(n) if nodes[i].ntype != NodeType.ENTRY]

    far_nodes  = [i for i in non_entry if hop_dist.get(i, 0) >= _MIN_LOOT_DIST]
    loot_count = min(params.loot_count, len(far_nodes))

    # Greedy spread-aware placement: each new loot node must be at least
    # loot_spread hops from all already-placed loot nodes.
    available    = list(far_nodes)
    rng.shuffle(available)
    loot_indices: list[int] = []
    for _ in range(loot_count):
        if not available:
            break
        if not loot_indices:
            pick = available[0]
        else:
            spread_ok = [c for c in available
                         if all(pairwise[c].get(p, 0) >= params.loot_spread
                                for p in loot_indices)]
            if spread_ok:
                pick = rng.choice(spread_ok)
            else:
                # Fallback: maximise minimum distance to already-placed loot
                pick = max(available,
                           key=lambda c: min(pairwise[c].get(p, 0)
                                             for p in loot_indices))
        loot_indices.append(pick)
        available.remove(pick)

    remaining   = [i for i in non_entry if i not in loot_indices]
    sec_count   = min(params.security_count, len(remaining))
    sec_indices = rng.sample(remaining, sec_count)

    # Distribute loot kinds with weights so weapons/bonus_time are rarer
    _loot_pool = (
        [LootKind.AMMO]         * 3 +
        [LootKind.RIFLE_AMMO]   * 2 +
        [LootKind.SHOTGUN_AMMO] * 2 +
        [LootKind.HEAL]         * 3 +
        [LootKind.MEDKIT]       * 1 +
        [LootKind.WEAPON]       * 1 +
        [LootKind.CREDITS]      * 3 +
        [LootKind.BONUS_TIME]   * 1
    )
    all_sec_kinds = list(SecurityKind)

    for idx in loot_indices:
        nodes[idx].ntype     = NodeType.LOOT
        nodes[idx].loot_kind = rng.choice(_loot_pool)
        nodes[idx].revealed  = True

    for idx in sec_indices:
        nodes[idx].ntype         = NodeType.SECURITY
        nodes[idx].security_kind = rng.choice(all_sec_kinds)
        nodes[idx].revealed      = False

    return HackMap(nodes=nodes, entry_id=entry_idx)
