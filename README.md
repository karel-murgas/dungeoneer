# Dungeoneer

Turn-based cyberpunk dungeon crawler. You play as a "Diver" — a freelancer hired to infiltrate a corporate facility, fight through security, and crack open the objective vault.

## Setup

```bash
pip install -r requirements.txt
python main.py
```

Requires Python 3.11+.

## Controls

| Key | Action |
|-----|--------|
| Arrow keys / WASD | Move (hold for auto-repeat) |
| Walk into enemy | Melee attack |
| Walk into / `E` next to container | Open container |
| `E` adjacent to elevator | Use elevator (descend / extract) |
| `F` | Fire ranged weapon at nearest visible enemy |
| Hold `F` / LMB | Charge melee attack *(melee minigame)* |
| `R` | Reload |
| `H` | Use healing item *(launches rhythm minigame)* |
| `.` / Numpad 5 / `Space` | Wait (skip turn) |
| `C` | Open weapon-swap picker |
| `I` | Open/close inventory |
| `M` | Open/close minimap |
| `E` | Use / equip item *(in inventory)* |
| `1`–`8` | Use item in slot *(in inventory)* |
| `D` | Drop item *(in inventory)* |
| `F1` | Open/close help overlay |
| `F3` | Open statistics panel *(profile runs only)* |
| `F11` | Open/close cheat / debug menu *(dev tool)* |
| `Esc` | Close overlay / quit |

## How to play

- **Explore** the floor and eliminate guards.
- **Loot** containers and enemy drops for weapons, ammo, and healing items.
- **Take the elevator** to go deeper (press `E` when adjacent).
- **On floor 3**: locate the **Corp Vault** and drain it, then use the elevator to extract with your credits.

Enemies only activate when they see you. Guards chase and fight in melee; Drones keep their distance and shoot. A `!` banner appears above your character when enemies first spot you. Press **M** to open a full dungeon minimap showing explored tiles, enemies, containers, and the elevator.

## Heat system

Every action that alerts security raises your **Heat** level (0–500 across 5 tiers: Ghost → Trace → Alert → Pursuit → Burn). Higher heat spawns tougher enemy patrols mid-floor and makes hacking harder. Collect **Coolant** nodes in the hack minigame to reduce heat. The heat bar is displayed centre-top in the HUD.

## Aiming minigame

Every ranged attack launches an aiming overlay directly on the game world:

1. A needle sweeps back and forth on a **90° arc** centred on the target direction.
2. A **green hit zone** appears at a random position on the arc. Its size shrinks with target distance.
3. Press **F** (or left-click) to stop the needle.
   - **Inside the zone** → hit. The closer to the zone centre, the higher the damage.
   - **Outside the zone** → miss, no damage.
4. The needle **speeds up** after each bounce off the arc edges — act fast.
5. Press **Esc** to cancel; all remaining shots miss.
6. Burst weapons (e.g. SMG) repeat the minigame once per shot.

Press **F1** during the aiming overlay to open in-game help explaining the mechanic, armor, and critical hits.

### Critical hits

Stop the needle at **≥ 95% accuracy** (dead centre of the zone) to score a **CRITICAL HIT**, dealing maximum weapon damage.

### Armor

Picking up armor auto-equips it (a stronger piece always replaces a weaker one). Each point of **defense** reduces incoming damage by 1 per hit. The equipped armor slot is shown in the HUD and inventory.

## Melee minigame

When the melee minigame is enabled (Settings → Gameplay), melee attacks use a power-bar overlay:

1. **Hold F** (or LMB) — a bar oscillates sinusoidally between 0 and 100%.
2. **Release** when the bar is high to deal more damage. The top 5% of the bar is the **crit zone** (gold strip) for maximum damage.
3. The bar auto-releases after 2.5 seconds if you hold too long.

Press **F1** during charging to freeze the bar and read the help overlay.

## Healing minigame

Pressing **H** launches the Cardiac Rhythm overlay:

1. Watch **two heartbeat cycles** (du-dum, du-dum).
2. On the **third beat** — press and hold **H** on the first thump.
3. Release **H** after the short gap (on the second thump).

Timing accuracy determines the heal bonus:

| Result | Bonus |
|--------|-------|
| Perfect | +20% |
| Great | +10% |
| Good | ±0% |
| Poor | −10% |
| Miss | −20% |

