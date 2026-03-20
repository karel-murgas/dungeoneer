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
| `help_catalog.*` | HelpCatalogOverlay: title, tab names, section headers, bullet content |

## Key naming convention
`<screen>.<section>.<name>` — e.g. `help.title`, `help.key.reload`, `hud.help_hint`

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
| `entity.*` | Entity names (player, guard, drone, crate, corp_vault) |
| `log.*` | Gameplay log messages (combat, pickup, containers, healing, equip, reload, drop, descent, credits_drop, action-denied feedback) |
| `hint.*` | In-world contextual hints (e.g. `hint.stair_descend` — shown above player on STAIR_DOWN tile) |
| `hack.status.*` | HackScene footer status bar text |
| `hack.overlay.*` | HackScene security/loot overlay banners (title + sub) |
| `hack.result.*` | HackScene final result overlay |
| `hack.header.*` | HackScene header (title, ESC hints) |
| `hack.footer.*` | HackScene footer hint + data counter |
| `hack.node.*` | HackScene node labels (CORRUPT) |
| `hack.loot.*` | HackScene loot kind display names |
| `hack.help.*` | HackScene F1 help overlay |
| `aim.help.*` | AimOverlay F1 help (mechanic, armor, crits, controls) |
| `heal.help.*` | HealOverlay F1 help + HelpCatalog HEALING tab (mechanic h1, scoring h2: s1–s3, controls h3: key1–key4) |
| `heal.overlay.*` | HealOverlay runtime labels (title, hint, quality results) |
| `overheal_confirm.*` | Overheal warning dialog reusing QuitConfirmDialog (title, question, confirm, cancel) |
| `settings.*` | SettingsOverlay (title, sections, labels, footer); `settings.gameplay.heal`, `settings.gameplay.heal_threshold`, `menu.heal.threshold_pct` |
| `help_catalog.*` | HelpCatalogOverlay (title, 6 tabs: Exploration/Combat/Shooting/Aiming/Hacking/Healing) |

## Rule (from CLAUDE.md)
- Every user-visible string goes through `t("key")`
- Parameterised strings use `.format(name=..., n=...)`
- Item/enemy names resolved at creation time via `t()` in factory functions
- Never raw string literals in: LogMessageEvent, `.render(…)`, button labels

## Add a new language
Add a new dict entry in `_STRINGS` with language code as key.
