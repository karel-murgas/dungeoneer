---
name: i18n quick reference
description: How to add localised strings and switch language in Dungeoneer
type: reference
---

File: `dungeoneer/core/i18n.py` | Languages: `"en"` (default), `"cs"`, `"es"` | Set via `set_language()`

## Add a string
```python
# in i18n.py â€” add to all three dicts (en, cs, es)
_STRINGS = {
    "en": { "my.key": "English text" },
    "cs": { "my.key": "ÄŒeskÃ½ text" },
    "es": { "my.key": "Texto en espaÃ±ol" },
}
```

## Use it
```python
from dungeoneer.core.i18n import t
label = t("my.key")                      # falls back to EN, then raw key â€” never crashes
label = t("my.key").format(n=value)      # parameterised strings
```

## Switch language at runtime
```python
from dungeoneer.core.i18n import set_language
set_language("cs")
```

## Key namespaces (2026-03-20, updated)
| Prefix | Usage |
|--------|-------|
| `menu.*` | Main menu labels, toggles |
| `hud.*` | HUD (HP, ammo, floor, credits) |
| `inv.*` | Inventory UI |
| `weapon_picker.*` | Weapon picker overlay |
| `help.*` | F1 help screen |
| `aim.*` | Aim minigame overlay |
| `aim.help.*` | Aim overlay F1 help (mechanic, armor, crits, controls) |
| `hack.*` | Hack minigame |
| `item.*` | Item names / descriptions |
| `entity.*` | Enemy names |
| `log.*` | Combat log messages |
| `gameover.*` | Game over screen |
| `quit_confirm.*` | In-game quit confirmation dialog (return to main menu) |
| `exit_confirm.*` | Main menu exit confirmation dialog (quit the game) |
| `overheal_confirm.*` | In-game overheal warning dialog (all items exceed threshold) |
| `settings.*` | SettingsOverlay: title, section headers, row labels, footer |
| `minimap.*` | MinimapOverlay: title, legend labels, close hint |
| `help_catalog.*` | HelpCatalogOverlay: title, tab names, section headers, bullet content |

## Key naming convention
`<screen>.<section>.<name>` â€” e.g. `help.title`, `help.key.reload`, `hud.help_hint`

