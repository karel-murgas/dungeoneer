---
name: i18n quick reference
description: How to add localised strings and switch language in Dungeoneer
type: reference
---

File: `dungeoneer/core/i18n.py` | Languages: `"en"` (default), `"cs"`, `"es"` | Set via `set_language()`

## Add a string
```python
# in i18n.py — add to all three dicts (en, cs, es)
_STRINGS = {
    "en": { "my.key": "English text" },
    "cs": { "my.key": "Český text" },
    "es": { "my.key": "Texto en español" },
}
```

## Use it
```python
from dungeoneer.core.i18n import t
label = t("my.key")                      # falls back to EN, then raw key — never crashes
label = t("my.key").format(n=value)      # parameterised strings
```

## Switch language at runtime
```python
from dungeoneer.core.i18n import set_language
set_language("cs")
```

## Key namespaces (2026-03-17)
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
| `quit_confirm.*` | Quit confirmation dialog |

## Key naming convention
`<screen>.<section>.<name>` — e.g. `help.title`, `help.key.reload`, `hud.help_hint`

## Key namespaces in use
| Namespace | Description |
|---|---|
| `menu.*` | MainMenuScene (difficulty, loot mode, language, start/quit, hints) |
| `gameover.*` | GameOverScene (title, sub, floors, credits, buttons) |
| `help.*` | HelpScreen overlay (key bindings) |
| `hud.*` | HUD: floor, HP, armor label, heal hint |
| `inv.*` | InventoryUI: title, labels, buttons |
| `weapon_picker.*` | WeaponPickerUI: title, empty msg, close btn, hint |
| `item.*` | Item names + descriptions (weapons, consumables, ammo, armor) |
| `entity.*` | Entity names (player, guard, drone) |
| `log.*` | Gameplay log messages (combat, pickup, containers, healing) |
| `hack.status.*` | HackScene footer status bar text |
| `hack.overlay.*` | HackScene security/loot overlay banners (title + sub) |
| `hack.result.*` | HackScene final result overlay |
| `hack.header.*` | HackScene header (title, ESC hints) |
| `hack.footer.*` | HackScene footer hint + data counter |
| `hack.node.*` | HackScene node labels (CORRUPT) |
| `hack.loot.*` | HackScene loot kind display names |
| `hack.help.*` | HackScene F1 help overlay |
| `aim.help.*` | AimOverlay F1 help (mechanic, armor, crits, controls) |

## Rule (from CLAUDE.md)
- Every user-visible string goes through `t("key")`
- Parameterised strings use `.format(name=..., n=...)`
- Item/enemy names resolved at creation time via `t()` in factory functions
- Never raw string literals in: LogMessageEvent, `.render(…)`, button labels

## Add a new language
Add a new dict entry in `_STRINGS` with language code as key.
