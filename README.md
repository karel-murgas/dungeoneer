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
| Arrow keys / WASD | Move |
| Walk into enemy | Melee attack |
| Walk into / `E` next to container | Open container |
| `E` / `>` / Numpad Enter | Descend stairs (or open adjacent container) |
| `F` | Fire ranged weapon at nearest visible enemy |
| `R` | Reload |
| `H` | Quick-use healing item (asks confirmation if it would overheal) |
| `.` / Numpad 5 / `Space` | Wait (skip turn) |
| `C` | Open weapon-swap picker |
| `I` | Open/close inventory |
| `E` | Equip weapon *(in inventory)* |
| `1`–`8` | Use item in slot *(in inventory)* |
| `D` | Drop item *(in inventory)* |
| `F1` | Open/close help overlay |
| `Esc` | Close overlay / quit |

## How to play

- **Explore** the floor and eliminate guards.
- **Loot** containers and enemy drops for weapons, ammo, and healing items.
- **Descend** the stairs to go deeper.
- **Open the Objective Vault** on the final floor to win.

Enemies only activate when they see you. Guards chase and fight in melee; Drones keep their distance and shoot.
A `!` banner appears above your character when enemies first spot you.

## Difficulty

Edit the difficulty in `dungeoneer/core/difficulty.py` or select at launch (if a menu is present). Differences:

| | Easy | Normal | Hard |
|---|---|---|---|
| Guards per floor | 3 | 5 | 7 |
| Drones per floor | 2 | 3 | 4 |
| Player HP | 35 | 30 | 25 |
| Starting ammo | 8× 9mm | — | — |

## Hacking minigame

When **Loot Mode: Hack Minigame** is selected in the main menu, opening a loot container launches the hacking minigame.

Two variants are available (toggle with **[V]** in the main menu):

| Variant | Description |
|---------|-------------|
| **Grid** *(default)* | Maze-grid corridor traversal. Press a direction to auto-move to the next node. |
| Classic | Node-graph navigation with WASD / mouse click. |

The standalone launcher is also available:

```bash
python main_hack.py [easy|normal|hard] [grid|classic]
```

## Language

Language is selected in the main menu (English / Czech / Spanish).

## Project structure

```
main.py                  # Entry point
dungeoneer/
├── core/                # Game loop, scenes, event bus, settings, i18n, difficulty
├── entities/            # Player, enemies, items on floor
├── items/               # Weapons, consumables, ammo, inventory
├── combat/              # Turn manager, actions, damage, LOS
├── ai/                  # Pathfinding (A*), enemy behaviour states
├── world/               # BSP dungeon generator, map, FOV
├── rendering/           # Renderer, camera, tile renderer, entity renderer
│   └── ui/              # HUD, CombatLog, InventoryUI, WeaponPickerUI, HelpScreen, AlertBanner
├── audio/               # Sound/music manager
└── data/                # Enemy and item definitions
assets/                  # Sprites, audio, fonts
tests/                   # Test suite (pytest)
```

## Running tests

```bash
pytest tests/
```
