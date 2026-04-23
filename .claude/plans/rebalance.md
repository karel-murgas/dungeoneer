# Rebalance Plan: Dynamic Spawning + Loot/Credit Economy

## Context

All enemies currently spawn at floor generation time in `dungeon_generator.py`. This rebalance:
1. Moves to **dynamic spawning on room reveal** — enemies appear when player's FOV first touches a room
2. Encounter composition scales with heat level using a "pack vs elite" model (no explicit tables)
3. Credit economy: vault (~500) is the big prize, containers are tempting, enemy kills are symbolic
4. Supply balance: enough ammo/heal for skilled play, temporary shortages OK, no long-term deficit
5. No heat constant changes in this rebalance

### Decisions from Karel
- Max 2 ranged per encounter; check by `weapon.range_type == RANGED`, not `is_drone`
- Start room CAN have enemies; end room ALWAYS has enemies (guaranteed encounter)
- No explicit encounter tables — procedural "pack vs elite" model, parameterized by tier
- Vault = ~500 credits; containers = tempting loot nodes; enemy credits = symbolic
- Container base credits are kept for `use_minigame=False` path; when hacking, credits already come only from hack CREDITS nodes (no code change needed)
- No heat changes in this rebalance

### Budget summary (Normal, 3-floor run, ~10 rooms/floor)
- **Enemies:** ~30-35 per run (dynamic spawning, ~75% rooms have encounters)
- **Ammo:** ~80 rounds available (10 start + ~38 enemy drops + ~32 hack nodes) for ~80 needed. Tight — forces locker use.
- **Healing:** ~83 HP from drops+hacks (boosted via hack pool); ~120-160 damage taken. Tight — no hoarding.
- **Credits:** ~40 enemies + ~90 hack nodes + ~400 vault (partial drain) ≈ 530 total. Vault dominates.

### Housekeeping (Chunk 4)
- Move `.claude/plan_vault_minigame.md` → `.claude/plans/plan_vault_minigame.md`

---

## Chunk 1: Room Reveal Infrastructure

**Goal:** Detect when a room is first seen via FOV. No spawning changes yet.

### Files to modify

1. **`world/room.py`** — add `revealed: bool = False` to Room dataclass

2. **`world/floor.py`** — add `rooms: list[Room] = []` attribute; add `room_for_tile(x, y) -> Room | None` helper

3. **`core/event_bus.py`** — add `RoomRevealedEvent(room)` event

4. **`world/fov.py`** — extend signature: `compute_fov(x, y, dungeon_map, rooms=None)`. After updating `explored`, iterate unrevealed rooms: if `dungeon_map.visible[iy:iy+ih, ix:ix+iw].any()` → set `room.revealed = True`, post `RoomRevealedEvent(room)`

5. **`scenes/game_scene.py`** — store `result.rooms` on `self.floor.rooms`; pass `rooms=self.floor.rooms` to all `compute_fov()` calls; subscribe to `RoomRevealedEvent` with a logging no-op

### Verification
- Walk around, check log for RoomRevealedEvent on new rooms
- Re-entering a seen room does NOT re-fire
- First room fires on spawn (player FOV covers it)

---

## Chunk 2: Encounter System + Dynamic Spawning

**Goal:** Replace static spawning with dynamic room-reveal spawning. "Pack vs elite" encounter model.

### New file: `systems/encounter.py`

**Encounter generation — "pack vs elite" model:**

Uses existing `_ENEMY_POOL = {1: [...], 2: [...], 3: [...]}`. Adding new enemies just means adding to the pool.

```
Max tier from heat (existing _TIER_CAP): heat 1-2→1, heat 3-4→2, heat 5→3
Heat 4 also has ~10% chance to unlock tier 3.
```

**Two branches, matching the source design document:**

**Branch A — "Pack" (all tier 1, no leader):**
- At heat 1-2: always this branch (max_tier=1, so no elite option)
- At heat 3+: ~40% chance this branch
- Size: heat 1→1, heat 2→1-2, heat 3→2-3, heat 4→3, heat 5→3-4
- All enemies randomly picked from `_ENEMY_POOL[1]`

**Branch B — "Elite" (1 high-tier leader + tier 1 fillers):**
- At heat 3+: ~60% chance this branch
- Leader: 1 enemy from `_ENEMY_POOL[max_tier]`
- Filler count inversely proportional to leader tier:
  - Tier 3 leader → 0 fillers (solo). At heat 5: 50% chance of +1 tier 1 filler
  - Tier 2 leader → 0-1 fillers at heat 3; 1-2 fillers at heat 4-5
- Fillers: random from `_ENEMY_POOL[1]`

**This matches the source file (Rebalanc.md):**
- Heat 1: 1 lone tier 1 (pack of 1)
- Heat 2: 1-2 tier 1 (small pack)
- Heat 3: tier 2 solo/+1 filler OR 2-3 tier 1 pack
- Heat 4: tier 2 + 1-2 tier 1, OR 3 tier 1, OR very rarely tier 3
- Heat 5: tier 3 (solo/+1), OR tier 2 + 1-2 tier 1, OR 3-4 tier 1

**Ranged cap (per encounter):** After building the enemy list, instantiate via factories, count those with `equipped_weapon.range_type == RANGED`. If >2, replace last ranged with a random melee enemy of the same or lower tier. Melee = any enemy from the pool whose factory produces `range_type != RANGED`.

