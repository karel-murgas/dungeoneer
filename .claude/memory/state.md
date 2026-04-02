---
name: Project state and roadmap
description: Current development phase, what's complete, what are stubs, and the phase roadmap
type: project
---

## Current State (2026-03-31, in dev)

**Phase 1 MVP ✅ + Phase 2 UI Polish ✅ + Phase 3 core content ✅ complete.**

### New (2026-03-31) — Vault drain minigame
- **VaultOverlay** (`minigame/vault_scene.py`) — cursor-tracking credit-drain minigame on floor 3
- 1D vertical cursor (0–1), physics: velocity + VAULT_DAMPING damping + Gaussian drift
- Drift scales with heat level and difficulty.vault_drift_mult (Easy=0.7×, Hard=1.3×)
- Last 20% of total credits: drift×2.0 (player doesn't see % but feels it)
- **Zone checks** every 1.5s: Perfect/Good/Bad/Fail → adjust multiplier [0.3–2.0] + add heat
- Credits drain at base_rate × multiplier; player sees earned total only (no remaining/total)
- Voluntary disconnect: Q/Esc — player can re-enter vault later
- Patrol interrupt: force_close() called from `_on_heat_level_up` — re-entry still allowed
- Vault fully drained → +25% bonus applied at extraction
- **GameScene integration**: _vault_overlay/container/credits_banked/fully_drained state vars
  - Floor 3: elevator KEPT for extraction (E→Extract); vault placed ≥3 tiles away in same room
  - Extraction: _elevator_descend on floor 3 awards vault_credits_banked (+ bonus) → victory
  - OpenContainerAction on is_objective → _launch_vault(); bypass action_resolver
  - LMB on objective container also routes to _launch_vault()
  - music.duck(0.15) on open, unduck on complete
- **i18n**: `vault.*`, `log.vault_*`, `hint.elevator_extract`, `tutorial.vault.*`, `help_catalog.vault.*`, `cheat.*vault*` (en/cs/es)
- **help_catalog**: VAULT tab (_TAB_VAULT=9) with zone gauge illustration
- **tutorial_overlay**: "vault" step added; procedural gauge illustration
- **cheat_menu**: VAULT section — open overlay, set credits 100/300/500, drain 50%, reset
- **settings**: VAULT_* constants in core/settings.py; vault_drift_mult in Difficulty
- Music: vault.mp3 plays from first vault open until run ends (death or escape); ducks 0.15 while overlay is open; MusicManager.start_vault() on ch2, idempotent on re-entry

### New (2026-03-29) — Heat system
- **HeatSystem** (`systems/heat.py`) — 5 levels (GHOST/TRACE/ALERT/PURSUIT/BURN), stored on `Player.heat` (0–500)
- **Sources**: +1/combat round (TurnEndEvent), +2/hacked node, +10/failed hack — hack heat applied at minigame end
- **Effects**: tier cap for floor generation (lv1-2 → tier1, lv3-4 → tier2, lv5 → tier3); hack time modifier (2−level seconds, min 4s); patrol spawn on level-up (1-2 enemies, CombatState, near player)
- **COOLANT loot node** (`LootKind.COOLANT`) — reduces heat by 12 at hack end; teal hexagon icon; +2 heat still applies for hacking it; added to `_loot_pool` weight 1
- **HUD heat bar** — center-top, 180×14px, fills per level (resets visually at level-up); level name shown below in level colour; pulse at level 5
- **Cheat menu** — Heat Level section, set to any level (1–5)
- **Events**: `HeatChangeEvent`, `HeatLevelUpEvent`, `HackNodesCollectedEvent` in event_bus.py
- **i18n**: `hud.heat_level`, `log.heat_level_up`, `hack.status.purge`, `hack.overlay.purge_*`, `hack.loot.coolant`, `cheat.section.heat`, `cheat.heat.level1-5` (en/cs/es)
- Balance numbers TBD in rebalance; tier cap first kicks in at floor load (not mid-floor), patrol arrives mid-floor on level-up

### New (2026-03-29) — 5 new enemy types + tier system
- **7 enemy types** across 3 tiers; each Enemy has `tier: int` and `sprite_key: str`
- **Tier 1**: Guard (existing), Drone (existing), Dog (K9 — 2 moves/turn, 1 attack, k9_bite 1–3 dmg)
- **Tier 2**: Heavy (pistol, def=3, approaches to dist~4, never retreats), Turret (immobile, 2 shots/turn, LOS lost → Idle)
- **Tier 3**: Sniper Drone (rifle, aim=6, always retreats, dist~7), Riot Guard (combat_knife, def=4)
- **AI flags on Enemy**: `can_move`, `preferred_dist`, `always_retreat`, `retreat_when_close`, `actions_per_turn`, `max_attacks_per_turn`
- **TurnManager** extended: multi-action loop (`actions_per_turn`, `max_attacks_per_turn`)
- **AI states.py**: `_turret_action` (immobile); `_drone_action` reads enemy flags; weapon range from `equipped_weapon.range_tiles`
- **Tier-aware spawn**: `dungeon_generator.generate(tier_cap=N)` — `_ENEMY_POOL` dict; default `tier_cap=1` (no change yet)
- **Procedural sprites**: dog, heavy, turret, sniper_drone, riot_guard added to `procedural_sprites.py`
- **EntityRenderer**: dispatches by `sprite_key`; `"drone_animated"` = spritesheet, others = procedural
- **Cheat menu (F11)**: all 7 enemy types spawnable
- **i18n**: entity + item keys added for all new types (en/cs/es); new weapon `k9_bite`

### New (2026-03-22) — melee power-charge minigame
- **MeleeOverlay** (`minigame/melee_scene.py`) — in-world power bar overlay for melee attacks
- Hold F/LMB → bar oscillates sinusoidally (0.0–1.0); release at peak = max damage
- `power` maps to `damage_min..damage_max`; crit zone at top 5% (gold strip)
- Oscillation frequency accelerates over time; auto-releases at 2.5s timeout
- Difficulty scales oscillation speed: Easy=0.75×, Normal=1.0×, Hard=1.3×
- `calc_melee_aimed(attacker, target, power)` in `combat/damage.py`
- `MeleeAttackAction.power` optional field; resolver uses aimed calc when set
- Settings toggle: "Melee" ON/OFF in SettingsOverlay (default ON); OFF = random roll as before
- Settings flow: `use_melee_minigame` carried through MainMenuScene → GameScene → GameOverScene
- Tutorial step "melee" triggers when player equips a melee weapon via weapon picker
- Help catalog: new MELEE tab (7th tab) with illustration
- F1 help overlay during charging (freezes bar)
- i18n: `melee.*` keys (en/cs/es); `settings.gameplay.melee`; `tutorial.melee.*`; `help_catalog.melee.*`

### New (2026-03-22) — minimap overlay
- **MinimapOverlay** (`rendering/ui/minimap_overlay.py`) — fullscreen dungeon minimap toggle on **M** key
- Shows explored tiles vs fog of war (unexplored = black), walls (dark grey), floors (grey, brighter if visible)
- Colour-coded entities: player (cyan), visible enemies (red), unopened chests (yellow), elevator/vault (blue), items on floor (dim dots)
- Legend bar at bottom; close with M or Esc
- i18n: `minimap.*` keys (en/cs/es); help_screen + help_catalog EXPLORATION tab updated

### New (2026-03-22) — map size setting
- **SettingsOverlay** — new GAMEPLAY row: "Map" toggle (Large / Small)
- Large = 60×40 (default, unchanged), Small = 40×26 (~60% area)
- Enemy/container counts stay the same → higher density on small map
- Setting carried through MainMenuScene → GameScene → GameOverScene → back to MainMenuScene
- `settings.py`: `MAP_WIDTH_SMALL`, `MAP_HEIGHT_SMALL`
- i18n: `settings.gameplay.map_size`, `menu.map_size.large`, `menu.map_size.small` (all 3 languages)

### New (2026-03-22) — elevator replaces stairs
- **Floor descent** now uses an **elevator** instead of stairs
- `TileType.ELEVATOR_CLOSED` / `ELEVATOR_OPEN` — wall-like tiles (not walkable when closed)
- **Elevator placement**: spawns in room perimeter wall with exactly 1 cardinal floor neighbor (accessible from one side only)
- **Animation sequence**: press [E] when adjacent → doors open (0.35s) → player enters (0.25s) → doors close (0.4s) → descend to next floor
- **Tile indices**: closed=36, open=37 (Dithart tileset)
- **Sounds**: `elevator_open` (hiss+slide+ding), `elevator_close` (hiss+slide+thud)
- `ElevatorAction` (adjacency check) + `ElevatorEvent(elevator_x, elevator_y)` — `StairAction`/`StairEvent` kept for compat
- **Final floor**: elevator replaced with wall, Corp Vault placed on adjacent floor tile
- **i18n**: `hint.elevator_descend` in en/cs/es; help catalog and tutorial text updated (stairs→elevator)
- **Help catalog**: illustration shows elevator tile instead of stair tile
- **Tutorial overlay**: elevator tile + `[E] Elevator` label

### In progress (2026-03-20) — tutorial system
- **Tutorial overlay** — `rendering/ui/tutorial_overlay.py`; `TutorialManager` (tracks seen steps per run) + `TutorialOverlay` (blocking centred panel, procedural illustrations per step)
- **5 steps**: `movement` (game start), `enemy` (first visible enemy), `container` (first container interaction), `ammo` (first ranged weapon), `medipack` (first consumable in inventory)
- **Opt-in** (default OFF): toggle in SettingsOverlay under GAMEPLAY → Tutorial [ON/OFF]
- **i18n**: `tutorial.*` keys in en/cs/es; `settings.gameplay.tutorial`, `tutorial.continue`, `menu.tutorial_on/off`
- **GameScene**: `use_tutorial` param → `TutorialManager(enabled=)`; triggers added at alert-banner sites (enemy), container validate, player-turn start (ammo/medipack); routing in `handle_events` mirrors aim/heal overlay pattern

### Latest batch (2026-03-20) — bugfixes & polish
- **Heal minigame** — 5-tier scoring (Perfect +20% / Great +10% / Good ±0% / Poor −10% / Miss −20%); press + release timing both scored; F1 help updated with SCORING section; hint text shown in overlay
- **Overheal confirm dialog** — H on an item that would exceed max HP now shows confirm dialog before launching heal overlay; uses `QuitConfirmDialog(key_prefix="overheal_confirm")`
- **Cheat menu** (F11) — new `rendering/ui/cheat_menu.py`; keyboard + mouse nav; spawn items/enemies/chest, set/adjust HP, add credits
- **Classic hack scene removed** — `hack_scene.py` and `hack_generator.py` deleted; only grid variant (`hack_scene_grid.py`) remains; `main_hack.py` simplified
- **Auto-repeat movement** — hold arrow / WASD keys to move continuously (configurable initial delay + repeat period via `settings.py`)
- **Inventory UX** — single `[E] Use` button (equip/use unified); `[D] Drop` removed from button bar (still works via key)
- **Entity names i18n** — `entity.crate.name`, `entity.corp_vault.name` added
- **Log messages** — added `log.reload_full`, `log.reload_no_reserves`, `log.container_already_open`, `hint.stair_descend`, `log.descend`, `log.reloaded`, `log.equipped`, `log.dropped`, `log.credits_drop`

### Codebase cleanup (2026-03-20)
- `minigame/hack_common.py` — extracted shared neon palette, draw helpers, `make_loot_item()` (was duplicated in hack_scene.py + hack_scene_grid.py)
- `minigame/hack_routing.py` — extracted ~500 lines of pure geometry: port assignment, orthogonal edge routing, BFS fallback, segment clipping, path interpolation (was at bottom of hack_scene.py)
- Local auto-memory cleaned: only `user_karel.md` stays local, all project/reference/feedback in git-tracked `.claude/memory/`

### Phase 2 UI features (all working)
- WeaponPickerUI (key C) — keyboard + mouse, shows stats
- HelpScreen (F1) — localised key-binding overlay
- AlertBanner — animated `!` on first enemy sighting
- Localisation: en / cs, `t("key")` system

### New in dev (2026-03-16) — armor system
- `minigame/` — hacking minigame (HackScene, HackMap, HackParams, HackAudio)
- `items/ammo.py` — AmmoPickup item type (make_9mm/rifle/shotgun_ammo)
- `main_hack.py` — standalone dev entry point for minigame
- **Minigame integrated into GameScene** — opening a non-objective container launches HackScene;
  success → drops loot + credits at container pos; failure → spawns alert drone in CombatState near container with LOS to player
- **Armor system** — `items/armor.py` (Armor, make_basic_armor, defense_bonus=1); auto-equips on pickup, discards duplicate;
  Player.equipped_armor, Player.total_defence override; HUD + InventoryUI show armor slot;
  drops from chests + hack minigame (LootKind.ARMOR); sprite: "item_loot_armor"

### Stubs (framework only, not integrated)
- `cyberware/` — skeleton, not connected to combat
- `skills/` — empty directory
- `meta/` — stub

### Also in dev (2026-03-16) — main menu
- `scenes/main_menu_scene.py` — MainMenuScene: between-run menu with difficulty, loot mode, language picker
- `core/i18n.py` — Spanish (`"es"`) added; full i18n pass: menu.*, gameover.*, hud.*, inv.*, weapon_picker.*, item.*, entity.*, log.*, hack.* keys in all 3 languages
- `GameScene` now accepts `use_minigame: bool` — when False, containers open with random loot (no HackScene)
- `GameOverScene` — "Main Menu [R]" button now returns to MainMenuScene, carrying settings forward
- Entry point (`game.py`) starts with MainMenuScene instead of GameScene

### New in dev (post 2026-03-17) — grid hack minigame variant
- `minigame/hack_scene_grid.py` — HackGridScene: maze-grid (PCB/circuit-board) traversal variant
- `minigame/hack_grid_generator.py` — HackGridParams + generate_grid_map(); 11×7 logical grid
- `minigame/hack_grid_map.py` — HackGridMap data model; physical 2× grid (even=nodes, odd=corridors)
- `LootKind.MYSTERY` added to `hack_node.py` (resolves randomly on collection)
- `main_hack.py` updated: `python main_hack.py [easy|normal|hard] [grid|classic]`; **grid is now default**
- `rendering/procedural_sprites.py` — extended (63 lines added)
- `rendering/ui/hud.py`, `help_screen.py`, `main_menu_scene.py` — significant rework

### New (2026-03-20) — heal minigame settings
- **SettingsOverlay** — two new GAMEPLAY rows: "Healing" toggle (On/Off) and "Threshold" (80/90/100/110/120%) when On
- When heal minigame is OFF: H key applies flat `heal_amount` without overlay
- Threshold controls which items are shown as "safe" (no overheal warning): `heal_amount * thr <= missing`
  - 80% = confident player, more items shown green; 120% = cautious, fewer shown green
- `MainMenuScene._use_heal_minigame`, `._heal_threshold_pct` carry forward to `GameScene`
- `HUD(heal_threshold_pct=...)` constructor arg; same threshold logic in HUD display
- i18n: `settings.gameplay.heal`, `settings.gameplay.heal_threshold`, `menu.heal.threshold_pct` (all 3 languages)

### New (2026-03-18) — healing rhythm minigame
- `minigame/heal_scene.py` — HealOverlay: centred panel overlay; watches 2 heartbeat cycles (du-dum, du-dum), player matches 3rd; ±20% heal based on timing accuracy
- `audio/audio_manager.py` — added `heart_du`, `heart_dum` procedural sounds
- `core/settings.py` — HEAL_MIN/MAX_CYCLE_MS, HEAL_MIN/MAX_DU_GAP_MS, HEAL_BEAT_FLASH_MS, HEAL_ACCURACY_WINDOW, HEAL_RESULT_PAUSE, HEAL_RANGE
- `core/i18n.py` — heal.overlay.* and heal.help.* keys (3 languages)
- `rendering/ui/help_catalog.py` — new HEALING tab (6th tab)
- **GameScene**: H key now always launches HealOverlay; removed overheal confirm path; `_heal_overlay` state; `_launch_heal()` / `_on_heal_complete()` mirror aim overlay pattern

### New (post 2026-03-17) — aim minigame F1 help
- `minigame/aim_scene.py` — AimOverlay: F1 toggles full-screen help overlay (needle frozen)
  - Left col: HOW AIMING WORKS (mechanic bullets) + ARMOR section
  - Right col: CRITICAL HITS + CONTROLS (key bindings)
  - Small `[F1] help` hint rendered below the arc during aiming
- `core/i18n.py` — added `aim.help.*` keys (28 keys × 3 languages)
- `README.md` — new "Aiming minigame", "Critical hits", "Armor" sections

### i18n full pass (2026-03-17)
All user-visible strings now go through `t()`. Files updated: `items/weapon.py`, `items/consumable.py`, `items/ammo.py`, `items/armor.py`, `entities/enemy.py`, `entities/player.py`, `combat/action_resolver.py`, `scenes/game_scene.py`, `rendering/ui/hud.py`, `rendering/ui/inventory_ui.py`, `rendering/ui/weapon_picker.py`, `minigame/hack_scene.py`.

### New in dev (2026-03-17) — background music
- `audio/music_manager.py` — MusicManager: **equal-power** crossfade BGM on channels 0+1 (reserved); `pause()`/`resume()` for overlaid scenes
- `assets/audio/music/` — calm.mp3, action.mp3, hacking.mp3, menu.mp3 (copied from sources/music/)
- **GameScene**: calm on enter; action on enemy alert (! banner); calm back when all enemies Idle; stair descent = immediate calm; pauses on HackScene push, resumes on pop
- **HackScene**: streams hacking.mp3 via `pygame.mixer.music`; fadeout 300ms on exit
- **MainMenuScene**: streams menu.mp3 via `pygame.mixer.music`; fadeout 500ms on exit

## Phase Roadmap
1. **MVP** ✅ — dungeon gen, movement, basic combat, 2 enemy types, win/lose
2. **UI Polish** ✅ — weapon picker, help screen, alert banner, i18n, tileset
3. **Content** ← *current* — **main menu ✅**, more enemy/item variety, multi-floor polish, save/load
4. **Cyberware + Skills** — implants, action combining, status effects, complex AI
5. **Meta-progression** — skill web UI, JSON save, credits, run modifiers
6. **Polish** — animations, particles, audio, more content
