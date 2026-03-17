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

## Memory maintenance

After every meaningful change to the codebase — and always before creating a git commit — update the memory files in `~/.claude/projects/.../memory/` to reflect the new state.

| Changed | Update |
|---|---|
| New module or file added | `arch.md` — add to module map |
| New Action / Event / Scene type | `arch.md` — Key Actions / Events section |
| Phase completed or new feature merged | `state.md` — update current phase |
| Design decision changed or made | `design.md` |
| New minigame mechanic or API change | `ref_minigame.md` |
| New i18n keys or language added | `ref_i18n.md` |
| New tileset indices found | `ref_tileset.md` |
| New feedback / rule from Karel | create `feedback_<topic>.md`, add to `MEMORY.md` |

**Rule:** Memory files must stay accurate and scannable. Goal: orient in codebase by reading memory alone, without re-reading source.

## Project quick facts

- Python + pygame-ce, turn-based cyberpunk roguelite
- Entry: `main.py` → `core/game.py` (`GameApp`)
- Full architecture: see `memory/arch.md`
- Current phase: see `memory/state.md`
