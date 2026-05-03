# Perks — Phase 1 implementation plan (framework)

## Context for every step

> Spec for all design decisions: `dungeonner_notes/Fatures/perks.md` and `.claude/plans/perks_design.md`. Read **perks.md first** — it has the rebalanced numbers, body-part groupings, prices, deferred list. Don't re-derive these.

**Project conventions (always apply, don't re-derive):**
- All user-visible strings via `t("key")` from `core/i18n.py`. Add to all 3 dicts: `"en"`, `"cs"`, `"es"`. Update `.claude/memory/ref_i18n.md`.
- New global constants → `core/settings.py`.
- Cross-module communication → `EventBus` (`core/event_bus.py`).
- New scenes → subclass `Scene`. New actions → subclass `Action`.
- Rendering modules can't be imported from game-logic modules.
- Tests in `tests/` directory; `pytest`. Run before declaring done.
- Read `.claude/memory/MEMORY.md` then `arch.md` + `state.md` at the start of each session.
- Active dev branch: `dev`. Commit there.

**Phase 1 scope:** energy/heat plumbing + hub shop UI + in-run perk menu/hotbar + recharge nodes + help catalog. **No actual perk effects** — buying a perk records ownership; firing an active perk just deducts EP and logs "fired X" stub. Perk effects come in Phase 2.

The 5 steps below are designed to be runnable in fresh sessions with no shared chat history. Each step lists exactly what to read.

---

## Step 1 — Data foundation (catalog + Player.energy + Profile.perks shape)

**Goal:** single source of truth for all perk definitions; energy field on Player; structured `Profile.perks` persistence; i18n keys for every perk.

**Read first:**
- `dungeonner_notes/Fatures/perks.md` (full)
- `.claude/memory/MEMORY.md`, `.claude/memory/arch.md` (module map only)
- `dungeoneer/entities/player.py` (whole file)
- `dungeoneer/core/settings.py` (whole file)
- `dungeoneer/meta/profile.py` (whole file)
- `dungeoneer/core/i18n.py` — read first 100 lines to learn structure, then jump to a representative section like `entity.*` keys
- `.claude/memory/ref_i18n.md`

**Tasks:**

1. **Create `dungeoneer/perks/` package** with:
   - `__init__.py` — re-export `PerkDef`, `PerkType`, `BodyPart`, `CATALOG`, `get_perk(id)`, `is_owned(profile, id, level=1)`, `get_level(profile, id)`, `set_level(profile, id, level)`, `total_cost_to(profile, id, target_level)`.
   - `catalog.py` — `PerkType = Enum(ACTIVE, PASSIVE)`, `BodyPart = Enum(BRAIN, EYES, HANDS, BODY, LEGS)`. `@dataclass PerkDef(id, name_key, desc_key, type, body, ep_cost: int|None, ep_per_turn: int|None, prices: tuple[int, ...], max_level: int, deferred: bool, target_required: bool)`. Build `CATALOG: dict[str, PerkDef]` with all entries from perks.md §Perky table. Use canonical ids: `smartlink`, `muscle_implants`, `skeleton`, `lenses`, `protocol_smg`, `protocol_shotgun`, `protocol_rifle`, `protocol_sword`, `network_scan`, `mech_arm`, `scanner`, `reflex_fibres`, `cloak`, `recoil_comp`, `nanobots`, `neural_protection`, `trap`, `surge_contacts`.
   - `state.py` — pure helpers operating on `profile.perks` dict; canonical shape: `{perk_id: {"level": int}}`. Functions above live here.
   - `tests/test_perks_catalog.py` — sanity checks: every entry has matching i18n key existing, prices length == max_level, EP cost present iff active, deferred flag matches list in perks.md.

2. **`core/settings.py`** — add:
   ```
   ENERGY_START = 100
   ENERGY_MAX = 100
   RECHARGE_NODE_EP = 50
   RECHARGE_HEAT_PER_EP = 0.2  # 1 heat per 5 EP, applied as int(ceil(ep_taken * RECHARGE_HEAT_PER_EP))
   RECHARGE_NODES_PER_FLOOR = (1, 2)  # min, max per floor
   ```
   Optionally per-difficulty override on `Difficulty` dataclass (`recharge_nodes_per_floor`).

3. **`entities/player.py`** — add `energy: int = ENERGY_START` field; method `consume_energy(cost: int) -> bool` (returns False if insufficient, doesn't deduct on failure); `add_energy(amount: int) -> int` (returns actual added, capped at MAX). No legacy compat needed.

4. **`meta/profile.py`** — `Profile.perks` already exists as dict. Confirm `to_dict/from_dict` round-trips it. Document the canonical shape `{perk_id: {"level": int}}` in a docstring. Add `hotbar: list[str|None]` field (length 10, all None default) — persisted hotbar assignments per profile. Update `to_dict/from_dict` and add a test.

5. **i18n keys** in all 3 languages:
   - `perk.<id>.name` and `perk.<id>.desc` for every perk in catalog (~18 perks × 2 keys × 3 langs).
   - `perk.body.brain/eyes/hands/body/legs`.
   - `perk.type.active`, `perk.type.passive`.
   - `perk.deferred` ("Coming soon" / "Brzy" / "Próximamente").
   - `log.perks.no_energy` ("Not enough energy" / "Nedostatek energie" / "Energía insuficiente").
   - `log.perks.fired` ("Activated: {name}" / "Aktivováno: {name}" / "Activado: {name}").
   - Update `.claude/memory/ref_i18n.md`.

**Verification:**
- `pytest tests/test_perks_catalog.py` passes.
- `python -c "from dungeoneer.perks import CATALOG; print(len(CATALOG))"` prints expected count (≥18).
- Existing tests still pass.

**Out of scope:** any UI; any perk effect; recharge nodes (just constants here).

---

## Step 2 — Hub: CyberwareShopOverlay

**Goal:** new top-nav button in MetaScene → tabbed shop overlay → buy/upgrade perks → write to `Profile.perks`, decrement credits, save.

**Read first:**
- `dungeonner_notes/Fatures/perks.md` (Hub UI section + pricing tables)
- `dungeoneer/scenes/meta_scene.py` (full — overlay pattern, top-nav layout)
- `dungeoneer/rendering/ui/settings_overlay.py` (full — closest reference for a tabbed/sectioned overlay with persistence)
- `dungeoneer/rendering/ui/statistics_overlay.py` (skim — another overlay pattern)
- `dungeoneer/rendering/ui/quit_confirm.py` (full — for confirm-buy dialog reuse)
- `dungeoneer/meta/storage.py` (`save_profile` only)
- Step 1 outputs: `dungeoneer/perks/__init__.py` (full), `catalog.py` (full)

**Tasks:**

1. **`rendering/ui/cyberware_shop_overlay.py`** — new file. Class `CyberwareShopOverlay`:
   - Constructor takes `profile`, `on_close`, `on_purchase(profile)` callback.
   - Internal state: `selected_tab: BodyPart`, `selected_perk_id: str|None`, `confirm_dialog: QuitConfirmDialog|None`.
   - `handle_events(events)`, `update(dt)`, `render(screen)` mirror SettingsOverlay style.
   - Layout per perks.md mockup: tabs row top, list left (scrollable), detail right with [Buy]/[Upgrade L2] button.
   - Buy flow: click button → spawn QuitConfirmDialog (key prefix `cyberware_buy_confirm`) → on confirm: deduct credits, increment perk level, call `on_purchase(profile)` (which scene saves).
   - Locked/deferred perks: greyed list row; detail panel shows "Coming soon".
   - Insufficient credits: button label red, disabled.
   - Mouse hit-testing + keyboard nav (arrow keys + Enter/Esc) for parity with other overlays.

2. **`scenes/meta_scene.py`** — add:
   - New nav button slot `nav_cyberware` in top-nav row (between `nav_game` and `nav_prefs`).
   - Dispatch case → opens the overlay (`_cyberware_open: bool`).
   - On purchase callback: `save_profile(self._profile)`.

3. **i18n** (en/cs/es):
   - `nav.cyberware`
   - `cyberware.title`, `cyberware.tab.brain/eyes/hands/body/legs`, `cyberware.btn.buy`, `cyberware.btn.upgrade`, `cyberware.lvl_label`, `cyberware.locked`, `cyberware.insufficient_credits`, `cyberware.confirm_title`, `cyberware.confirm_body` (parameterised with `{name}` and `{price}`).

4. **Tutorial — "buy_perks"** (read `rendering/ui/tutorial_overlay.py` first to learn the existing TutorialManager + step pattern):
   - New step id `"buy_perks"`. Add to `tutorial_overlay.py` step content table with title + body bullets explaining: credits earned during runs, MetaScene Cyberware nav button, body-part tabs, what to buy first (essentials: armor + 1 weapon protocol).
   - Trigger site: `MetaScene.on_enter`. Show iff `profile.tutorial_enabled` and `"buy_perks" not in profile.tutorial_seen` and `profile.stats.runs_completed >= 1` (player must have actually finished a run — survived or died and returned).
   - On dismiss, mark seen and persist (`save_profile`).
   - i18n: `tutorial.buy_perks.title`, `tutorial.buy_perks.body` (multi-line with `>> ` accent lines per existing convention).
   - Procedural illustration: simple coin icon + perk grid mock; reuse the visual conventions from existing tutorial steps.

5. **Tests** `tests/test_cyberware_purchase.py`:
   - Profile starts with 1000 credits. Buy `smartlink` (350) → credits=650, `profile.perks["smartlink"]["level"]==1`.
   - Buy `protocol_smg` L1 then L2 → credits drop by 500+1500, level==2.
   - Insufficient credits → no change.
   - Deferred perk (`mech_arm`) → buy raises or returns False.

**Verification:**
- Run game → main menu → load/create profile → MetaScene → click [Cyberware] → buy a perk → close → reopen → perk shown owned.
- Quit and relaunch → owned perk persists.
- With a fresh profile that has `runs_completed=0`, the buy_perks tutorial does NOT show.
- After completing one run, returning to MetaScene shows the buy_perks tutorial once; dismissing + reopening MetaScene does not show it again.
- `pytest tests/test_cyberware_purchase.py` passes.

**Out of scope:** energy bar HUD, in-run UI, recharge nodes, perk effects.

---

## Step 3 — HUD energy bar + In-run cyberware menu (K) + hotbar

**Goal:** during a run, player sees energy bar; presses K to open menu showing owned perks; assigns active perks to hotbar slots 1–0; presses 1–0 to fire (stub effect = log message + EP deduction).

**Read first:**
- `dungeonner_notes/Fatures/perks.md` (In-run UI section)
- `dungeoneer/rendering/ui/hud.py` (full — heat bar is the reference for energy bar layout/styling)
- `dungeoneer/rendering/ui/inventory_ui.py` (full — closest pattern for the K-menu)
- `dungeoneer/scenes/game_scene.py` — read overlay-handling section: how InventoryUI/HelpCatalog is opened, how key dispatch works in `handle_events`, how mouse routing works
- `dungeoneer/core/event_bus.py` (skim — `LogMessageEvent`)
- Step 1 outputs: `dungeoneer/perks/` (full)
- `dungeoneer/meta/profile.py` — note `Profile.hotbar` field added in Step 1

**Tasks:**

1. **HUD energy bar** in `rendering/ui/hud.py`:
   - Below or beside heat bar at top-center. 180×10 px, neon-blue fill (`(80, 200, 255)`).
   - Label `EP / MAX` next to bar.
   - Reads `player.energy` each frame.

2. **`rendering/ui/cyberware_menu_overlay.py`** — new file. Class `CyberwareMenuOverlay`:
   - Constructor: `profile`, `player`, `on_close`, `on_assign_hotbar(slot, perk_id|None)`.
   - Layout per perks.md mockup: ACTIVE section (with EP cost + hotbar slot indicator), PASSIVE section (always-on list).
   - Click an active perk → enter "assign mode": next 1-0 key press assigns to that slot (or click an empty hotbar slot directly).
   - Esc or K closes.
   - Mouse + keyboard nav.

3. **Hotbar HUD widget** in `rendering/ui/hud.py` (or a new sub-file `hotbar.py` if hud.py is cluttered):
   - 10 slots, dim if empty, lit with icon + EP cost if assigned, red border if EP insufficient.
   - Anchor: above HUD bottom-left, or right of weapon block — pick the cleaner one based on current HUD layout.
   - Tooltip on hover showing perk name + EP cost.

4. **`scenes/game_scene.py`** — wiring:
   - `K` key opens `CyberwareMenuOverlay`. Routing mirrors `InventoryUI` (block input while open, render on top, close on Esc/K).
   - Keys `1`–`0` in gameplay (menu closed) → `_fire_perk(slot)`:
     - Look up `profile.hotbar[slot]`. If None → `log.perks.empty_slot` toast.
     - Look up `PerkDef` from catalog. If `target_required` → enter target-pick mode (stub: just abort with "target required, not implemented yet" log for now — Phase 2 will wire targeting).
     - `if not player.consume_energy(cost)` → post `LogMessageEvent(t("log.perks.no_energy"))`. No turn consumed.
     - Otherwise: post `LogMessageEvent(t("log.perks.fired").format(name=t(perkdef.name_key)))`. **Phase 1 stub** — no actual effect. No turn consumed (Phase 2 will decide per-perk).
   - On cyberware menu close, `save_profile(self._profile)` if hotbar changed.

5. **Cheat menu (F11)** — add buttons "Energy +50" / "Energy MAX" in a new "PERKS" section (small QoL for testing). Read `rendering/ui/cheat_menu.py` first, follow existing pattern.

6. **i18n** (en/cs/es):
   - `hud.energy`
   - `cyberware.menu.title`, `cyberware.menu.section.active`, `cyberware.menu.section.passive`, `cyberware.menu.assign_hint`, `cyberware.menu.always_on`
   - `hotbar.empty`
   - `log.perks.empty_slot`
   - `log.perks.target_required` (stub for Phase 1, real targeting later)

7. **Tutorial — "use_perks"** (TutorialManager pattern same as Step 2):
   - New step id `"use_perks"`. Add to `tutorial_overlay.py` content table with title + body explaining: K opens cyberware menu, assign actives to slots 1–0, press 1–0 in gameplay to fire, EP cost shown, recharge nodes restore EP at heat cost (foreshadow — actual node tutorial implicit in finding one).
   - Trigger site: `GameScene.on_enter` (or first frame of `update`). Show iff `profile.tutorial_enabled` and `"use_perks" not in profile.tutorial_seen` and the profile owns **at least one ACTIVE perk** (use `perks.state` helper; e.g. `any(catalog[id].type == ACTIVE for id in profile.perks)`). The first run after the player buys their first active perk = trigger fires.
   - On dismiss, mark seen and persist.
   - i18n: `tutorial.use_perks.title`, `tutorial.use_perks.body`.
   - Procedural illustration: hotbar mock with one slot lit + key glyph "1".

8. **Tests** `tests/test_perk_fire_stub.py`:
   - Player with energy=20, profile.hotbar[0]="scanner" (cost 8). Call `_fire_perk(0)` → energy=12, log message posted.
   - Player with energy=5 → `_fire_perk(0)` returns False, energy unchanged.
   - Empty slot → no-op + log.

**Verification:**
- Start a run → energy bar visible at 100/100. Press K → menu shows passives + actives (whatever profile owns; use cheat menu in step 2 to buy stuff before running, OR create a debug profile with many perks).
- Assign scanner to slot 1, close menu, press 1 → energy drops 8, log shows "Activated: Sensitive scanner".
- Press 1 enough times to deplete energy → "Not enough energy".
- Quit and relaunch → hotbar assignments persist on the profile.
- Profile with no active perks owned → use_perks tutorial does NOT show on run start.
- After buying first active perk and starting a run → use_perks tutorial shows once; subsequent runs don't show it.
- `pytest tests/test_perk_fire_stub.py` passes.

**Out of scope:** recharge nodes, perk effects, target-pick UI.

---

## Step 4 — Recharge node entity + spawn + interaction overlay

**Goal:** new wall-embedded entity that spawns 1–2 per floor; pressing E adjacent opens overlay with 25/50/75/100% choices; refills EP and adds heat; consumed on use.

**Read first:**
- `dungeonner_notes/Fatures/perks.md` (Energy & dobíjení section + recharge node overlay mockup)
- `dungeoneer/entities/container_entity.py` (full — closest reference: a wall-anchored interactable)
- `dungeoneer/world/dungeon_generator.py` (skim — find where containers / vault / elevator are placed)
- `dungeoneer/scenes/game_scene.py` — find: ElevatorAction handling, container open flow, E-key dispatch, heat application sites
- `dungeoneer/systems/heat.py` (full — `HeatSystem.add_heat()`)
- `dungeoneer/combat/action.py` and `action_resolver.py` — how an Action subclass is created and resolved
- `dungeoneer/rendering/ui/quit_confirm.py` (overlay pattern again)
- `dungeoneer/rendering/entity_renderer.py` and `procedural_sprites.py` — how to add a new sprite_key
- `dungeoneer/core/settings.py` — Step 1 added `RECHARGE_NODE_EP`, `RECHARGE_HEAT_PER_EP`, `RECHARGE_NODES_PER_FLOOR`

**Tasks:**

1. **`entities/recharge_node.py`** — new file. `RechargeNode(Entity)` dataclass: `x, y, capacity_ep: int = RECHARGE_NODE_EP, used: bool = False, sprite_key="recharge_node"`. Embedded in wall tile (blocks=True like a wall, but interactable from adjacent floor tile).

2. **`world/dungeon_generator.py`** — extend generation: after rooms placed, pick `RECHARGE_NODES_PER_FLOOR` random rooms; for each, find a wall tile with exactly one cardinal floor neighbour (same logic as elevator placement); place RechargeNode there. Add to `floor.entities` (or wherever containers/elevators live — match the existing pattern).

3. **`combat/action.py`** — `RechargeAction(node: RechargeNode, amount_ep: int)` Action. Adjacency check.

4. **`combat/action_resolver.py`** — `resolve_recharge(action)`:
   - `actual_added = player.add_energy(action.amount_ep)`
   - `heat_gain = int(math.ceil(action.amount_ep * RECHARGE_HEAT_PER_EP))` — heat charged on requested amount, not actual added (per perks.md: "incentive to pick the right amount").
   - `heat_system.add_heat(heat_gain)`
   - `node.used = True`
   - Post `LogMessageEvent("log.perks.recharged".format(ep=actual_added, heat=heat_gain))`.
   - Consumes a turn (`return True`).

5. **`rendering/ui/recharge_overlay.py`** — small centered overlay. Constructor: `node`, `player`, `on_choice(amount_ep|None)`. Renders 4 options with computed EP gain (capped at `ENERGY_MAX - player.energy`) and heat cost. Disabled rows where EP cap means 0 actual gain. Keys 1–4 + Esc + click.

6. **`scenes/game_scene.py`** wiring:
   - When player presses E adjacent to an unused RechargeNode → open overlay (mirror elevator/vault pattern). Block input while open.
   - On choice: dispatch `RechargeAction(node, amount)`.
   - When `node.used`, render with "spent" sprite/colour and skip the open flow.

7. **`rendering/procedural_sprites.py` + `entity_renderer.py`** — add `recharge_node` sprite (purple/cyan jack icon, simple geometric); add `recharge_node_spent` (greyed out version).

8. **i18n** (en/cs/es):
   - `entity.recharge_node.name`
   - `recharge.title`, `recharge.option` (parameterised: `[{key}] {pct}%   +{ep} EP   +{heat} heat`), `recharge.cancel`, `recharge.spent`
   - `log.perks.recharged` (parameterised `{ep}`, `{heat}`)
   - `hint.recharge` (shown when adjacent: "[E] Recharge")

9. **Cheat menu (F11)** — "Spawn recharge node at player" button in PERKS section.

10. **Tests** `tests/test_recharge_node.py`:
    - Generate a floor → assert 1–2 nodes placed in wall tiles.
    - Player with energy=80 takes 100% (50 EP) → energy=100, +10 heat, node.used=True.
    - Player with energy=100 → all overlay options that yield 0 actual EP shown disabled (test the helper, not the overlay).

**Verification:**
- Start a run → walk floor → find recharge node (cheat menu can spawn one). Press E → overlay opens. Choose 50% → energy +25, heat +5. Press E again → "spent" message, no overlay.
- Heat number on HUD ticks up correctly.
- Generation places nodes within the configured range across multiple seeds.
- `pytest tests/test_recharge_node.py` passes.

**Out of scope:** balancing recharge node density (Phase-2 playtest), perk effects.

---

## Step 5 — Help catalog tab + memory updates + final wiring polish

**Goal:** player-facing help for the new system; memory files reflect the new architecture so future sessions don't re-derive.

**Read first:**
- `dungeonner_notes/Fatures/perks.md` (full — for what to summarize for the player)
- `dungeoneer/rendering/ui/help_catalog.py` (full — tab pattern, `_TABS` list)
- `.claude/memory/arch.md`, `.claude/memory/state.md`, `.claude/memory/MEMORY.md`
- Outputs of Steps 1–4 (paths, not full files): list files added, key class names

**Tasks:**

1. **`rendering/ui/help_catalog.py`** — new tab `CYBERWARE`. Sections:
   - "Cyberware basics" — owned permanently, passives always on, actives cost EP.
   - "Energy" — start of run = 100 EP, refill at recharge nodes.
   - "Recharge" — cost in heat, choose amount, single use per node.
   - "Hotbar" — assign in K menu, fire with 1–0.
   - "Buying perks" — visit Cyberware shop in hub between runs.

2. **i18n** for all the new help strings (en/cs/es): `help_catalog.cyberware.tab`, `help_catalog.cyberware.section.*`, `help_catalog.cyberware.bullet.*`.

3. **Memory updates:**
   - `.claude/memory/arch.md` — add `dungeoneer/perks/` to module map; add `RechargeAction` / `RechargeNode` / new overlays to Key Actions and module sub-tree; add `CyberwareShopOverlay` and `CyberwareMenuOverlay` to `rendering/ui/`.
   - `.claude/memory/state.md` — new section "(date) — Phase 1 perks framework" listing what landed.
   - `.claude/memory/ref_i18n.md` — add all new key prefixes (`perk.*`, `cyberware.*`, `recharge.*`, `log.perks.*`, `hud.energy`, `hint.recharge`).

4. **Update `dungeonner_notes/Fatures/perks.md`** TODO list — mark Phase 1 boxes done.

**Verification:**
- Press F1 in-game → help catalog opens → CYBERWARE tab visible and readable.
- Memory files match the actual code structure.

**No code beyond help+memory.** This step is intentionally light — just polish + handoff.

---

## Cross-cutting reminders for every step

- **Branch:** all commits to `dev`.
- **Don't create perk effects yet.** Step 3's `_fire_perk` is a stub. Step 2's purchase only writes to `Profile.perks`. Real effects are Phase 2.
- **Don't touch deferred perks.** Surge contacts, neural protection, mech arm, trap deployer appear in catalog with `deferred=True`, are visible in shop greyed out, but aren't otherwise wired anywhere.
- **`Pistol` and `knife` stay always-usable** — Phase 2 will gate the other weapons via protocol perks. In Phase 1, all weapons remain at full power; nothing in damage.py changes.
- **Save eagerly.** After every credit/perk/hotbar change → `save_profile(profile)`. Existing pattern; don't invent a new one.

## Final-state verification (after all 5 steps)

1. Fresh profile → MetaScene → Cyberware → buy Smartlink (350c) and Sensitive scanner (600c) → close → relaunch → both still owned.
2. Start run → energy=100 visible. Press K → menu shows Smartlink (passive, always on) and Scanner (active, 8 EP). Assign Scanner to slot 1.
3. Press 1 in gameplay → energy=92, log shows "Activated: Sensitive scanner".
4. Walk floor → find recharge node → press E → choose 50% → energy=100 (capped), heat +5, node spent.
5. Quit run → MetaScene → hotbar slot 1 still shows Scanner.
6. Press F1 → CYBERWARE tab readable.
7. `pytest` — all green.
