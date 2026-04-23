# Vault Drain Minigame — Implementation Plan

## Context

On the final floor (floor 3), the player reaches the Corp Vault. Currently, opening it immediately awards credits and triggers victory. The new design replaces this with an interactive **cursor-tracking minigame** where the player "drains" credits over time. The player balances credit gain vs. heat accumulation, and can quit anytime or get kicked out by a patrol.

**Key rules:**
- Player can **return to the vault** after voluntarily disconnecting (only patrol interrupts permanently)
- Credits are **not awarded until the player escapes** (uses elevator to extract)
- Player does **not see** how many credits remain in the vault
- Elevator and vault must be placed so that pressing E doesn't trigger both

---

## 1. VaultOverlay (`minigame/vault_scene.py`) — NEW FILE

### Class: `VaultOverlay` (plain class, NOT a Scene)

**Constructor:**
```python
def __init__(self, total_credits: int, credits_already_drained: int,
             player: Player, heat_system: HeatSystem,
             difficulty: Difficulty,
             on_complete: Callable[[int, bool, bool], None]) -> None:
```
- `total_credits` — full vault value (hidden from player)
- `credits_already_drained` — from previous drain sessions (allows re-entry)
- `on_complete(credits_earned_this_session: int, fully_drained: bool)` — callback when overlay ends
  - Player can always re-enter after disconnecting (voluntary or patrol interrupt)
  - Patrol interrupt just closes the overlay; after combat resolves, player walks back

**State Machine** (`_State` enum):
- `DRAINING` — main gameplay loop (cursor tracking + periodic checks)
- `RESULT` — brief pause showing disconnection message (0.8s)
- `DONE` — fires callback

### Cursor Physics (1D vertical, range 0.0–1.0)
- `position: float` — starts at 0.5 (center)
- `velocity: float` — starts at 0.0
- **Damping**: `velocity *= 0.92` per frame (60 FPS)
- **Player impulse**: UP/W = +impulse, DOWN/S = −impulse
  - `VAULT_IMPULSE = 0.8` (units/s added to velocity)
  - Impulse applied continuously while key is held (not just on keydown)
