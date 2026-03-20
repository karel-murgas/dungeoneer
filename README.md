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
| `E` / `>` / Numpad Enter | Descend stairs (or open adjacent container) |
| `F` | Fire ranged weapon at nearest visible enemy |
| `R` | Reload |
| `H` | Use healing item (launches rhythm minigame; asks confirmation if it would overheal) |
| `.` / Numpad 5 / `Space` | Wait (skip turn) |
| `C` | Open weapon-swap picker |
| `I` | Open/close inventory |
| `E` | Use / equip item *(in inventory)* |
| `1`–`8` | Use item in slot *(in inventory)* |
| `D` | Drop item *(in inventory)* |
| `F1` | Open/close help overlay |
| `F11` | Open/close cheat / debug menu *(dev tool)* |
| `Esc` | Close overlay / quit |

## How to play

- **Explore** the floor and eliminate guards.
- **Loot** containers and enemy drops for weapons, ammo, and healing items.
- **Descend** the stairs to go deeper.
- **Open the Objective Vault** on the final floor to win.

Enemies only activate when they see you. Guards chase and fight in melee; Drones keep their distance and shoot.
A `!` banner appears above your character when enemies first spot you.

## Aiming minigame

Every ranged attack launches an aiming overlay directly on the game world:

1. A needle sweeps back and forth on a **90° arc** centred on the target direction.
2. A **green hit zone** appears at a random position on the arc. Its size shrinks with target distance.
3. Press **F** (or left-click) to stop the needle.
   - **Inside the zone** → hit. The closer to the zone centre, the higher the damage (up to max weapon damage).
   - **Outside the zone** → miss, no damage.
4. The needle **speeds up** after each bounce off the arc edges — act fast.
5. Press **Esc** to cancel; all remaining shots miss.
6. Burst weapons (e.g. SMG) repeat the minigame once per shot.

Press **F1** during the aiming overlay to open in-game help that explains the mechanic, armor, and critical hits.

### Critical hits

Stop the needle at **≥ 95% accuracy** (dead centre of the zone) to score a **CRITICAL HIT**, which deals maximum weapon damage.

### Armor

Picking up armor auto-equips it (a stronger piece always replaces a weaker one). Each point of **defense** reduces incoming damage by 1 per hit (melee and ranged). The equipped armor slot is shown in the HUD and inventory.

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

Press **F1** during the overlay for the full mechanic explanation. The minigame can be turned off (flat heal) and the "safe overheal" threshold adjusted in **Settings → Gameplay**.

If healing would exceed max HP, a confirmation dialog appears before launching.

## Hacking minigame

When **Loot Mode: Hack Minigame** is selected in the main menu, opening a loot container launches the grid hacking minigame: navigate the maze-grid (PCB/circuit-board layout), collect loot nodes, reach the exit before time runs out.

The standalone launcher is also available:

```bash
python main_hack.py [easy|normal|hard]
```


## Difficulty

Select at launch from the main menu, or edit `dungeoneer/core/difficulty.py`.

| | Easy | Normal | Hard |
|---|---|---|---|
| Guards per floor | 3 | 5 | 7 |
| Drones per floor | 2 | 3 | 4 |
| Player HP | 35 | 30 | 25 |
| Starting ammo | 8× 9mm | — | — |

## Language

Language is selected in the main menu (English / Czech / Spanish).

## Settings

The gear icon (⚙) on the main menu or in-game opens the Settings overlay:

- **Gameplay** — Loot mode (hack/random), Aim minigame on/off, Healing minigame on/off, Quickheal threshold
- **Audio** — Master, Music, and Effects volume
- **Language** — EN / CS / ES

## Cheat / debug menu

Press **F11** during a run to open the developer cheat menu. Allows spawning items, enemies, and containers; adjusting HP and credits. For development and testing only.

## Project structure

```
main.py                  # Entry point
main_hack.py             # Standalone hacking minigame (dev/test)
dungeoneer/
├── core/                # Game loop, scenes, event bus, settings, i18n, difficulty
├── entities/            # Player, enemies, items on floor
├── items/               # Weapons, consumables, ammo, armor, inventory
├── combat/              # Turn manager, actions, damage, LOS
├── ai/                  # Pathfinding (A*), enemy behaviour states
├── world/               # BSP dungeon generator, map, FOV
├── rendering/           # Renderer, camera, tile renderer, entity renderer
│   └── ui/              # HUD, CombatLog, InventoryUI, WeaponPickerUI, HelpScreen,
│                        #   AlertBanner, SettingsOverlay, HelpCatalog, CheatMenu
├── minigame/            # Aiming overlay, hacking grid, healing rhythm minigame
├── audio/               # SFX manager, background music manager
└── data/                # Enemy and item definitions
assets/                  # Sprites, audio, fonts
tests/                   # Test suite (pytest)
```

## Running tests

```bash
pytest tests/
```
