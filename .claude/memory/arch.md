---
name: Architecture quick-reference
description: Module map, key classes, tech stack constants — fast navigation without reading source
type: project
---

## Tech Stack Constants
- Window: **1280×720**, 60 FPS, tile **32px**, map **60×40** tiles
- Entry: `main.py` → `core/game.py` (`GameApp`) → `SceneManager` → scenes
- Deps: `pygame-ce ≥2.5.0`, `python-tcod ≥16.0.0` (FOV), `numpy ≥1.26.0`, `pytest ≥8.0.0`, `rembg[cpu]` (asset post-processing)
- Asset generation: `scripts/sd_generate.py` (SD WebUI API), `scripts/asset_postprocess.py` (rembg + PCA rotate + frame fill + downscale)
- Asset pipeline config: `.claude/imagegen.md`

## Module Map

```
dungeoneer/
├── core/
│   ├── game.py          — GameApp (main loop, window, clock)
│   ├── scene.py         — Scene ABC (on_enter, handle_events, update, render)
│   ├── scene_manager.py — SceneManager (push/pop/replace scenes)
│   ├── event_bus.py     — EventBus (pub/sub, typed events)
│   ├── settings.py      — Settings dataclass (LANGUAGE, difficulty, window)
│   ├── difficulty.py    — Difficulty presets (Easy/Normal/Hard)
│   ├── i18n.py          — t(key), set_language()
│   └── logging_setup.py — logs → dungeoneer.log
│
├── entities/
│   ├── entity.py        — Entity (x, y, char, color, name, blocks)
│   ├── actor.py         — Actor(Entity): hp, max_hp, attack, defence, total_defence property; equipped_weapon, inventory
│   ├── player.py        — Player(Actor): credits, ammo_reserves dict, equipped_armor (Armor|None)
│   ├── enemy.py         — Enemy(Actor): ai_brain, xp_value, loot_table
│   ├── item_entity.py   — ItemEntity (item on floor)
│   └── container_entity.py — ContainerEntity (lootable chest)
│
├── items/
│   ├── item.py          — Item dataclass (id, name, description, ItemType enum)
│   ├── weapon.py        — Weapon(Item): damage_dice, ammo_type, clip_size, range_tiles
│   ├── consumable.py    — Consumable(Item): heal_amount, overheal
│   ├── ammo.py          — AmmoPickup(Item): ammo_type, ammo_count; make_9mm/rifle/shotgun_ammo()
│   ├── armor.py         — Armor(Item): defense_bonus; make_basic_armor()
│   └── inventory.py     — Inventory: 8 slots, add/remove/find methods
│
├── combat/
│   ├── action.py        — Action ABC + all action subclasses (see API section)
│   ├── action_resolver.py — ActionResolver: resolve_move/melee/ranged/open_container + _auto_pickup
│   ├── turn_manager.py  — TurnManager: player turn → enemy turns, burst queue, delay logic
│   ├── damage.py        — damage formula: roll(weapon) + atk − total_defence, min 1
│   └── line_of_sight.py — raycast LOS check
│
├── ai/
│   ├── brain.py         — Brain: tick(actor, floor) → Action; owns state machine
│   ├── states.py        — BehaviorState: Idle (patrol) / Combat (chase+attack)
│   ├── pathfinder.py    — A* pathfinding
│   └── perception.py    — sight radius, LOS checks for enemies
│
├── world/
│   ├── dungeon_generator.py — BSP tree generator → DungeonMap
│   ├── map.py           — DungeonMap: tiles 2D array, entities list, items list
│   ├── floor.py         — Floor: wraps map + entity lists for a single depth level
│   ├── room.py          — Room dataclass
│   ├── tile.py          — Tile: walkable, transparent, explored, visible
│   └── fov.py           — FOV via python-tcod shadowcasting
│
├── rendering/
│   ├── renderer.py      — Renderer: orchestrates all sub-renderers
│   ├── camera.py        — Camera: world→screen offset
│   ├── tile_renderer.py — TileRenderer: Dithart tileset + autotile wall mapping
│   ├── entity_renderer.py — EntityRenderer: sprite or procedural fallback
│   ├── spritesheet.py   — Spritesheet loader/slicer
│   ├── procedural_sprites.py — coloured-square fallback sprites
│   ├── floating_numbers.py   — floating damage number animations
│   ├── range_overlay.py      — range highlight overlay
│   └── ui/
│       ├── hud.py         — HUD: HP, floor, weapon, ammo, credits
│       ├── combat_log.py  — CombatLog: scrolling message log
│       ├── inventory_ui.py— InventoryUI: 8-slot grid overlay
│       ├── weapon_picker.py — WeaponPickerUI (key C): keyboard+mouse weapon swap
│       ├── help_screen.py — HelpScreen: legacy key-binding overlay (unused, kept for reference)
│       ├── alert_banner.py — AlertBanner: animated ! on first enemy sighting
│       ├── quit_confirm.py — QuitConfirmDialog (Esc in-run): confirm/cancel return to main menu
│       ├── cheat_menu.py  — CheatMenuOverlay (F11): dev/debug overlay; keyboard+mouse; spawn items/enemies/chest, adjust HP/credits
│       ├── settings_overlay.py — SettingsOverlay: gear icon panel (difficulty, gameplay, audio, language)
│       ├── help_catalog.py — HelpCatalogOverlay (F1): tabbed help reference (Exploration/Combat/Shooting/Aiming/Hacking/Melee/Healing); open_tab(idx) for context-specific tab; used in MainMenu + GameScene + HackGridScene
│       ├── minimap_overlay.py — MinimapOverlay (key M): fullscreen dungeon minimap; explored tiles, fog of war, containers, elevator, vault, enemies, items
│       └── tutorial_overlay.py — TutorialManager (tracks seen steps) + TutorialOverlay (blocking panel, 6 steps incl. melee, procedural illustrations)
│
├── audio/
│   ├── audio_manager.py — AudioManager: listens to EventBus, plays SFX (procedural numpy); volume = vol × settings.SFX_VOLUME × settings.MASTER_VOLUME
│   ├── music_manager.py — MusicManager: equal-power crossfade BGM (calm↔action); channels 0+1 reserved; pause()/resume(); refresh_volume() for live updates
│   └── sound_events.py  — sound event types
│
├── assets/audio/music/  — calm.mp3, action.mp3, hacking.mp3, menu.mp3 (copied from sources/music/)
│
├── scenes/
│   ├── main_menu_scene.py — MainMenuScene(Scene): hub with Start/Quit + ⚙ Settings + ? Help icons; all config in SettingsOverlay; ? opens HelpCatalogOverlay
│   ├── game_scene.py    — GameScene(Scene): main game loop scene; params: difficulty, use_minigame; F1/? HUD button opens HelpCatalogOverlay (Exploration tab)
│   └── game_over_scene.py — GameOverScene: victory/defeat screen; "Main Menu [R]" → MainMenuScene
│
├── minigame/
│   ├── hack_node.py         — LootKind (incl. ARMOR, MYSTERY), SecurityKind enums (shared)
│   ├── hack_audio.py        — HackAudio: minigame-specific sound effects
│   ├── hack_scene_grid.py   — HackGridScene(Scene): maze-grid (PCB/circuit-board) hacking minigame (only variant); F1 opens HelpCatalogOverlay on Hacking tab
│   ├── hack_grid_generator.py — generate_grid_map(params) → HackGridMap; HackGridParams.for_difficulty()
│   ├── hack_grid_map.py     — HackGridMap, GridCell, GridCellType; physical 2× grid model
│   ├── hack_common.py       — shared colours (neon palette), draw helpers (corner bracket, glow circle), make_loot_item()
│   ├── aim_scene.py         — AimOverlay (plain class, NOT a Scene): in-world arc overlay owned by GameScene; on_complete(list[float])
│   ├── heal_scene.py        — HealOverlay (plain class, NOT a Scene): centred panel overlay; heartbeat rhythm minigame; 5-tier scoring (Perfect/Great/Good/Poor/Miss); on_complete(int actual_heal)
│   └── melee_scene.py       — MeleeOverlay (plain class, NOT a Scene): in-world power bar overlay; 2-phase (IDLE→CHARGING); compound sine oscillation (no accel); timer countdown in CHARGING; on_complete(float power)
│
main.py                  — entry point
main_hack.py             — standalone hack minigame entry point (dev/test)
```

