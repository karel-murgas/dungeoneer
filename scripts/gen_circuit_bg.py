"""Generate a pixel-art circuit-board background for the hack minigame.

Output: dungeoneer/assets/ui/bg_hack_circuit.png  (1280x720, RGBA)

Algorithm
---------
1. Lay a grid of nodes (STEP px apart).
2. For each node randomly decide which of its 4 neighbours to connect.
   Connection probability is biased so the board looks dense but not solid.
3. Draw traces (thin lines) between connected nodes.
4. Draw a pad (small filled circle) at every node that has at least one
   connection.
5. Optionally draw a faint glow copy of every trace (wider, low alpha) so the
   lines feel neon-lit without blurring the crisp edges.

Palette is taken directly from hack_common.py:
  BG         (4,   8,  18)   – background fill
  trace dim  (18,  50,  70)  – unlit secondary trace
  trace main (0,  160, 180)  – main lit trace  (_COL_WIRE_LIT)
  pad        (0,  210, 220)  – pad highlight
  glow       (0,   90, 120)  – wide soft glow band
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
W, H        = 1280, 720
STEP        = 40          # grid cell size in px
SEED        = 42

# Colours
COL_BG          = (4,   8,  18, 255)
COL_TRACE_DIM   = (12,  38,  55, 255)   # secondary / crossing traces
COL_TRACE_MAIN  = (0,  110, 135, 255)   # main traces (teal, not full cyan)
COL_PAD         = (0,  150, 175, 255)   # pad circle fill
COL_PAD_INNER   = (0,  200, 220, 255)   # bright centre dot
COL_GLOW        = (0,   55,  80,  18)   # wide soft halo (low alpha)

# Geometry
TRACE_W     = 2           # trace line width in px
GLOW_W      = 6           # glow band width
PAD_R       = 3           # pad outer radius
PAD_INNER_R = 1           # bright centre dot radius

# Graph density: probability that a given node→neighbour edge is drawn.
# Two independent rolls (one per endpoint direction) — effective density ≈ P²
CONNECT_P   = 0.55

# Fraction of nodes rendered as "dim" vs "main" colour
DIM_FRACTION = 0.35

# ---------------------------------------------------------------------------
# Build the node grid and connection graph
# ---------------------------------------------------------------------------
def build_graph(w: int, h: int, step: int, p: float, rng: random.Random):
    cols = w // step + 2
    rows = h // step + 2

    # node centre coordinates
    nodes: dict[tuple[int,int], tuple[int,int]] = {}
    for col in range(cols):
        for row in range(rows):
            nx = col * step + step // 2
            ny = row * step + step // 2
            nodes[(col, row)] = (nx, ny)

    # edges: set of frozensets (avoid duplicates)
    edges: set[frozenset] = set()
    for (col, row) in nodes:
        for dcol, drow in ((1, 0), (0, 1)):   # only right + down to avoid dups
            nb = (col + dcol, row + drow)
            if nb in nodes and rng.random() < p:
                edges.add(frozenset({(col, row), nb}))

    return nodes, edges


# ---------------------------------------------------------------------------
# Draw
# ---------------------------------------------------------------------------
def draw(nodes, edges, dim_fraction: float, rng: random.Random) -> Image.Image:
    img  = Image.new("RGBA", (W, H), COL_BG)
    draw = ImageDraw.Draw(img, "RGBA")

    # classify edges into dim / main
    edge_list = list(edges)
    rng.shuffle(edge_list)
    split = int(len(edge_list) * dim_fraction)
    dim_edges  = set(map(frozenset, [list(e) for e in edge_list[:split]]))
    main_edges = set(map(frozenset, [list(e) for e in edge_list[split:]]))

    # which nodes are connected at all
    connected: set[tuple[int,int]] = set()
    for e in edges:
        for n in e:
            connected.add(n)

    # 1. glow pass (wide, very transparent) — main edges only
    for e in main_edges:
        a, b = list(e)
        pa, pb = nodes[a], nodes[b]
        draw.line([pa, pb], fill=COL_GLOW, width=GLOW_W)

    # 2. dim traces
    for e in dim_edges:
        a, b = list(e)
        pa, pb = nodes[a], nodes[b]
        draw.line([pa, pb], fill=COL_TRACE_DIM, width=TRACE_W)

    # 3. main traces
    for e in main_edges:
        a, b = list(e)
        pa, pb = nodes[a], nodes[b]
        draw.line([pa, pb], fill=COL_TRACE_MAIN, width=TRACE_W)

    # 4. pads at connected nodes
    for grid_pos, (px, py) in nodes.items():
        if grid_pos not in connected:
            continue
        # outer pad
        draw.ellipse(
            [px - PAD_R, py - PAD_R, px + PAD_R, py + PAD_R],
            fill=COL_PAD,
        )
        # bright centre
        draw.ellipse(
            [px - PAD_INNER_R, py - PAD_INNER_R,
             px + PAD_INNER_R, py + PAD_INNER_R],
            fill=COL_PAD_INNER,
        )

    return img


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    out_path = Path(__file__).parent.parent / "dungeoneer" / "assets" / "ui" / "bg_hack_circuit.png"

    rng = random.Random(SEED)
    nodes, edges = build_graph(W, H, STEP, CONNECT_P, rng)
    img = draw(nodes, edges, DIM_FRACTION, rng)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    print(f"Saved {img.size[0]}x{img.size[1]} → {out_path}")


if __name__ == "__main__":
    main()