The minigame can be turned off (flat heal) and the safe-overheal threshold adjusted in **Settings → Gameplay**. If healing would exceed max HP, a confirmation dialog appears before launching.

## Hacking minigame

When **Loot Mode: Hack Minigame** is selected, opening a container launches the grid hacking minigame: navigate the maze-grid (PCB/circuit-board layout), collect loot nodes, reach the exit before time runs out. Higher heat reduces your available time.

The standalone launcher is also available:

```bash
python main_hack.py [easy|normal|hard]
```

## Vault drain minigame

On floor 3, the **Corp Vault** is your primary objective. Interacting with it launches a drain overlay:

- Keep a **1D cursor** inside the scoring zone — the cursor drifts due to physics (velocity + damping).
- Zone checks every 1.5 s yield Perfect / Good / Bad / Fail, adjusting the drain rate multiplier.
- Drift intensifies with heat level and difficulty.
- Press **Q** or **Esc** to voluntarily disconnect; you can re-enter later.
- Draining the vault fully earns a **+25% bonus** on extraction.
- After draining, use the elevator in the same room to extract with your credits.

## Difficulty

Select at launch from the main menu.

| | Easy | Normal | Hard |
|---|---|---|---|
| Guards per floor | 3 | 5 | 7 |
| Drones per floor | 2 | 3 | 4 |
| Player HP | 35 | 30 | 25 |
| Starting ammo | 8× 9mm | — | — |
| Vault drift | 0.7× | 1.0× | 1.3× |

## Enemy types

Enemies spawn in tiers based on floor depth and heat level.

| Enemy | Tier | Notes |
|-------|------|-------|
| Guard | 1 | Melee; patrols then chases |
| Drone | 1 | Ranged; keeps distance |
| Dog (K9) | 1 | 2 moves/turn; fast melee |
| Heavy | 2 | Pistol; high defence; never retreats |
| Turret | 2 | Immobile; 2 shots/turn |
| Sniper Drone | 3 | Rifle; always retreats; long range |
| Riot Guard | 3 | Combat knife; high defence |

## Profiles and saves

The main menu supports multiple named **profiles** with persistent progress and lifetime statistics. Choose **New Game** to create a profile (walks through a setup wizard), **Load Game** to continue an existing one, or **Quick Game** for a one-off run without a profile. Save data is stored in `%APPDATA%/Dungeoneer/` (Windows) or `~/.local/share/Dungeoneer/` (Linux/macOS).

## Settings

The gear icon (⚙) on the main menu or in-game opens the Settings overlay:

- **Gameplay** — Loot mode (hack/random), Aim minigame on/off, Melee minigame on/off, Healing minigame on/off, Quickheal threshold, Tutorial on/off
- **Audio** — Master, Music, and Effects volume
- **Language** — EN / CS / ES

## Language

Language is selected in the main menu (English / Czech / Spanish).

## Cheat / debug menu

Press **F11** during a run to open the developer cheat menu. Allows spawning items, enemies, and containers; adjusting HP, credits, and heat level. For development and testing only.

## Project structure

```
main.py                  # Entry point
main_hack.py             # Standalone hacking minigame (dev/test)
dungeoneer/
├── core/                # Game loop, scenes, event bus, settings, i18n, difficulty, stats
├── entities/            # Player, enemies, items on floor, containers
├── items/               # Weapons, consumables, ammo, armor, inventory
├── combat/              # Turn manager, actions, damage, LOS
├── ai/                  # Pathfinding (A*), enemy behaviour states
├── systems/             # HeatSystem, EncounterSystem, StatsTracker
├── world/               # BSP dungeon generator, map, FOV, rooms
├── meta/                # Profiles, lifetime stats, save/load (storage.py)
├── rendering/           # Renderer, camera, tile renderer, entity renderer
│   └── ui/              # HUD, CombatLog, InventoryUI, WeaponPickerUI, HelpCatalog,
│                        #   MinimapOverlay, TutorialOverlay, StatisticsOverlay,
│                        #   SettingsOverlay, CheatMenu, NewGameWizard, LoadGamePicker
├── scenes/              # MainMenuScene, MetaScene, GameScene, GameOverScene
├── minigame/            # Aiming, hacking grid, healing rhythm, melee, vault overlays
├── audio/               # SFX manager, background music manager
└── data/                # Enemy and item definitions
assets/                  # Sprites, audio, fonts
tests/                   # Test suite (pytest)
```

## Running tests

```bash
pytest tests/
```
