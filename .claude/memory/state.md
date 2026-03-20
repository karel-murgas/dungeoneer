---
name: Project state and roadmap
description: Current development phase, what's complete, what are stubs, and the phase roadmap
type: project
---

## Current State (2026-03-20, stable)

**Phase 1 MVP ✅ + Phase 2 UI Polish ✅ + Phase 3 core content ✅ complete.**
Stable version committed: bugfixes, UI polish, minigame refinements merged.

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
