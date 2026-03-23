---
name: Hack minigame module reference
description: API overview of the hacking minigame — HackScene, HackMap, HackParams, node types
type: reference
---

## Variants

### Classic (node-graph) — `hack_scene.py` / `hack_generator.py`
- `dungeoneer/minigame/hack_scene.py` — HackScene (classic node-graph variant)
- `dungeoneer/minigame/hack_generator.py` — generate_hack_map(params) → HackMap; HackParams
- `dungeoneer/minigame/hack_node.py` — shared data model (NodeType, LootKind, SecurityKind, HackNode, HackMap)
- `dungeoneer/minigame/hack_audio.py` — sound effects (shared)

### Grid (maze / PCB) — `hack_scene_grid.py` / `hack_grid_generator.py`
- `dungeoneer/minigame/hack_scene_grid.py` (~1232 lines) — HackGridScene: maze-grid traversal, PCB/circuit visual
- `dungeoneer/minigame/hack_grid_generator.py` (~581 lines) — generate_grid_map(params) → HackGridMap; HackGridParams
- `dungeoneer/minigame/hack_grid_map.py` (81 lines) — HackGridMap, GridCell, GridCellType; physical 2× grid

### Standalone launcher
- `main_hack.py` — `python main_hack.py [easy|normal|hard] [grid|classic]`; default: normal grid

## Classic Data Model (hack_node.py)

```python
class NodeType(Enum):  ENTRY | EMPTY | LOOT | SECURITY
class LootKind(Enum):  AMMO | RIFLE_AMMO | SHOTGUN_AMMO | HEAL | MEDKIT | WEAPON | CREDITS | BONUS_TIME | ARMOR | MYSTERY
# MYSTERY resolves to a random non-mystery kind on collection
class SecurityKind(Enum):  TIME_PENALTY | DESTROY_LOOT | BLOCKED

@dataclass class HackNode:
    node_id, ntype, sx, sy        # normalised layout [0,1]
    loot_kind, security_kind      # type-specific payload
    hacked, revealed, active      # state flags
    flash_timer: float            # red flash FX
    neighbors: List[int]          # adjacency by node_id

@dataclass class HackMap:
    nodes: List[HackNode]; entry_id: int
    .get(node_id) → HackNode
    .neighbors_of(node_id) → List[HackNode]  # active only
```

## Generation (hack_generator.py)

```python
@dataclass class HackParams:
    node_count=15, loot_count=4, security_count=3
    time_limit=9.0, move_time=0.30, hack_time=0.60, loot_spread=3
    .for_difficulty(difficulty) → HackParams  # Easy/Normal/Hard presets

generate_hack_map(params: HackParams) → HackMap
```

## Scene (hack_scene.py)

```python
class HackScene(Scene):
    def __init__(app, on_finish: Callable[[bool, List[Item]], None], params: HackParams)
    # on_finish(success, collected_items) called when minigame ends
```

Key internal states: `IDLE | MOVING | HACKING | RESULT`

Visual constants: `_NODE_R = 18` (node radius px), `_PLAYER_R = 34`

Security effects: `TIME_PENALTY` subtracts time | `DESTROY_LOOT` destroys random *active* loot node (shown as ghosted red-X "CORRUPT") | `BLOCKED` flashes node, denies entry

F1 help overlay: pauses timer, blocks all input while open. Timer also paused by `_sec_overlay`.

Edge routing: H-V orthogonal paths; BFS 0-1 fallback (`_bfs_ortho_route`) fires when all direct options fail. Bypass candidates clamped to src-tgt bbox ± 3×_NODE_R.

Node layout margins: `_MARGIN_H=0.07`, `_MARGIN_V=0.12` (keeps nodes away from panel edges).

Loot converts to actual `Item` objects via `_make_loot_item(kind)` — maps LootKind → item factory functions from `items/`

## Grid Data Model (hack_grid_map.py / hack_grid_generator.py)

```python
class GridCellType(Enum):  ENTRY | PATH | EMPTY | LOOT | SECURITY
Pos = Tuple[int, int]  # (col, row) physical grid coords

@dataclass class GridCell:
    col, row, cell_type
    loot_kind, security_kind      # type-specific payload
    hacked, revealed, active      # state flags (same semantics as HackNode)
    flash_timer: float

@dataclass class HackGridMap:
    logical_cols, logical_rows    # e.g. 11 × 7
    cells: Dict[Pos, GridCell]    # walkable physical cells
    connections: Dict[Pos, Set[Pos]]  # explicit movement graph
    entry_pos, loot_positions, security_positions, node_positions
    .phys_cols / .phys_rows       # = logical*2-1
    .is_walkable(col, row) → bool
    .neighbors(col, row) → List[Pos]   # explicit edges only
    .active_loot_remaining() → int

# Physical grid: even coords = node positions; odd coords = corridor (PATH) cells
# Logical (lc, lr) → physical (lc*2, lr*2)

@dataclass class HackGridParams:
    logical_cols=11, logical_rows=7
    loot_count=5, security_count=3, empty_count=14
    time_limit=10.0, step_time=0.13, hack_time=0.60
    .for_difficulty(difficulty) → HackGridParams

generate_grid_map(params: HackGridParams) → HackGridMap
```

## Grid Scene (hack_scene_grid.py)

