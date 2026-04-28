# Between-runs menu + profiles + stats — implementation plan

## Context

Source spec: [Meziherní menu.md](../../dungeonner_notes/Progress/Meziherní menu.md).

We're reworking the between-runs menu into a profile-based hub. Today the menu has Start/Quit + a settings overlay, all gameplay flags live as `MainMenuScene` instance attributes, and there is **no save/load layer** at all — every fresh launch starts the same. Karel wants:

- **Profiles** (named save files) keyed by player name, persisted to disk
- **Hub menu**: Continue / Load Game / New Game / Quick Game + Settings / Help / Statistics / Quit + the active profile name shown prominently
- **New Game wizard**: language → name (overwrite-confirm on conflict) → difficulty → tutorial — profile created at end
- **Settings rework**: drop map-size / difficulty / tutorial pickers from the overlay (difficulty/tutorial set in wizard, map-size frozen on "large"); difficulty shown read-only
- **Statistics screen**: per-profile aggregate stats (kills by enemy, kills by weapon, deaths by killer, hp healed, bullets shot, hacks/loot, runs won, lifetime credits)
- **Auto-save**: on profile create, on settings change, at run end (both victory and death). Items/HP/heat NOT saved — only meta state.
- **Quick Game**: bypass profile entirely, no saving; mini-overlay seeded with last-used config and editable
- **Player name** flows from profile into the in-game player (replaces hardcoded `t("entity.player.name")`)

End goal: Karel can quit mid-meta-progression, return later, pick their profile, see stats accumulate, and once perks/skills exist (next initiative) they plug into the same `Profile` object.

## Decisions (from clarifying round)