## Key Action Subclasses (combat/action.py)
`MoveAction(dx,dy)` | `MeleeAttackAction(target)` | `RangedAttackAction(target)` | `WaitAction` | `StairAction` (legacy) | `ElevatorAction` | `ReloadAction` | `EquipAction(weapon)` | `UseItemAction(item)` | `DropItemAction(item)` | `OpenContainerAction(container)`

## Key Events (core/event_bus.py)
`MoveEvent` | `DamageEvent` | `DeathEvent` | `TurnEndEvent` | `StairEvent` (legacy) | `ElevatorEvent(elevator_x, elevator_y)` | `ObjectiveEvent` | `LogMessageEvent`

## Scene Lifecycle (core/scene.py)
`on_enter()` → `handle_events(events)` → `update(dt)` → `render(screen)` → `on_exit()`

## Tileset
- File: `dungeoneer/assets/tileset_for_free.png` — 8 cols × 15 rows of 32×32 tiles, 0-indexed
- Autotile: 8-bit neighbour mask (cardinal + diagonal bits) → wall tile index
- Procedural fallback sprites when tileset unavailable

## TileType enum (world/tile.py)
`WALL` | `FLOOR` | `STAIR_DOWN` (compat) | `DOOR` | `ELEVATOR_CLOSED` (descent, blue on minimap) | `ELEVATOR_OPEN` | `ELEVATOR_ENTRY` (entry/arrival, dim grey-blue on minimap, "no way back")

## Entry elevator (arrival animation)
- `ELEVATOR_ENTRY` placed in start room by dungeon generator; `GenerationResult.entry_pos` is its (x,y)
- Adjacent floor tile blocked from container placement
- On floors 2+: arrival animation plays — closed→open+hero→hero steps out→closed (same timing as descent)
- `_arrival_phase` state machine in `GameScene.update()`; input blocked during animation
- Pressing E near ELEVATOR_ENTRY posts `hint.elevator_no_return` log message, no turn consumed
- Hint shown above player when adjacent to ELEVATOR_ENTRY; dim amber text (vs yellow for descent elevator)