```python
class HackGridScene(Scene):
    def __init__(app, params: HackGridParams,
                 on_complete: Callable[[bool, List[Item], int], None])
    # on_complete(success, items, credits) — same signature as HackScene
```

Visual: corridors = thin coloured lines; nodes = circles; player = pulsing yellow square.
Security hidden: looks like EMPTY until triggered. Movement: arrow keys / WASD along explicit edges only.

## Aim overlay (aim_scene.py)

```python
class AimOverlay:
    """In-world arc overlay — NOT a Scene, no push/pop.
    GameScene owns _aim_overlay: AimOverlay | None directly.
    """
    def __init__(weapon: Weapon, player: Player, target: Enemy,
                 shots: int, on_complete: Callable[[list[float]], None])
    # on_complete(results) — list of accuracy floats, one per shot
    # accuracy: -1.0 = miss, 0.0 = zone edge (min dmg), 1.0 = centre (max dmg / crit)

    def handle_event(event) -> None   # routes F/LMB/Esc; consumes all events
    def update(dt) -> None
    def render(screen, cam_offset_x, cam_offset_y) -> None
    @property is_active -> bool       # False once on_complete has been called
```

Constants (all in `core/settings.py`):
- `AIM_ARC_DEGREES = 90.0` — rozsah arcu (°)
- `AIM_MIN_ZONE = 5.0` — min hit zone size (°)
- `AIM_START_SPEED = 70.0` — °/s
- `AIM_ACCEL = 18.0` — °/s²
- `AIM_CRIT_THRESHOLD = 0.95` — accuracy >= tato hodnota = crit
- `AIM_RESULT_PAUSE = 0.3` — sekund zobrazení výsledku výstřelu
- `AIM_RADIUS_PX = 64` — poloměr arcu v px (~2 dlaždice)

Visual: 90° arc centred on player, pointing toward target. No dark background overlay.
Arc band: outer radius=64px, inner=52px. No scene context switch.

Weapon fields: `aim_zone_base: float` (° at dist=0) and `aim_zone_penalty: float` (°/tile).
Zone at distance d: `max(AIM_MIN_ZONE, aim_zone_base - d * aim_zone_penalty)`.

Integration: `GameScene._launch_aim(target)` → creates AimOverlay → `_on_aim_complete(target, results)` → `RangedAttackAction(accuracy_values=results)` + `_schedule_advance()`.
Statistical simulation (enemies / minigame OFF): `simulate_aim(weapon, distance)` in `combat/damage.py`.
Formula: `hit_chance = min(1.0, zone / AIM_ARC_DEGREES)` (corrected from old zone/(ARC/2)).

## Melee overlay (melee_scene.py)

```python
class MeleeOverlay:
    """In-world power bar — NOT a Scene, no push/pop.
    GameScene owns _melee_overlay: MeleeOverlay | None directly.
    """
    def __init__(weapon: Weapon, player: Player, target: Enemy,
                 on_complete: Callable[[float], None], freq_mult: float = 1.0)
    # on_complete(power) — power ∈ [0.0, 1.0], or -1.0 if cancelled
    # power maps to damage_min..damage_max via calc_melee_aimed()

    def handle_event(event) -> None   # routes F-release/LMB-release/Esc; consumes all events
    def update(dt) -> None
    def render(screen, cam_offset_x, cam_offset_y) -> None
    @property is_active -> bool       # False once on_complete has been called
```

Constants (all in `core/settings.py`):
- `MELEE_FREQ1 = 1.1`, `MELEE_FREQ2 = 0.7` — Hz, two frequencies for compound beat
- `MELEE_FREQ_ACCEL = 0.25` — Hz/s, frequency drift over time
- `MELEE_TIMEOUT = 3.0` — seconds before auto-release
- `MELEE_CRIT_THRESHOLD = 0.92` — power >= this = crit
- `MELEE_RESULT_PAUSE = 0.35` — seconds to display result
- `MELEE_BAR_W = 120`, `MELEE_BAR_H = 12` — bar dimensions in pixels

Visual: horizontal bar above player (world-space). Gradient: red→yellow→green→gold(crit).
Oscillation: `power = 0.5 + 0.5 * sin(f1*t) * sin(f2*t)` — compound beat pattern.
Amplitude varies — not every cycle peaks high; player must READ the pattern.

**Bump-to-attack disabled**: walking into enemy shows "tile occupied" log msg. Melee only via F key.

Integration: `GameScene._launch_melee(target)` → creates MeleeOverlay → `_on_melee_complete(target, power)` → `MeleeAttackAction(target, power=power)` + `_schedule_advance()`.
Enemies / minigame OFF: use `calc_melee()` (random roll, same as before).

## Integration Notes
- Launched as a `Scene` via `SceneManager` — push HackScene, it calls `on_complete` callback, then pops itself
- `on_complete(success: bool, items: List[Item], credits: int)` — credits are from hacked nodes
- **Integrated into `GameScene`**: `OpenContainerAction` on a non-objective container intercepts and calls `GameScene._launch_hack(container)`
  - `_on_hack_complete`: marks container opened; success → drops items + awards credits; failure → spawns alert drone (CombatState, LOS spawn)
  - `GameScene.on_resume()` fires `_schedule_advance()` after the scene pops (safe: avoids running AI while HackScene is still on stack)
- Objective containers (Corp Vault) still open immediately (no minigame)
