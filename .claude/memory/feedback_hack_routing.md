---
name: Hack minigame routing layout tuning history
description: History of routing/layout changes with original values — use to revert if needed
type: feedback
---

## Baseline (před opravami, commit 104ac5e)
- `_NODE_R = 24` v hack_scene.py
- Žádný margin v generátoru — sx/sy volně v [0,1]
- CLEAR = NODE_R pro všechny nódy (inflace rect přes celý prostor mezi nódy)
- Fallback routing nekontroloval `_middle_ok` — cesty procházely skrz nódy

## Aktuální stav (session březen 2026)

### Routing
1. **Heuristika** (L/Z/U trasy + bypass) — zkouší `_middle_ok AND _parallel_ok`, pak relaxuje parallel
2. **BFS fallback** (`_bfs_ortho_route`) — 0-1 BFS na mřížce s CELL=NODE_R//3, minimalizuje zatáčky, zaručuje vyhnutí se nódům
3. **Two-tier clearance**: `CLEAR_SELF=NODE_R` pro src/tgt, `CLEAR_INTER=6` pro intermediate
4. Ikony `sz = _NODE_R * 2 - 4` (dříve hardcoded 38)

### Layout
- `_NODE_R = 18` (z 24)
- `_MARGIN_H = 0.07`, `_MARGIN_V = 0.12` v generátoru

## Jak revertovat celé
- `_NODE_R` v hack_scene.py řádek 75: vrátit na `24`
- Generátor: odebrat `_MARGIN_H / _MARGIN_V` remapping, vrátit:
  ```python
  sx = (col + 0.5 + jx) / grid_cols
  sy = (row + 0.5 + jy) / grid_rows
  ```
- Routing: odebrat `_bfs_ortho_route` funkci; vrátit konec `_edge_path` na:
  ```python
  return _build(options[0])
  ```
- CLEAR: vrátit na `CLEAR = _NODE_R` (jedno číslo, odebrat `_is_endpoint`, `CLEAR_SELF/CLEAR_INTER`)
- Ikony: vrátit `sz = 38`
