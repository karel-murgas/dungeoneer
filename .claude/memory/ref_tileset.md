---
name: Dithart tileset index lookup
description: Correct tile indices for each autotile configuration in tileset_for_free.png, plus PIL identification method
type: reference
---

When a tile index is wrong (e.g. outer wall corners look like inner concave pieces), use this approach to find the correct index:

1. Load `sources/.../texture/godot_template/godot_minimal_3x3_autotile.png` (384×128, 12×4 grid of 32×32 tiles) alongside the template `godot_minimal_3x3_autotile_template.png` (same size — pink=wall, white=floor).
2. For each autotile position, count white pixels in the template to determine how many floor neighbors it has.
3. To identify which direction(s) have floor: compute the centroid of white pixels relative to the tile center. Positive cx=E, negative cx=W, positive cy=S, negative cy=N.
4. Match the autotile tile image pixel-for-pixel against every tile in `tileset_for_free.png` (8 cols × 15 rows, 0-indexed) to get the tile index.

**Key findings (confirmed correct in-game):**

Single face tiles (1 floor neighbor):
- N floor → tile 42   (white=270, centroid N)
- S floor → tile 88   (white=270, centroid S)
- W floor → tile 20   (white=270, centroid W)
- E floor → tile 16   (white=270, centroid E)

Wall end cap tiles (7 floor neighbors, 1 wall neighbor — tip of a 1-tile-wide wall stub):
- N cap (floor N+E+W, wall S) → tile 15  (top of isolated NS wall)
- S cap (floor S+E+W, wall N) → tile 31  (bottom of isolated NS wall)
- W cap (floor N+S+W, wall E) → tile 5   (left end of isolated EW wall)
- E cap (floor N+S+E, wall W) → tile 7   (right end of isolated EW wall)

Two opposite face tiles (2 floor neighbors, opposite sides):
- N+S floor → tile 6   (floor both north and south, corridor running E-W)
- E+W floor → tile 23  (floor both east and west, corridor running N-S)

Isolated wall pillar (all 4 cardinal + all diagonal neighbors are floor):
- 0b1111 → tile 21  (autotile bottom-left corner (0,3); fuzzy match on opaque pixels only, diff=8.8)

Two adjacent face tiles / inner corners (2 floor neighbors, adjacent):
- N+W → tile 27
- N+E → tile 25
- S+W → tile 11
- S+E → tile 9

Outer convex corner tiles (mask=0, one diagonal floor neighbor):
- SE floor → tile 1   (outer top-left corner of room)
- SW floor → tile 3   (outer top-right corner)
- NE floor → tile 24  (outer bottom-left corner)
- NW floor → tile 28  (outer bottom-right corner)

Elevator tiles:
- Closed elevator → tile 36  (row 4, col 4 — teal glass doors)
- Open elevator   → tile 44  (row 5, col 4 — doors retracted, mostly transparent)

**Why:** Identified by pixel-matching the `godot_minimal_3x3_autotile.png` positions against the main tileset, and using template centroid analysis to determine floor direction. Elevator tiles identified by teal pixel count analysis.

**How to apply:** Whenever a wall tile looks wrong in-game, use the PIL pixel-matching script to re-derive the correct index from the autotile template rather than guessing.