- **Random drift**: every frame, add `random.gauss(0, drift_sigma) * dt`
  - Base `VAULT_DRIFT_SIGMA = 1.2`
  - Scales with heat level: `drift_sigma = base * (1.0 + 0.3 * (heat_level - 1))`
  - Scales with difficulty: `drift_sigma *= difficulty.vault_drift_mult`
  - Last 20% of credits: `drift_sigma *= 2.0` (dramatic finale — player doesn't know exact % but feels it)
- **Boundary**: clamp position to [0.0, 1.0]; bounce velocity on edges (`velocity *= -0.3`)

### Zones (centered at 0.5)
- **Perfect**: |pos − 0.5| ≤ 0.08 (center 16%)
- **Good**: |pos − 0.5| ≤ 0.20 (center 40%)
- **Bad**: |pos − 0.5| ≤ 0.35 (center 70%)
- **Fail**: everything else (outer 30%)

### Periodic Check (every `VAULT_CHECK_INTERVAL = 1.5` seconds)
Evaluate cursor position zone:
| Zone | Multiplier change | Heat |
|------|------------------|------|
| Perfect | +0.15 (cap 2.0×) | +4 |
| Good | +0.05 (cap 2.0×) | +6 |
| Bad | −0.10 (floor 0.3×) | +8 |
| Fail | −0.20 (floor 0.3×) | +14 |

Visual flash on check: zone name + color flash on the gauge.

**Heat budget for full drain (~30s at 1.0×):**
- ~20 checks × 5 avg = 100 heat (1 level) for decent player
- ~20 checks × 10 avg = 200 heat (2 levels) for poor player
- Skilled player (mostly Perfect): ~20 × 4.5 = 90 heat (~1 level)

### Credit Drain
- `VAULT_DRAIN_SECONDS = 30.0` — time for full drain at 1.0× multiplier
- Base rate: `total_credits / VAULT_DRAIN_SECONDS` credits per second
- Actual rate: `base_rate * multiplier`
- Multiplier starts at 1.0, range [0.3, 2.0]
- Internal `_credits_drained_this_session` counter (float, for precision)
- **Player sees only**: earned credits counter (going up) — NOT remaining/total
- When internal remaining ≤ 0: vault fully drained → end

### Completion Bonus
- Full drain: +25% bonus credits (`VAULT_FULL_DRAIN_BONUS = 0.25`)
- Applied later when player extracts (not shown immediately, to keep vault total hidden)

### Patrol Interrupt
- `force_close()` method — called by GameScene when `HeatLevelUpEvent` fires during drain
- Sets state to RESULT immediately
- Log message: "Security patrol — connection interrupted"
- After patrol combat resolves, player can walk back and re-enter vault

### Voluntary Disconnect
- Q or Escape — sets state to RESULT
- Player can walk back to vault and press E to re-enter (resumes with accumulated credits)

### Input
- **UP / W** (hold): impulse upward (toward 1.0)
- **DOWN / S** (hold): impulse downward (toward 0.0)
- **Q / Escape**: voluntary disconnect
- **F1**: open help catalog (freeze overlay, same pattern as other overlays)

### UI Layout (centered panel, ~500×380px)
```
┌──────────────────────────────────────────┐
│  ◆ VAULT DRAIN                           │
│                                          │
│  ┌──┐   ╔══════════════════════════╗     │
│  │  │   ║  CREDITS: ¥347          ║     │
│  │▓▓│   ║  MULTIPLIER: 1.45×      ║     │
│  │▓▓│   ║                          ║     │
│  │▓▓│   ║  ─── LAST CHECK ───     ║     │
│  │▒▒│   ║    ★ PERFECT            ║     │
│  │  │   ║                          ║     │
│  │  │   ╚══════════════════════════╝     │
│  └──┘                                    │
│                                          │
│         [Q] Disconnect                   │
└──────────────────────────────────────────┘
```
- Left: vertical gauge with cursor marker + zone colors (green=perfect, yellow=good, orange=bad, red=fail)
- Right: credits earned (only going up, no total shown), multiplier, last check result
- **No progress bar, no "remaining" indicator** — player doesn't know how much is left
- Zone colors shift / pulse with heat level
- Screen tint / edge glow at high heat

### Music Integration
- Prepare `self._music_path` field and `MusicManager` integration hooks
- Karel will provide a `vault.mp3` track in `assets/audio/music/`
- On overlay start: crossfade to vault music (same pattern as hack scene)
- On overlay end: crossfade back to calm/action based on combat state

---

## 2. GameScene Integration (`scenes/game_scene.py`) — MODIFY

### New instance variables
```python
self._vault_overlay = None          # VaultOverlay | None
self._vault_container = None        # ContainerEntity | None (the vault)
self._vault_credits_banked: int = 0 # credits drained so far (across sessions)
self._vault_fully_drained: bool = False
# no forced_close flag — player can always re-enter after combat
```

### Launch — `_launch_vault(container)`
- Called when player presses E on the vault (`OpenContainerAction` on `is_objective` container)
- If `self._vault_forced_close`: refuse, log "vault connection permanently severed"
- If `self._vault_fully_drained`: refuse, log "vault already drained"
- Create VaultOverlay with `container.credits`, `self._vault_credits_banked`, player, heat_system, difficulty
- Store `self._vault_container = container`
- Switch music to vault track (or duck if no track yet)
- Stop auto-repeat movement

### Input handling — add before existing overlay checks (after help catalog)
```python
if self._vault_overlay is not None:
    for event in events:
        self._vault_overlay.handle_event(event)
    return  # exclusive
```

### Update
```python
if self._vault_overlay is not None:
    self._vault_overlay.update(dt)
    if not self._vault_overlay.is_active:
        self._vault_overlay = None
```

### Render
```python
if self._vault_overlay is not None:
    self._vault_overlay.render(screen)
```

### Completion callback — `_on_vault_complete(credits_this_session, fully_drained)`
- `self._vault_credits_banked += credits_this_session`
- `self._vault_fully_drained = fully_drained`
- **Do NOT award credits to player yet** — only on extraction (elevator)
- Log credits drained this session
- Restore music
- **Do NOT mark container as opened** (player can always re-enter)

### Vault re-entry
When player presses E on vault again:
- If `fully_drained` → log "vault empty"
- Otherwise → launch VaultOverlay again with updated `credits_already_drained`

### Force-close on heat level-up
In `_on_heat_level_up()`, add at the top:
```python
if self._vault_overlay is not None:
    self._vault_overlay.force_close()
    # patrol spawn continues as normal below
    # after player deals with the patrol, they can re-enter the vault
```

### Heat during vault drain
The VaultOverlay calls `heat_system.add_heat()` directly on each periodic check. This may trigger `HeatLevelUpEvent` → `_on_heat_level_up()` → `force_close()`. The event system is synchronous, so this works naturally.

### Extraction (elevator on floor 3)
When player uses elevator on floor 3 (`_on_elevator` or E-press handler):
- Award `self._vault_credits_banked` to player
- If `self._vault_fully_drained`: add bonus (+25%)
- Log total credits
- Trigger `_trigger_game_over(victory=True)`

---

## 3. Vault Room Layout — MODIFY `scenes/game_scene.py` `_load_floor()`

### Current behavior (floor 3):
- Elevator position → set to WALL
- Vault placed on adjacent floor tile

### New behavior (floor 3):
- **Keep elevator** as `ELEVATOR_CLOSED` (don't convert to WALL)
- Place vault on a **different floor tile in the vault room** — NOT adjacent to elevator
- Ensure vault and elevator are ≥2 tiles apart so E doesn't trigger both

### Implementation:
```python
if depth == FLOORS_PER_RUN:
    ex, ey = result.stair_pos  # elevator stays as elevator
    # Find the room containing the elevator
    vault_room = next(r for r in result.rooms if r.contains(ex, ey))
    # Find a floor tile in the room that is NOT adjacent to elevator
    candidates = []
    for ty in range(vault_room.y, vault_room.y + vault_room.h):
        for tx in range(vault_room.x, vault_room.x + vault_room.w):
            if not self.floor.dungeon_map.is_walkable(tx, ty):
                continue
            dist = abs(tx - ex) + abs(ty - ey)
            if dist >= 3:  # at least 3 tiles from elevator
                candidates.append((tx, ty))
    vault_x, vault_y = random.choice(candidates)  # or farthest from elevator
    obj_credits = self.difficulty.objective_credits
    self.floor.add_container(
        ContainerEntity(vault_x, vault_y, credits=obj_credits,
                        is_objective=True, name=t("entity.corp_vault.name"))
    )
```

### Elevator behavior on floor 3:
In the elevator E-press handler, check `if self.player.floor_depth == FLOORS_PER_RUN`:
- Play elevator animation as normal
- But instead of loading next floor → award vault credits + trigger victory

---

## 4. Action Resolver — Intercept in GameScene (NO changes to `action_resolver.py`)

In GameScene's player action handling, intercept `OpenContainerAction` on objective containers BEFORE sending to resolver (same pattern as hack minigame intercept):
```python
if isinstance(action, OpenContainerAction) and action.container.is_objective:
    if not self._vault_forced_close and not self._vault_fully_drained:
        self._launch_vault(action.container)
        return  # don't resolve through normal path
    # If forced/drained, let resolver handle it (posts ObjectiveEvent or shows message)
```

The resolver's existing objective handling stays as fallback for edge cases.

---

## 5. Settings Constants (`core/settings.py`) — MODIFY

```python
# Vault drain minigame
VAULT_CHECK_INTERVAL:    float = 1.5    # seconds between position checks
VAULT_IMPULSE:           float = 0.8    # velocity added per frame while key held
VAULT_DAMPING:           float = 0.92   # velocity damping per frame (at 60 FPS)
VAULT_DRIFT_SIGMA:       float = 1.2    # base random drift strength
VAULT_DRIFT_HEAT_SCALE:  float = 0.3    # drift increase per heat level above 1
VAULT_DRIFT_FINALE_MULT: float = 2.0    # drift multiplier for last 20% of credits
VAULT_ZONE_PERFECT:      float = 0.08   # |pos-0.5| threshold for Perfect
VAULT_ZONE_GOOD:         float = 0.20   # |pos-0.5| threshold for Good
VAULT_ZONE_BAD:          float = 0.35   # |pos-0.5| threshold for Bad
VAULT_DRAIN_SECONDS:     float = 30.0   # base time for full drain at 1.0x mult
VAULT_MULT_MIN:          float = 0.3    # minimum drain multiplier
VAULT_MULT_MAX:          float = 2.0    # maximum drain multiplier
VAULT_FULL_DRAIN_BONUS:  float = 0.25   # +25% credits for draining everything
VAULT_RESULT_PAUSE:      float = 0.8    # seconds to show result before closing

# Heat per vault check by zone
VAULT_HEAT_PERFECT:      int = 4
VAULT_HEAT_GOOD:         int = 6
VAULT_HEAT_BAD:          int = 8
VAULT_HEAT_FAIL:         int = 14

# Multiplier changes per vault check by zone
VAULT_MULT_PERFECT:      float =  0.15
VAULT_MULT_GOOD:         float =  0.05
VAULT_MULT_BAD:          float = -0.10
VAULT_MULT_FAIL:         float = -0.20
```

---

## 6. Difficulty Integration (`core/difficulty.py`) — MODIFY

Add to `Difficulty` dataclass:
```python
vault_drift_mult: float = 1.0   # multiplier on drift sigma
```

- EASY: `vault_drift_mult=0.7`
- NORMAL: `vault_drift_mult=1.0` (default)
- HARD: `vault_drift_mult=1.3`

---

## 7. i18n Keys (`core/i18n.py`) — MODIFY

Add to all 3 languages (en/cs/es):
```
vault.overlay.title          — "VAULT DRAIN" / "VYSÁVÁNÍ TREZORU" / "DRENAJE DE BÓVEDA"
vault.overlay.credits        — "Credits: ¥{n}" / "Kredity: ¥{n}" / "Créditos: ¥{n}"
vault.overlay.multiplier     — "Multiplier: {n}×" / "Multiplikátor: {n}×" / "Multiplicador: {n}×"
vault.overlay.disconnect     — "[Q] Disconnect" / "[Q] Odpojit" / "[Q] Desconectar"
vault.overlay.drained        — "FULLY DRAINED" / "KOMPLETNĚ VYSÁTO" / "COMPLETAMENTE DRENADO"
vault.overlay.severed        — "Connection severed!" / "Spojení přerušeno!" / "¡Conexión cortada!"
vault.zone.perfect           — "PERFECT" / "PERFEKTNÍ" / "PERFECTO"
vault.zone.good              — "GOOD" / "DOBRÉ" / "BUENO"
vault.zone.bad               — "BAD" / "ŠPATNÉ" / "MALO"
vault.zone.fail              — "FAIL" / "SELHÁNÍ" / "FALLO"
log.vault_drained            — "Drained ¥{credits} from vault" / "Vysáto ¥{credits} z trezoru" / "Drenado ¥{credits} de la bóveda"
log.vault_bonus              — "Full drain bonus: +¥{bonus}" / "Bonus za úplné vysátí: +¥{bonus}" / "Bono por drenaje total: +¥{bonus}"
log.vault_interrupted        — "Security patrol — connection interrupted!" / "Bezpečnostní hlídka — spojení přerušeno!" / "¡Patrulla — conexión interrumpida!"
log.vault_empty              — "Vault already empty" / "Trezor je prázdný" / "La bóveda está vacía"
log.vault_extract            — "Extracted with ¥{credits}" / "Extrakce s ¥{credits}" / "Extracción con ¥{credits}"
hint.elevator_extract        — "[E] Extract" / "[E] Extrakce" / "[E] Extracción"
tutorial.vault.title         — "Corp Vault" / "Trezor korporace" / "Bóveda corporativa"
tutorial.vault.text          — "Hold cursor in optimal zone..." (see below)
help_catalog.vault.*         — (see section 8)
```

Tutorial text (simple, 5 bullet points):
```
en: "Hold the cursor in the optimal zone for faster credit drain.\nHeat increases with each check — worse position means more heat.\nThe more heat, the harder it is to maintain the connection.\nSecurity patrols may interrupt you if heat rises too high.\nCredits are only yours once you extract via the elevator.\nDisconnect anytime with [Q] — you can return later."
```

---

## 8. Help Catalog — NEW "VAULT" tab (`rendering/ui/help_catalog.py`) — MODIFY

New tab **VAULT** (after HACKING):
```python
("help_catalog.vault.header", [
    # HOW IT WORKS
    "help_catalog.vault.cursor",         # Use ↑↓/WS to keep cursor in the green zone
    "help_catalog.vault.checks",         # Position checked every 1.5s — Perfect/Good/Bad/Fail
    "help_catalog.vault.multiplier",     # Better checks = faster drain multiplier
    "help_catalog.vault.heat",           # Each check increases heat
    # DANGER
    "help_catalog.vault.volatility",     # Higher heat = more cursor drift
    "help_catalog.vault.patrol",         # Heat level-up spawns a patrol — kicks you out
    "help_catalog.vault.finale",         # Final portion is harder (more drift)
    # REWARDS
    "help_catalog.vault.reenter",        # Disconnect with Q, return later
    "help_catalog.vault.bonus",          # Drain everything for a bonus
    "help_catalog.vault.credits_on_leave", # Credits only awarded when you extract!
    "help_catalog.vault.extract",          # Use elevator to extract with your credits
]),
```

---

## 9. Tutorial Step (`rendering/ui/tutorial_overlay.py`) — MODIFY

Add tutorial step `"vault"`:
- Triggered when player first opens the vault (in `_launch_vault`)
- Simple text panel (same style as other tutorial steps)
- Content: 4-5 short bullets:
  1. Keep cursor in the green zone for faster drain
  2. Heat increases — worse checks = more heat
  3. More heat = harder to control
  4. Patrols may appear if heat rises
  5. Press Q to disconnect, come back later
- Procedural illustration: vertical gauge with zone colors + cursor marker

---

## 10. Cheat Menu (`rendering/ui/cheat_menu.py`) — MODIFY

Add a **VAULT** section to the cheat menu:
- **"Open Vault Overlay"** — spawns a test ContainerEntity with `is_objective=True` at player position and launches VaultOverlay
- **"Set Vault Credits"** — presets: 100 / 300 / 500
- **"Drain 50%"** — sets `_vault_credits_banked` to half of total
- **"Reset Vault"** — clears all vault state (banked credits, forced flag)

This lets Karel test the minigame without playing to floor 3.

---

## 11. File Change Summary

| File | Action | What |
|------|--------|------|
| `minigame/vault_scene.py` | **NEW** | VaultOverlay class (~300 lines) |
| `scenes/game_scene.py` | MODIFY | Vault overlay lifecycle, launch/complete/re-entry, floor-3 elevator=extract, vault room layout, force-close on heat level-up |
| `core/settings.py` | MODIFY | Add `VAULT_*` constants (~20 lines) |
| `core/difficulty.py` | MODIFY | Add `vault_drift_mult` field + presets |
| `core/i18n.py` | MODIFY | Add ~25 vault i18n keys × 3 languages |
| `rendering/ui/help_catalog.py` | MODIFY | Add VAULT tab |
| `rendering/ui/tutorial_overlay.py` | MODIFY | Add "vault" tutorial step |
| `rendering/ui/cheat_menu.py` | MODIFY | Add vault test section |

`combat/action_resolver.py` — NO changes needed (intercept happens in GameScene).

---

## 12. Verification

1. **Cheat menu test**: F11 → spawn vault → open → verify minigame launches
2. **Cursor tracking**: verify UP/DOWN with inertia, drift pushes away, zones visually distinct
3. **Periodic checks**: verify zone flash every 1.5s, multiplier changes, heat added
4. **Credit drain**: verify credits counter goes up, rate scales with multiplier
5. **Voluntary disconnect (Q)**: verify overlay closes, can walk back and re-enter
6. **Re-entry**: verify credits_banked persists, drain resumes from where left off
7. **Patrol interrupt**: set heat near level boundary → verify patrol kicks from minigame, then after combat player can re-enter
8. **Full drain**: verify bonus applied on extraction
9. **Extraction**: walk to elevator on floor 3 → verify credits awarded + victory
10. **No credits before extraction**: disconnect and check player.credits unchanged
11. **Vault+elevator spacing**: verify E near vault doesn't trigger elevator and vice versa
12. **Tutorial**: verify vault tutorial shows on first vault interaction
13. **Help catalog**: verify VAULT tab content
14. **i18n**: switch language, verify all vault strings
15. **Difficulty**: verify drift lower on Easy, higher on Hard
16. **Music**: verify hooks exist (actual track TBD by Karel)
17. **pytest**: run existing tests, ensure no regressions