## Key namespaces in use
| Namespace | Description |
|---|---|
| `menu.*` | MainMenuScene (difficulty, loot mode, language, start/quit, hints) |
| `gameover.*` | GameOverScene (title, sub, floors, credits, buttons) |
| `help.*` | HelpScreen overlay (key bindings) |
| `hud.*` | HUD: floor, HP, armor label, heal hint |
| `inv.*` | InventoryUI: title, labels, buttons (inv.btn_use=[E], inv.btn_close=[I]; equip/drop buttons removed) |
| `weapon_picker.*` | WeaponPickerUI: title, empty msg, close btn, hint |
| `item.*` | Item names + descriptions (weapons, consumables, ammo, armor) |
| `entity.*` | Entity names (player, guard, drone, dog, heavy, turret, sniper_drone, riot_guard, crate, corp_vault) |
| `log.*` | Gameplay log messages (combat, pickup, containers, healing, equip, reload, drop, descent, credits_drop, action-denied feedback); `log.room_encounter` / `log.room_clear` (encounter spawning) |
| `hint.*` | In-world contextual hints: `hint.elevator_descend` (adjacent to descent elevator), `hint.elevator_no_return` (adjacent to entry/arrival elevator â€” "no way back"), `hint.container_open` (adjacent to unopened container â€” "[E] Open container"), `hint.elevator_extract` (adjacent to elevator on final floor) |
| `vault.*` | VaultOverlay: title, credits, multiplier, heat label, controls hint, disconnect hint, drained/severed messages |
| `vault.zone.*` | Zone result names: perfect / good / bad / fail |
| `log.vault_*` | Vault log messages: drained, bonus, interrupted, empty, extract, in_combat |
| `tutorial.vault.*` | Vault tutorial step (title + body) |
| `help_catalog.vault.*` | VAULT tab content in help catalog |
| `cheat.section.vault` | Vault section header in cheat menu |
| `cheat.vault.*` | Vault cheat row labels (open, credits, drain50, reset) |
| `hack.status.*` | HackScene footer status bar text |
| `hack.overlay.*` | HackScene security/loot overlay banners (title + sub) |
| `hack.result.*` | HackScene final result overlay |
| `hack.header.*` | HackScene header (title, ESC hints) |
| `hack.footer.*` | HackScene footer hint + data counter |
| `hack.node.*` | HackScene node labels (CORRUPT) |
| `hack.loot.*` | HackScene loot kind display names |
| `hack.help.*` | HackScene F1 help overlay |
| `aim.help.*` | AimOverlay F1 help (mechanic, armor, crits, controls) |
| `heal.help.*` | HealOverlay F1 help + HelpCatalog HEALING tab (mechanic h1, scoring h2: s1â€“s3, controls h3: key1â€“key4) |
| `heal.overlay.*` | HealOverlay runtime labels (title, hint, quality results) |
| `melee.*` | MeleeOverlay: hint_release, result.crit/hit/weak, help.title/1-4/controls_header/key_release/key_cancel/key_help/close |
| `help_catalog.melee.*` | HelpCatalog MELEE tab (h1: Power Strike, h2: Damage & Crits, h3: Controls) |
| `tutorial.melee.*` | Tutorial step for melee weapon equip |
| `settings.gameplay.melee` | Settings row label for melee minigame toggle |
| `overheal_confirm.*` | Overheal warning dialog reusing QuitConfirmDialog (title, question, confirm, cancel) |
| `settings.*` | SettingsOverlay (title, sections, labels, footer); `settings.gameplay.heal`, `settings.gameplay.heal_threshold`, `settings.gameplay.tutorial`, `settings.gameplay.map_size`, `menu.map_size.large/small`, `menu.heal.threshold_pct` |
| `minimap.*` | MinimapOverlay (title, legend labels: player/enemy/container/elevator, hint_close) |
| `help_catalog.*` | HelpCatalogOverlay (title, 9 tabs: Exploration/Combat/Shooting/Aiming/Hacking/Melee/Healing/Heat/Enemies) |
| `help_catalog.enem.*` | HelpCatalog ENEMIES tab (h1/h2/h3 section headers, 7 enemy bullets, tag.* chip labels) |
| `tutorial.*` | TutorialOverlay: `tutorial.<step>.title`, `tutorial.<step>.body` (steps: movement/enemy/container/ammo/medipack/melee/heat), `tutorial.continue`, `menu.tutorial_on/off` |
| `help_catalog.items.icon.*` | HelpCatalog ITEMS tab illustration: `icon.9mm/rifle/shell` â€” ammo type PNG icon labels (en/cs/es) |
| `help_catalog.heat.*` | HelpCatalog HEAT tab (h1: What is Heat, h2: What Raises Heat, h3: Effects); illustration: 5 level colour strips |
| `tutorial.heat.*` | Tutorial step shown after first combat kill or first hack completion |
| `hud.heat_level` | HUD heat bar level name label (param: `level`) |
| `log.heat_level_up` | Combat log when heat escalates (param: `level` = level name string) |
| `hack.status.purge` | HackScene status bar when COOLANT node collected |
| `hack.overlay.purge_title/sub` | HackScene overlay banner for COOLANT node (no params â€” heat amount not shown) |
| `hack.loot.coolant` | COOLANT loot kind display name in HackScene extracting status |
| `cheat.section.heat` | Cheat menu section header |
| `cheat.heat.level1â€“5` | Cheat menu rows to set heat level |

## Rule (from CLAUDE.md)
- Every user-visible string goes through `t("key")`
- Parameterised strings use `.format(name=..., n=...)`
- Item/enemy names resolved at creation time via `t()` in factory functions
- Never raw string literals in: LogMessageEvent, `.render(â€¦)`, button labels

## Add a new language
Add a new dict entry in `_STRINGS` with language code as key.
