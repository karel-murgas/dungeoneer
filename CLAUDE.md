# Claude Instructions — Dungeoneer

## How to run

```bash
python main.py                        # full game
python main_hack.py [easy|normal|hard]  # hacking minigame standalone
pytest                                # tests (tests/ directory)
```

## Git workflow

- Active development branch: `dev`
- Production / stable: `main`
- Always commit to `dev`, PRs go `dev → main`

## Localisation rule

- **Every user-visible string** must go through `t("key")` from `dungeoneer.core.i18n`
- **Parameterised strings** (names, numbers) use `t("key").format(name=..., n=...)` — never f-strings with raw text
- **Item / enemy names** are resolved at creation time via `t()` in factory functions (language is fixed for the whole run)
- **Never** use raw string literals in: `LogMessageEvent`, `.render(…)`, button labels, status fields, overlay dicts
- When adding a new string: add it to **all three language dicts** (`"en"`, `"cs"`, `"es"`) in `core/i18n.py` and update `memory/ref_i18n.md`

## Help catalog rule

- **When adding a new in-game help overlay** (new minigame, mechanic, scene): add matching entries to `rendering/ui/help_catalog.py` — a new tab or a new section inside an existing tab.
- The catalog tabs are: EXPLORATION | COMBAT | SHOOTING | AIMING | HACKING.  Add a new tab if the topic doesn't fit, otherwise extend the closest existing tab.
- Each entry: `(section_header_i18n_key, [bullet_i18n_key, ...])` in the `_TABS` list.

## Architecture rules

- **Cross-module communication** → use `EventBus` (`core/event_bus.py`), not direct imports between unrelated modules (e.g. combat should not import from rendering)
- **New global constants** → go into `core/settings.py`, not scattered in modules
- **Rendering stays in `rendering/`** — game logic (combat, AI, world) must not import from `rendering/` or `rendering/ui/`
- **New game scenes** → subclass `Scene` from `core/scene.py`, register in `SceneManager`
- **New actions** → subclass `Action` from `combat/action.py`, handle in `ActionResolver`

## Assets

- Karel downloads assets manually into `sources/` at the project root
- **Never reference files from `sources/` in game code** — always copy to `dungeoneer/assets/` first
- `sources/` is not committed to git

## Memory

Memory files live in `.claude/memory/` (committed to git, syncs across machines).

**At the start of every conversation, read `.claude/memory/MEMORY.md`** and load relevant files from there.

After every meaningful change — and always before a git commit — update the relevant file:

| Changed | Update |
|---|---|
| New module or file added | `.claude/memory/arch.md` — add to module map |
| New Action / Event / Scene type | `.claude/memory/arch.md` — Key Actions / Events section |
| Phase completed or new feature merged | `.claude/memory/state.md` — update current phase |
| Design decision changed or made | `.claude/memory/design.md` |
| New minigame mechanic or API change | `.claude/memory/ref_minigame.md` |
| New i18n keys or language added | `.claude/memory/ref_i18n.md` |
| New tileset indices found | `.claude/memory/ref_tileset.md` |
| New feedback / rule from Karel | create `.claude/memory/feedback_<topic>.md`, add to `.claude/memory/MEMORY.md` |

**Rule:** Memory files must stay accurate and scannable. Goal: orient in codebase by reading memory alone, without re-reading source.

## Project quick facts

- Python + pygame-ce, turn-based cyberpunk roguelite
- Entry: `main.py` → `core/game.py` (`GameApp`)
- Full architecture: see `.claude/memory/arch.md`
- Current phase: see `.claude/memory/state.md`