**EncounterSystem class:**
- `__init__(floor, heat_system, difficulty, end_room)` — subscribes to `RoomRevealedEvent`
- `on_room_revealed(event)`:
  - `room is end_room` → always spawn (skip empty roll)
  - Small rooms (inner area < `ENCOUNTER_MIN_ROOM_AREA`) → skip
  - Else: `random() < difficulty.empty_room_chance` → skip
  - Generate encounter via pack/elite, spawn in `CombatState`
  - Post `LogMessageEvent` with encounter warning
- `spawn_patrol(near_x, near_y)` — for heat level-up patrols (same generation logic, placed 4-8 tiles from player)

### Files to modify

1. **`systems/encounter.py`** — NEW FILE
2. **`world/dungeon_generator.py`** — remove enemy spawning loop (lines 135-151); keep `generate()` signature for compat but ignore `guards`/`drones`/`tier_cap`
3. **`core/difficulty.py`** — add `empty_room_chance: float` (Easy=0.35, Normal=0.25, Hard=0.15)
4. **`scenes/game_scene.py`** — create `EncounterSystem` in `_load_floor()` after floor+heat; remove enemy factories dict and instantiation loop; remove guards/drones/tier_cap from `gen.generate()` call; update `_on_heat_level_up()` to use `encounter_system.spawn_patrol()`
5. **`core/settings.py`** — add `ENCOUNTER_MIN_ROOM_AREA = 9`, `ENCOUNTER_PACK_CHANCE = 0.4`, `ENCOUNTER_T3_CHANCE_AT_H4 = 0.10`

### Verification
- Rooms start empty; FOV reveal spawns enemies
- Heat 1: single tier 1. Heat 2: 1-2 tier 1.
- Heat 3: ~40% get pack of 2-3 tier 1, ~60% get solo tier 2 with maybe 1 filler
- Heat 5: tier 3 solo, OR tier 2 + fillers, OR tier 1 pack of 3-4
- End room always has enemies
- Max 2 ranged per encounter
- No encounter with 2+ tier 3 enemies
- Tier 1 packs appear at all heat levels
- Patrol spawns on heat level-up still work

---

## Chunk 3: Loot & Credit Economy Rebalance

**Goal:** Vault = big prize, containers = tempting, enemies = symbolic credits. Enough supply for skilled play.

### Files to modify

1. **`core/difficulty.py`**:
   - `objective_credits` (vault): Easy=400, Normal=**500**, Hard=600
   - `containers_per_floor`: Easy 4→**5**, Normal 3→**4**, Hard 2→**3** (more enemies need more supply)

2. **`entities/enemy.py`** — reduce ONLY credit drops (keep item drop rates unchanged for supply):

   | Enemy | Credits old→new | Chance old→new |
   |-------|----------------|---------------|
   | Guard | (3,10)→(1,5) | 50%→30% |
   | Drone | (8,18)→(2,6) | 50%→30% |
   | Dog | (2,8)→(1,3) | 30%→20% |
   | Heavy | (10,20)→(3,8) | 60%→40% |
   | Turret | (5,12)→(2,6) | 40%→30% |
   | Sniper | (12,25)→(4,10) | 60%→40% |
   | Riot | (15,30)→(5,12) | 70%→50% |

3. **`minigame/hack_grid_generator.py`** (`_loot_pool`) — boost healing availability:
   - HEAL: 3→**4** (more healing from containers)
   - MYSTERY: 2→**1** (freed weight goes to HEAL)
   - Rest unchanged. Total still 20.

4. **No changes to `_make_container` credits** — container.credits (5-25) is already only awarded when `use_minigame=False`. When hacking is ON, credits come only from hack CREDITS nodes. Both paths work correctly as-is.

### Verification
- Enemy kills: 1-5 credits (symbolic)
- Hacking a container: 1-2 credit nodes → 10-80 credits (variable, sometimes jackpot — tempting)
- Vault: ~350-500 earned via drain minigame
- Ammo: tight but sufficient for skilled play; temporary shortages force locker use
- Healing: doesn't pile up past 2-3 items

---

## Chunk 4: Polish, i18n & Housekeeping

**Goal:** Log messages, translations, memory updates, file moves.

### Files to modify

1. **`core/i18n.py`** — add keys in en/cs/es:
   - `log.room_encounter` — "Hostiles detected!" / "Nepřátelé detekováni!" / "¡Hostiles detectados!"
   - `log.room_clear` — "Room clear." / "Místnost čistá." / "Habitación despejada."

2. **`systems/encounter.py`** — post `LogMessageEvent(t("log.room_encounter"))` when enemies spawn

3. **`rendering/ui/help_catalog.py`** — update ENEMIES / HEAT tabs if needed

4. **`.claude/memory/arch.md`** — add `systems/encounter.py`, `RoomRevealedEvent`

5. **`.claude/memory/state.md`** — update with rebalance status

6. **File moves:**
   - Move `.claude/plan_vault_minigame.md` → `.claude/plans/plan_vault_minigame.md`

### Verification
- All 3 languages show encounter messages
- At least 5-7 combat rooms per floor on Normal
- Memory files accurate
- Full playtest Easy/Normal/Hard

---

## Chunk Dependencies

```
Chunk 1 (Room Reveal)  ← foundation
   ↓
Chunk 2 (Encounters)   ← needs RoomRevealedEvent
   ↓
Chunk 3 (Loot/Credits) ← different files, but test with encounters
   ↓
Chunk 4 (Polish)       ← needs encounter.py for log messages
```

## Instructions for Sonnet sessions

Each chunk = one session. Provide:
1. This plan file
2. Which chunk to implement
3. "Read all listed files before editing. Run `pytest` after. Update `.claude/memory/` only in Chunk 4."