- **Save location**: OS-standard user data dir. Use `os.environ.get("APPDATA", os.path.expanduser("~"))` on Windows → `%APPDATA%/Dungeoneer/`. POSIX fallback: `~/.local/share/Dungeoneer/`. Stdlib only, no new dep.
- **Audio volumes** are **global** (saved in `global.json`, not in profiles). Quick Game uses them too.
- **Quick Game**: a small overlay seeded with the last-used config (from `global.json`); Karel can change difficulty / language / tutorial before launching. Not saved.
- **Profile delete**: each row in Load picker has an `[x]` button with a confirm dialog.
- **Stable IDs for stats**: stats are bucketed by IDs — never localised names — so the same enemy/weapon counts across languages and survives future renames. Items already have `Item.id` (`"pistol"`, `"combat_knife"`, …); **enemies need a new `enemy_id` field added**.
- **Per-weapon kill stats**: track `kills_by_weapon: dict[weapon_id, count]` in `LifetimeStats` — covers all current weapons (`combat_knife`, `energy_sword`, `pistol`, `shotgun`, `smg`, `rifle`, `k9_bite` — though `k9_bite` is enemy-only, it'll just stay 0 for the player).

## Codebase findings

### No existing persistence
- Searched `json.dump`, `pickle`, `save`, `load` across `dungeoneer/` — nothing relevant. `meta/` directory referenced in arch.md is an unimplemented stub (does not exist on disk).
- Audio globals: [core/settings.py:26-28](../../dungeoneer/core/settings.py#L26-L28) — `MASTER_VOLUME`, `MUSIC_VOLUME`, `SFX_VOLUME`.
- Gameplay flags: instance attrs on [scenes/main_menu_scene.py:80-104](../../dungeoneer/scenes/main_menu_scene.py#L80-L104), passed to GameScene at [:316-330](../../dungeoneer/scenes/main_menu_scene.py#L316-L330).

### Stats hook points (verified)
| Stat | Hook | Location |
|---|---|---|
| Enemies killed (by enemy_id) | `DeathEvent` filter `entity is not player`, bucket by `entity.enemy_id` | posted in [combat/action_resolver.py:139](../../dungeoneer/combat/action_resolver.py#L139) (melee), [:247](../../dungeoneer/combat/action_resolver.py#L247) (ranged) |
| Per-weapon kills | extend `DeathEvent` with `weapon_id`, populate from `actor.equipped_weapon.id` | same posting sites as above |
| Player deaths (by killer) | `DeathEvent` where `entity is player`; killer comes from `event.killer` (new field) | [event_bus.py:36](../../dungeoneer/core/event_bus.py#L36) |
| HP healed | Wrap `Actor.heal()` — single chokepoint | [entities/actor.py:40-43](../../dungeoneer/entities/actor.py#L40-L43) |
| Bullets shot | Counter inside `resolve_ranged` shot loop | [combat/action_resolver.py:197](../../dungeoneer/combat/action_resolver.py#L197) |
| Hacked containers (success) | `_on_hack_complete(success=True)` | [scenes/game_scene.py:1298-1315](../../dungeoneer/scenes/game_scene.py#L1298-L1315) |
| Hacked nodes | existing `HackNodesCollectedEvent` | posted [minigame/hack_scene_grid.py:739-743](../../dungeoneer/minigame/hack_scene_grid.py#L739-L743) |
| Looted containers (non-hack) | `resolve_open_container` | [combat/action_resolver.py:253-283](../../dungeoneer/combat/action_resolver.py#L253-L283) |
| Failed containers (hack failed) | `_on_hack_complete(success=False)` | [scenes/game_scene.py:1315-1323](../../dungeoneer/scenes/game_scene.py#L1315-L1323) |
| Won runs | `_trigger_game_over(victory=True)` | [scenes/game_scene.py:449-461](../../dungeoneer/scenes/game_scene.py#L449-L461) |
| Lifetime credits | All `player.credits +=` sites: [action_resolver.py:48,269](../../dungeoneer/combat/action_resolver.py), [game_scene.py:435,439,1309](../../dungeoneer/scenes/game_scene.py); skip the cheat-menu site at game_scene.py:1549 |

### Other findings
- Player name today: hardcoded via `t("entity.player.name")` in [entities/player.py:23](../../dungeoneer/entities/player.py#L23). `Player.name` (inherited) is set once in `__init__`; need a constructor arg to override.
- `TutorialManager._seen` set lives in [rendering/ui/tutorial_overlay.py:78-96](../../dungeoneer/rendering/ui/tutorial_overlay.py#L78-L96), reset per run today; needs profile load/save round-trip.
- `Player.heat` resets to 0 on every `Player.__init__` — natural; do not persist.
- SceneManager supports `push/pop` (sub-scenes stack with on_resume) — wizard can be a pushed sub-scene OR a flag-based overlay. Existing pattern is overlays; we'll keep that for visual consistency.
- i18n is a flat dict-of-dicts in [core/i18n.py](../../dungeoneer/core/i18n.py). New keys go in all three languages (`en`/`cs`/`es`). Naming convention in [.claude/memory/ref_i18n.md](../memory/ref_i18n.md).
- **`Item.id` already exists** ([items/item.py:22](../../dungeoneer/items/item.py#L22)). Every weapon factory sets it ([items/weapon.py](../../dungeoneer/items/weapon.py)). Re-use directly for stats.
- **Enemies do NOT have an `enemy_id` field**. They only have `name = t("entity.guard.name")` (localised) and `sprite_key` (sprite-table key, e.g. `"drone_animated"` is a sprite filename, not a clean semantic ID). New field needed — see Session 0.

---

## Data model (shared across all sessions)

```python
# dungeoneer/meta/profile.py
@dataclass
class LifetimeStats:
    kills_total: int = 0
    kills_by_enemy: dict[str, int] = field(default_factory=dict)    # enemy_id -> count (e.g. "guard": 12)
    kills_by_weapon: dict[str, int] = field(default_factory=dict)   # weapon_id -> count (e.g. "pistol": 8)
    deaths_total: int = 0
    deaths_by_killer: dict[str, int] = field(default_factory=dict)  # enemy_id of killer -> count
    hp_healed: int = 0
    bullets_shot: int = 0
    containers_hacked: int = 0       # hack-minigame success
    nodes_hacked: int = 0            # individual loot nodes
    containers_looted: int = 0       # all opens (success + non-hack path)
    containers_failed: int = 0       # hack failures
    runs_won: int = 0
    credits_lifetime: int = 0        # total credits ever earned (not net)

@dataclass
class GameplayFlags:
    use_minigame: bool = True
    use_aim_minigame: bool = True
    use_heal_minigame: bool = True
    use_melee_minigame: bool = True
    heal_threshold_pct: int = 100

@dataclass
class Profile:
    name: str
    language: str = "en"
    difficulty: str = "normal"        # "easy" | "normal" | "hard"
    tutorial_enabled: bool = False
    tutorial_seen: list[str] = field(default_factory=list)
    credits: int = 0                   # banked between-run credits (unused today; future meta)
    flags: GameplayFlags = ...
    stats: LifetimeStats = ...
    perks: dict = field(default_factory=dict)   # forward-compat stub
    skills: dict = field(default_factory=dict)  # forward-compat stub
    created_at: str = ...
    updated_at: str = ...

# dungeoneer/meta/global_config.py
@dataclass
class GlobalConfig:
    master_volume: float = 1.0
    music_volume: float = 0.30
    sfx_volume: float = 1.0
    last_active_profile: str | None = None
    last_quick_config: dict = field(default_factory=dict)  # mirrors GameplayFlags + difficulty/lang/tutorial
```

Storage layout:
```
%APPDATA%/Dungeoneer/
├── global.json
└── profiles/
    ├── Karel.json
    ├── Diver.json
    └── ...
```

Filename = sanitized profile name (whitelist `[A-Za-z0-9 _-]`, max 24 chars; reject empty/whitespace-only). Display name = original.

---

## Task groups (each = one Sonnet session)

Sessions are ordered by dependency. **Each session's "Required reading" lists exactly the files Sonnet must load** — keep context tight.

### Session 0 — Stable IDs for enemies (prep)

**Goal**: give every enemy a stable `enemy_id` string field so stats / logs / future loot tables can refer to them without depending on locale or display name. Items already have `Item.id` — leave items alone.

**Deliverables**:
- [dungeoneer/entities/enemy.py](../../dungeoneer/entities/enemy.py): add new constructor arg `enemy_id: str` (required, no default — fail loudly if a factory forgets it). Store as `self.enemy_id`. Place it as the first field after `name` so misuse is obvious.
- Update every factory in the same file with its ID — use these exact strings (match `sprite_key` where it's already clean, but **drone uses `enemy_id="drone"`, not `"drone_animated"`** — sprite_key is unrelated):

| Factory | `enemy_id` | Notes |
|---|---|---|
| `make_guard` | `"guard"` | |
| `make_drone` | `"drone"` | NOT `"drone_animated"` |
| `make_dog` | `"dog"` | |
| `make_heavy` | `"heavy"` | |
| `make_turret` | `"turret"` | |
| `make_sniper_drone` | `"sniper_drone"` | |
| `make_riot_guard` | `"riot_guard"` | |

- Search the whole `dungeoneer/` tree for any place that compares enemy by `name` or `sprite_key` for semantic logic (not rendering) and switch to `enemy_id`. Likely candidates:
  - [systems/encounter.py](../../dungeoneer/systems/encounter.py) — pack/elite selection by tier (probably uses tier already, but check).
  - [rendering/ui/cheat_menu.py](../../dungeoneer/rendering/ui/cheat_menu.py) — spawn-by-type uses factory functions directly, no change needed.
  - Anywhere else `entity.name ==` or `entity.sprite_key ==` is used as game logic.
  - Rendering by `sprite_key` stays as-is (sprite_key is a render concern, not identity).
- **No i18n change needed** — display names still come from `t(f"entity.{enemy_id}.name")`, and the existing keys (`entity.guard.name`, `entity.drone.name`, …) already match these IDs. Just verify the mapping holds.
- Tests: `tests/test_enemy_ids.py` — instantiate every factory, assert each has `enemy_id` set and matches the table above; assert all IDs are unique.
- Update [.claude/memory/arch.md](../memory/arch.md) — add a one-line note in the Enemy section listing the canonical enemy_ids.

**Required reading**:
- this plan file (this section only)
- [dungeoneer/entities/enemy.py](../../dungeoneer/entities/enemy.py) — full file
- [dungeoneer/core/i18n.py](../../dungeoneer/core/i18n.py) — verify the `entity.<id>.name` keys
- [dungeoneer/systems/encounter.py](../../dungeoneer/systems/encounter.py) — only enemy-spawn dispatch
- [dungeoneer/rendering/ui/cheat_menu.py](../../dungeoneer/rendering/ui/cheat_menu.py) — only the spawn section

**Verification**: `pytest tests/test_enemy_ids.py`; `python main.py` — fight at least one of each enemy type; rendering and AI behaviour unchanged.

---

### Session 1 — Persistence layer (`meta/` package)

**Goal**: stand up the dataclasses + JSON read/write so later sessions can call them. **Touches zero existing source modules.**

**Deliverables**:
- `dungeoneer/meta/__init__.py`
- `dungeoneer/meta/profile.py` — `Profile`, `LifetimeStats`, `GameplayFlags` dataclasses + `to_dict` / `from_dict` (handle missing keys gracefully = backward-compat for future profile fields)
- `dungeoneer/meta/global_config.py` — `GlobalConfig` dataclass + `to_dict` / `from_dict`
- `dungeoneer/meta/storage.py` — public API:
  - `get_save_dir() -> Path` (creates dir if missing)
  - `list_profiles() -> list[str]` (display names, sorted by `updated_at` desc)
  - `profile_exists(name: str) -> bool`
  - `load_profile(name: str) -> Profile | None`
  - `save_profile(profile: Profile) -> None` (atomic write via tmpfile + rename; updates `updated_at`)
  - `delete_profile(name: str) -> bool`
  - `load_global() -> GlobalConfig` (returns defaults if file missing)
  - `save_global(cfg: GlobalConfig) -> None`
  - `sanitize_name(raw: str) -> str` (strip → whitelist `[A-Za-z0-9 _-]` → trim to 24 chars; raises `ValueError` if empty after sanitization)
- `tests/test_profiles.py` — round-trip create/load/save/delete/list/sanitize-name + missing-key tolerance + invalid-name rejection. Use `tmp_path` fixture and monkeypatch `meta.storage._SAVE_DIR_OVERRIDE` (add a module-level override hook for tests).
- Add 1-2 i18n keys for filesystem error toasts: `profile.error.read_failed`, `profile.error.write_failed` (en/cs/es).
- Update [.claude/memory/arch.md](../memory/arch.md) with `meta/` entry + [.claude/memory/MEMORY.md](../memory/MEMORY.md) index.

**Required reading**:
- this plan file
- [.claude/memory/arch.md](../memory/arch.md) for module-map convention
- [.claude/memory/ref_i18n.md](../memory/ref_i18n.md) for key naming
- [dungeoneer/core/i18n.py](../../dungeoneer/core/i18n.py) — to add the 2 keys

**Verification**: `pytest tests/test_profiles.py` passes; manually `python -c "from dungeoneer.meta.storage import save_profile, load_profile, Profile; ..."` round-trips a profile.

---

### Session 2 — Stats tracking system

**Goal**: live counters during a run, merged into `LifetimeStats` and saved on run end (victory or death). All bucketing uses **stable IDs** (Session 0 enemy_id, existing Item.id), never localised names.

**Deliverables**:
- `dungeoneer/core/stats.py` — `RunStats` dataclass (mirrors `LifetimeStats` minus `runs_won`); `merge_run_into_lifetime(run, lifetime, victory)` helper.
- New events in [dungeoneer/core/event_bus.py](../../dungeoneer/core/event_bus.py):
  - `HealEvent(actor, amount)` — emitted by `Actor.heal()` after applying.
  - `BulletFiredEvent(shooter, weapon_id)` — emitted in `resolve_ranged` per shot. Stats only count player shots (`shooter is player`); the `weapon_id` is for completeness / future enemy-weapon stats.
  - `ContainerLootedEvent(container, success: bool, was_hacked: bool)` — emitted from `_on_hack_complete` and `resolve_open_container`.
  - **Extend `DeathEvent`** ([core/event_bus.py:36](../../dungeoneer/core/event_bus.py#L36)) with two optional fields: `killer: Actor | None = None` and `weapon_id: str | None = None`. Update both posting sites in [combat/action_resolver.py:139,247](../../dungeoneer/combat/action_resolver.py) to populate them from `actor` (the attacker) and `actor.equipped_weapon.id`. Existing subscribers that only read `entity` keep working.
- `dungeoneer/systems/stats_tracker.py` — `StatsTracker` subscribes to `DeathEvent` / `HealEvent` / `BulletFiredEvent` / `ContainerLootedEvent` / `HackNodesCollectedEvent`; owns a `RunStats`. Owns `credit_baseline` set at run start; on finalize, `credits_earned = max(0, player.credits - baseline)` (vault credits already flow through `player.credits`, so no double-counting needed — verify this against [scenes/game_scene.py:435,439](../../dungeoneer/scenes/game_scene.py)).

  Bucketing rules:
  - On `DeathEvent` where `entity is not player` and `event.killer is player`: `kills_total += 1`; `kills_by_enemy[entity.enemy_id] += 1`; `kills_by_weapon[event.weapon_id] += 1` (skip weapon bucket if `weapon_id is None`).
  - On `DeathEvent` where `entity is player`: `deaths_total += 1`; if `event.killer` is an `Enemy`, `deaths_by_killer[event.killer.enemy_id] += 1`.
  - All other DeathEvents (e.g. enemy killed by another enemy in some hypothetical future) are ignored for stats.
- Hooks (single line each, mostly emits):
  - [entities/actor.py:40-43](../../dungeoneer/entities/actor.py#L40-L43): emit `HealEvent(self, actual_amount)` where `actual_amount = self.hp_after - self.hp_before` (so overheal that's clamped doesn't inflate the counter).
  - [combat/action_resolver.py:197](../../dungeoneer/combat/action_resolver.py#L197): emit `BulletFiredEvent(shooter, weapon.id)` per shot.
  - [combat/action_resolver.py:139,247](../../dungeoneer/combat/action_resolver.py#L139): pass `killer=actor, weapon_id=weapon.id if weapon else None` when posting `DeathEvent`.
  - [combat/action_resolver.py:269](../../dungeoneer/combat/action_resolver.py#L269) and equivalent objective-vault path: emit `ContainerLootedEvent(container, success=True, was_hacked=False)` after credit award.
  - [scenes/game_scene.py:1298-1323](../../dungeoneer/scenes/game_scene.py#L1298-L1323): in `_on_hack_complete`, emit `ContainerLootedEvent(container, success=success, was_hacked=True)`.
- [scenes/game_scene.py](../../dungeoneer/scenes/game_scene.py): own a `StatsTracker` instance; create at `on_enter`, dispose at `on_exit`. In `_trigger_game_over(victory)`, finalize: load active profile (skip if Quick Game / no active profile), merge run stats, save.
- Tests in `tests/test_stats_tracker.py` — fire events synthetically, assert counters; test `merge_run_into_lifetime` arithmetic; test that `kills_by_weapon` and `kills_by_enemy` increment in lockstep on player kill events; test that enemy-on-player kills bucket the killer correctly.

**Required reading**:
- this plan file (Sessions 0–2 sections)
- [dungeoneer/meta/profile.py](../../dungeoneer/meta/profile.py) (from Session 1)
- [dungeoneer/meta/storage.py](../../dungeoneer/meta/storage.py) (from Session 1)
- [dungeoneer/core/event_bus.py](../../dungeoneer/core/event_bus.py) — to learn pattern + extend
- [dungeoneer/entities/actor.py](../../dungeoneer/entities/actor.py)
- [dungeoneer/entities/enemy.py](../../dungeoneer/entities/enemy.py) — to use `enemy_id` (added in Session 0)
- [dungeoneer/items/item.py](../../dungeoneer/items/item.py) + [dungeoneer/items/weapon.py](../../dungeoneer/items/weapon.py) — for `Item.id`
- [dungeoneer/combat/action_resolver.py](../../dungeoneer/combat/action_resolver.py) — `resolve_ranged`, `resolve_melee`, `resolve_open_container` only
- [dungeoneer/scenes/game_scene.py](../../dungeoneer/scenes/game_scene.py) — only `__init__`, `on_enter`, `on_exit`, `_on_hack_complete`, `_trigger_game_over`
- [dungeoneer/systems/heat.py](../../dungeoneer/systems/heat.py) as reference for the subscriber pattern

**Verification**: `pytest tests/test_stats_tracker.py`; manual: play a run, check that `<save_dir>/profiles/<name>.json` shows incremented `kills_total`, `bullets_shot`, etc.

**Out of scope here**: UI for stats display (Session 4); profile creation flow (Session 3) — Session 2 just assumes `load_global().last_active_profile` may give a name; if `None`, it's Quick Game and saves are skipped.

---

### Session 3 — Menu UI rework + wizard + load picker + settings strip + player name flow

**Goal**: replace MainMenuScene's Start button with the full hub. End of session: Karel can create a profile via the wizard, see Continue/Load work, settings save automatically.

**Deliverables**:
- **`dungeoneer/scenes/main_menu_scene.py`** rewrite:
  - Hub layout: title + active profile name (large, top-centre) + buttons grid: Continue / New Game / Load Game / Quick Game / Statistics / Quit + ⚙ Help icons (top-right).
  - "Continue" disabled if `last_active_profile` is `None` or the profile file no longer exists.
  - Holds `_active_profile: Profile | None` loaded from `last_active_profile` on `on_enter`. All gameplay flags now read from `self._active_profile.flags` (or `None` defaults during Quick Game).
  - On click of Continue / Load → set `last_active_profile` and start `GameScene` with profile-derived params.
- **New overlay `dungeoneer/rendering/ui/new_game_wizard.py`**: 4-step state machine.
  - Step 1: language (3 buttons, switches `set_language` live for instant translation feedback).
  - Step 2: name input (typing field; live-shows sanitized version; validates non-empty; if `profile_exists(name)` shows yellow warning + "Overwrite?" Yes/No mini-dialog).
  - Step 3: difficulty (Easy/Normal/Hard).
  - Step 4: tutorial On/Off.
  - On Confirm: build `Profile`, `save_profile`, set as `last_active_profile`, save global, signal MainMenuScene to start the run.
- **New overlay `dungeoneer/rendering/ui/load_game_picker.py`**:
  - Scrollable list of profiles (name + last-played date + total runs won badge).
  - Click row → load + start run.
  - `[x]` icon per row → confirm dialog (reuse `QuitConfirmDialog`-style with i18n key `profile.delete.confirm`) → `delete_profile`.
  - Empty state: "No saved games" with a "New Game" CTA.
- **New overlay `dungeoneer/rendering/ui/quick_game_overlay.py`**:
  - Compact panel showing language / difficulty / tutorial / minigame toggles (4-5 rows). Pre-filled from `GlobalConfig.last_quick_config`.
  - "Start" button → write back to `last_quick_config`, save global, start `GameScene` with no active profile.
- **`dungeoneer/rendering/ui/settings_overlay.py`** strip-down:
  - Remove DIFFICULTY toggle (replace with read-only line `Difficulty: <Normal>` from active profile, or hide entirely in Quick Game).
  - Remove Tutorial toggle.
  - Remove Map size toggle (map_size hardcoded to "large" — drop the param or default it permanently).
  - Keep: gameplay minigame toggles, heal threshold, language, audio.
  - On any change: if `_active_profile` is not None, write back into `profile.flags` (or `profile.language` for language) and `save_profile`. For Quick Game / no profile, mutate `GlobalConfig.last_quick_config` and `save_global`.
  - Audio change always writes `GlobalConfig` (audio is global).
- **Player name flow**:
  - [entities/player.py:18](../../dungeoneer/entities/player.py#L18): add `name: str | None = None` param to `Player.__init__`; if `None`, falls back to `t("entity.player.name")`. Pass through `super().__init__(..., name=...)`.
  - [scenes/game_scene.py](../../dungeoneer/scenes/game_scene.py): accept `player_name: str | None = None` constructor arg, pass to `Player(...)`.
  - MainMenuScene passes `profile.name` (or `None` for Quick Game).
- i18n: all new strings (`menu.continue`, `menu.load`, `menu.new_game`, `menu.quick`, `menu.statistics`, `menu.profile.no_active`, `menu.no_saves`, `wizard.step.language/name/difficulty/tutorial`, `wizard.name.prompt`, `wizard.name.invalid`, `wizard.name.exists.confirm`, `wizard.next`, `wizard.back`, `wizard.confirm`, `loadpicker.title`, `loadpicker.last_played`, `loadpicker.runs_won`, `profile.delete.confirm`, `quick.title`, `quick.start`, …) in en/cs/es. Update [.claude/memory/ref_i18n.md](../memory/ref_i18n.md).

**Required reading**:
- this plan file (full)
- [dungeoneer/scenes/main_menu_scene.py](../../dungeoneer/scenes/main_menu_scene.py) — full rewrite
- [dungeoneer/rendering/ui/settings_overlay.py](../../dungeoneer/rendering/ui/settings_overlay.py) — strip + wire
- [dungeoneer/rendering/ui/quit_confirm.py](../../dungeoneer/rendering/ui/quit_confirm.py) — pattern reference
- [dungeoneer/rendering/ui/help_catalog.py](../../dungeoneer/rendering/ui/help_catalog.py) — overlay pattern with tabs
- [dungeoneer/scenes/game_scene.py](../../dungeoneer/scenes/game_scene.py) — only `__init__` signature
- [dungeoneer/scenes/game_over_scene.py](../../dungeoneer/scenes/game_over_scene.py) — for return path
- [dungeoneer/entities/player.py](../../dungeoneer/entities/player.py) — full file (small)
- [dungeoneer/meta/profile.py](../../dungeoneer/meta/profile.py), [dungeoneer/meta/storage.py](../../dungeoneer/meta/storage.py), [dungeoneer/meta/global_config.py](../../dungeoneer/meta/global_config.py) (from Session 1)
- [dungeoneer/core/i18n.py](../../dungeoneer/core/i18n.py) — to add many keys
- [.claude/memory/ref_i18n.md](../memory/ref_i18n.md)

**Verification** (manual playtest checklist — Sonnet should run through it before claiming done):
1. Fresh launch (delete `<save_dir>` first): hub shows "No active profile"; Continue is disabled.
2. New Game wizard: type `Karel`, English, Hard, tutorial ON → starts run → profile exists on disk with those settings.
3. Quit to menu → Continue button is enabled, shows `Karel` as active.
4. Settings overlay: change SFX volume → `global.json.sfx_volume` updated. Toggle aim minigame off → `Karel.json.flags.use_aim_minigame=false`.
5. New Game with name `Karel` → overwrite-confirm appears.
6. Load Game picker: shows all profiles with last-played dates.
7. Delete profile from picker → confirm → file gone.
8. Quick Game overlay: change language → start run → `Karel.json` unchanged; `global.json.last_quick_config.language` updated.
9. Player name in HUD reads `Karel`, not `Diver`.

**Out of scope here**: stats screen rendering (Session 4); tutorial-seen persistence (Session 4).

---

### Session 4 — Statistics screen + tutorial-seen persistence

**Goal**: render stats from active profile + persist `TutorialManager._seen` across runs within the same profile.

**Deliverables**:
- **`dungeoneer/rendering/ui/statistics_overlay.py`**:
  - Centred panel, sections (use tabbed layout if it overflows the panel — see help_catalog.py for pattern):
    - **Combat**: kills_total, kills_by_enemy (sorted desc, show top 7 + "others" lumped together), deaths_total, deaths_by_killer.
    - **Weapons**: kills_by_weapon (sorted desc, show all entries — ~6-7 weapons; rendered as `<weapon name>: <count>`).
    - **Healing & ranged**: hp_healed, bullets_shot.
    - **Hacking & loot**: containers_hacked / containers_looted / containers_failed / nodes_hacked.
    - **Career**: runs_won, credits_lifetime.
  - Empty-state for fresh profile ("No stats yet").
  - Bucket keys are stable IDs (Session 0 enemy_id + existing Item.id), so display rendering is straightforward:
    - Enemy name: `t(f"entity.{enemy_id}.name")`
    - Weapon name: `t(f"item.{weapon_id}.name")`
    - This means switching language live (in Settings) renders the screen in the new language without any data migration.
- **Wire into MainMenuScene**: "Statistics" button opens overlay; reads `_active_profile.stats`. Disabled / hidden if no active profile.
- **Tutorial-seen persistence**:
  - [rendering/ui/tutorial_overlay.py:78-96](../../dungeoneer/rendering/ui/tutorial_overlay.py#L78-L96): `TutorialManager.__init__` accepts optional `initial_seen: list[str]`; populates `_seen` from it.
  - [scenes/game_scene.py](../../dungeoneer/scenes/game_scene.py): on `on_enter`, pass `profile.tutorial_seen` (if profile present); whenever `should_show` returns True, after the step is shown, call `profile.tutorial_seen.append(step)` + `save_profile`. Skip for Quick Game.
- i18n: stats labels (`stats.title`, `stats.section.combat`, `stats.section.weapons`, `stats.kills_total`, `stats.deaths_total`, `stats.hp_healed`, `stats.bullets_shot`, `stats.containers_hacked`, `stats.containers_looted`, `stats.containers_failed`, `stats.nodes_hacked`, `stats.runs_won`, `stats.credits_lifetime`, `stats.empty`, `stats.others`) in en/cs/es.

**Required reading**:
- this plan file
- [dungeoneer/scenes/main_menu_scene.py](../../dungeoneer/scenes/main_menu_scene.py) (post-Session-3)
- [dungeoneer/rendering/ui/help_catalog.py](../../dungeoneer/rendering/ui/help_catalog.py) — for tabbed-overlay layout reference
- [dungeoneer/rendering/ui/settings_overlay.py](../../dungeoneer/rendering/ui/settings_overlay.py) — for fonts/colours pattern
- [dungeoneer/rendering/ui/tutorial_overlay.py](../../dungeoneer/rendering/ui/tutorial_overlay.py) — full file
- [dungeoneer/scenes/game_scene.py](../../dungeoneer/scenes/game_scene.py) — only tutorial-trigger sites + `on_enter`
- [dungeoneer/meta/profile.py](../../dungeoneer/meta/profile.py), [meta/storage.py](../../dungeoneer/meta/storage.py)
- [dungeoneer/core/i18n.py](../../dungeoneer/core/i18n.py)

**Verification**:
1. Play part of a run, die early at tutorial step "movement" before reaching "enemy". Reload same profile → "movement" tutorial does NOT show again, "enemy" tutorial still pending.
2. Statistics overlay shows non-zero counters after a run. Delete a profile → its stats gone.
3. Kill enemies with multiple different weapons → stats screen "Weapons" section shows correct per-weapon kill counts.
4. Switch language in Settings → reopen Statistics → enemy and weapon names render in new language; counts unchanged.

---

## Why this grouping (context economy)

| Session | Scope | Files touched | Why grouped |
|---|---|---|---|
| **0 — Enemy IDs** | tiny prep refactor | `entities/enemy.py`, possibly `systems/encounter.py`, new test | 1 concept (stable IDs); independent of everything else; unblocks Session 2 |
| **1 — Persistence** | new module only | new `meta/`, tests, i18n (2 keys) | zero coupling to existing code; reads no game logic |
| **2 — Stats tracking** | event hooks + new tracker system | `event_bus`, `actor`, `action_resolver`, `game_scene` (tiny), new `core/stats.py` + `systems/stats_tracker.py` | all about wiring counters via events; one mental model. Depends on Sessions 0 + 1. |
| **3 — Menu UI rework** | menu/overlays + player-name flow | `main_menu_scene` rewrite, new wizard/picker/quick overlays, `settings_overlay` strip, `player.py` + `game_scene.py` constructor | all UI/state-flow work; shares fonts, palette, overlay pattern, i18n batch. Depends on Session 1. |
| **4 — Stats screen + tutorial seen** | read-only display + small persistence | new `statistics_overlay`, `tutorial_overlay` tweak, `game_scene` wire | both read `Profile`, both render polish; small enough to share a session. Depends on Sessions 1 + 2 + 3. |

Total: 5 sessions. Recommended order: 0 → 1 → 2 → 3 → 4 (Sessions 1 and 2 can swap; 2 and 3 can swap if Session 0 is done first). Sonnet should be told **at the start of each session** which files to load (the "Required reading" list); skip global codebase exploration.

## Out of scope (future sessions)

- Perks / skills hookup into `Profile.perks` / `Profile.skills` (after metagame design is final).
- Cloud sync / save backups.
- "Run history" log per profile (different from aggregate stats).
- Settings overlay in-game (during a run, the profile's flags are read-only — no live re-read needed since the run is already configured).