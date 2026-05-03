# Perks (Cyberware) — Mechanics Design Plan

## Context

Karel wants to start work on the Perks system from `dungeonner_notes/Fatures/Metagame — perky, skilly, progrese.md`. This plan is the **mechanics-design phase only** — implementation planning comes after. The aim is to lock down: perk balance numbers, energy & heat economy, hub-shop pricing, and high-level UI concepts (in-run + hub) so the next phase can plan implementation per-area.

Long-game intent (Karel's words):
- Player is overwhelmed early on Normal; perks unlock approaches, not flat power.
- Active perks cost energy → in-fight tradeoffs.
- Energy refills cost heat → strategic-pacing tradeoff.
- Essentials (weapon/armor/ICE protocols) are cheap so first runs aren't crippled forever.
- Higher levels (especially weapon protocols) get steeply more expensive.
- Vault credits also fund non-perk things later, so perks shouldn't soak up 100% of budget.

## Decisions locked with Karel

1. **Free combination** — every owned perk is permanently active. No slots, no loadout step.
2. **In-run activation** — one menu key (like inventory) lists all owned perks; active perks can be assigned to a 1‑0 hotbar.
3. **Starter loadout** — pistol + knife only. All other weapons, armor, ICE protection, grenades require perks.
4. **Recharge nodes** — fixed-capacity wall nodes; player picks 25/50/75/100% to take; heat scales with amount taken; one use per node.
5. **Pricing anchor** — essential L1 perks 300–600 credits (~1 vault clear).
6. **Heat from perks** — only refills generate heat; activation itself is heat-free.

---

## 1. Energy & Heat economy

### Energy pool
- `Player.energy` (new field). **Run-scoped pool**, persists across floors, refilled only at recharge nodes. Resets to `ENERGY_START = 100` at the start of each run.
- Hard cap `ENERGY_MAX = 100` (refills past 100 are wasted — mirrors HP healing logic).
- Active perk activation deducts EP; if `energy < cost` → action fails with `log.perks.no_energy` toast.

### Recharge nodes
- Spawn in wall tiles inside revealed rooms (1–2 per floor; tunable per difficulty).
- Sprite: small purple/cyan jack icon embedded in wall. Discoverable like containers.
- Node capacity `RECHARGE_NODE_EP = 50`.
- Interaction: small overlay "Take 25 / 50 / 75 / 100% (+X heat)". Confirm or cancel.
- **Heat cost**: `+1 heat per 5 EP taken`. So 25 EP → +5 heat, 50 EP → +10 heat.
- **Single use per node** (matches notes: "1× na místo").
- Per run baseline: 100 starting + ~2 nodes × 50 EP = ~200 EP total → 10–13 expensive activations or 25+ cheap ones across the whole run.

### Heat interaction
- Heat gain channels stay limited and legible: combat (existing), hacking (existing), **recharge nodes (new)**.
- Activation never generates heat directly. The dial Karel can tune later if a perk feels too spammable: increase its EP cost, not its heat cost.

---

## 2. Rebalanced perk table

**Revised down (Karel feedback):** original costs felt too high — perks with tradeoffs (Strip armor, Reflex fibres, Nanobots) and Cloak should be *usable*, not hoarded. New scale gives roughly **8–15 baseline uses per 100 EP** for cheap actives, **5–7** for expensive ones. Cloak from full should comfortably escape one encounter and leave a healthy buffer.

### 2.1 Active perks

| Perk | Body | EP / use | Notes / tradeoff |
|---|---|---|---|
| Sensitive-spot scanner (aim buff) | Eyes | **8** | +20% needle speed, +20% damage on next ranged shot. ~12/run. |
| Reflex fibres (move + shoot) | Legs | **8** | Move + ranged in same turn at half accuracy. Half-accuracy is the real tradeoff. ~12/run. |
| Chameleon skin (cloak) | Body | **2 / turn** while active | Toggle on; drains every turn while active. Breaks on attack/hack. Full pool = 50 turns; a 10-turn escape costs 20 EP and leaves 80. |
| Recoil compensators (strip armor) L1 | Hands | **10** | Next hit −1 armor, −20% accuracy. ~10/run. |
| Recoil compensators L2 | Hands | **15** | Next hit −2 armor, −20% accuracy. ~6/run. |
| Nanobots (heal) | Body | **15** | Heals 8 HP, stacking −20% accuracy on next fight (decays after a fight). ~6/run. |
| Neural protection (ICE block) L1 | Brain | **15** | One ICE convert per minigame, must hit during warning window. The timing window is itself the tradeoff. *(deferred — needs warning-window feature)* |
| Neural protection L2 | Brain | **15** (per use) | Two converts per minigame. *(deferred)* |
| Trap deployer | Legs | **12** | Place trap on tile. *(deferred — needs trap entity)* |
| Surge contacts (secret passage) | Hands | **20** | Open hidden passage from outside. *(deferred — needs secret passages)* |

### 2.2 Passive perks

| Perk | Body | Effect |
|---|---|---|
| Smartlink | Eyes | Ranged crit → 1-turn stun on target. |
| Muscle implants | Hands | Melee crit → 30% bleed/short DoT (organic vs mechanical). |
| Skeleton reinforcement | Body | Unlocks armor — without it, armor cannot be equipped. |
| SMG protocol L1 / L2 / L3 | Brain | L1 unlocks SMG full accuracy. L2/L3 enable in-run weapon upgrades. |
| Shotgun protocol L1 / L2 / L3 | Brain | Same pattern; without L1, shotgun damage halved. |
| Rifle protocol L1 / L2 / L3 | Brain | Same pattern. |
| Energy-sword protocol L1 / L2 / L3 | Brain | Same pattern. |
| Mechanical arm | Hands | Unlocks grenades. *(deferred)* |
| Electronic lenses | Eyes | +1 sight radius (asymmetry vs enemies — disengage without heat). |
| Network scan L1 / L2 / L3 | Brain | Reveals loot kinds in hack: L1 heal, L2 ammo, L3 weapons. |

Passives are **always on once owned** (no toggle UI needed — keeps mental model simple).

---

## 3. Hub shop pricing

Anchor: vault ≈ 500 credits/run on Normal. Essentials ≈ 1 vault. Weapon L2/L3 escalate steeply.

### Essentials (cheap — first buys)

| Perk | L1 | L2 | L3 |
|---|---|---|---|
| Skeleton reinforcement (armor unlock) | **400** | — | — |
| Smartlink | **350** | — | — |
| Muscle implants | **350** | — | — |
| Electronic lenses | **500** | — | — |
| SMG protocol | **500** | 1500 | 3000 |
| Shotgun protocol | **500** | 1500 | 3000 |
| Rifle protocol | **500** | 1500 | 3000 |
| Energy-sword protocol | **500** | 1500 | 3000 |
| Neural protection | **500** | 1500 | — |

### Mid (active utilities — buy after essentials)

| Perk | L1 | L2 |
|---|---|---|
| Sensitive-spot scanner | **600** | — |
| Reflex fibres | **700** | — |
| Recoil compensators (strip armor) | **700** | 1800 |
| Chameleon skin | **800** | — |
| Nanobots | **800** | — |

### Flat-cost utility

| Perk | L1 | L2 | L3 |
|---|---|---|---|
| Network scan | **700** | 1000 | 1500 |

### Deferred (priced when implemented)

Mechanical arm (grenades), Trap deployer, Surge contacts (secret passages).

**Total full buyout** (excluding deferred): ~38 000 credits → ~75 vault clears. Plenty of headroom for non-perk credit sinks later.

---

## 4. Hub UI — Cyberware shop

### Entry point
New item in the existing `MetaScene` Game dropdown OR a new top-nav button **[Cyberware]** between **[Game]** and **[Preferences]**. Recommend: new nav button — frequent enough access to deserve top-level placement.

### Overlay structure (`CyberwareShopOverlay`)
Mirrors the established overlay pattern (`SettingsOverlay`, `StatisticsOverlay`).

```
┌─ Cyberware ─────────────────────────────────────────────── [X] ┐
│ Credits: 1240                                                  │
│                                                                │
│ ┌─ Tabs ────────────────────────────────────────────────────┐  │
│ │ [Brain] [Eyes] [Hands] [Body] [Legs]                      │  │
│ └───────────────────────────────────────────────────────────┘  │
│                                                                │
│ ┌─ List (left, scroll) ──────┐  ┌─ Detail (right) ──────────┐  │
│ │ ✓ Skeleton reinf.   400 ★  │  │ Sensitive-spot scanner    │  │
│ │ ☐ Sensitive scan.   600    │  │ Active │ Eyes │ Cost 15 EP│  │
│ │ ☐ Chameleon skin    800    │  │                           │  │
│ │ ☐ Recoil comp. L1   700    │  │ Next ranged shot: needle  │  │
│ │   └ L2             1800    │  │ +20% speed, +20% damage.  │  │
│ │ — Mech. arm   (locked)     │  │                           │  │
│ │                            │  │ [ Buy — 600 credits ]     │  │
│ └────────────────────────────┘  └───────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

- Owned: ✓ icon, level badge, "Upgrade L2 — 1500c" button if applicable.
- Locked (deferred): greyed out, tooltip "Coming soon".
- Insufficient credits: button disabled with red price.
- Confirm-buy uses existing `QuitConfirmDialog` pattern with key prefix `cyberware_buy_confirm`.
- Persistence: writes to `Profile.perks` (already reserved); credits decremented and saved atomically via existing `meta/storage.py` flow.

---

## 5. In-run UI

### HUD changes
Add an **energy bar** under the heat bar (top-center). Same styling as heat: 180×10 px, neon-blue fill, numeric `EP/MAX` label. Tooltip on hover: "Cyberware energy".

### Cyberware menu (key `K`)
Modal overlay analogous to `InventoryUI`:

```
┌─ Cyberware ───────────────────────────── [Esc] close ──┐
│ Energy: 65 / 100                                       │
│                                                        │
│ ACTIVE                                  Hotbar         │
│  ▸ Sensitive scanner    8 EP   [1]      1: Scanner     │
│  ▸ Chameleon skin       2/t    [-]      2: Cloak       │
│  ▸ Recoil comp. L1     10 EP   [2]      3: -           │
│  ▸ Nanobots            15 EP   [-]      4: -           │
│                                                        │
│ PASSIVE (always on)                                    │
│  • Smartlink                                           │
│  • Skeleton reinforcement                              │
│  • SMG protocol L1                                     │
│                                                        │
│ Click an active perk to assign/clear hotbar slot.      │
└────────────────────────────────────────────────────────┘
```

- Selecting an active perk while menu is open prompts for hotbar slot 1–0 (or click an empty slot directly).
- Pressing 1–0 in-game **with menu closed** fires the assigned perk if EP and game-state allow it.
- Targeting actives (Strip-armor, Trap) enter a target-pick mode similar to ranged attack.
- Hotbar UI: thin row above HUD bottom-left or right of the weapon/HUD block. 10 slots, dim if empty, lit with icon + EP cost if assigned, red if EP insufficient.

### Recharge node interaction
Press `E` adjacent to a node → small centered overlay:

```
┌─ Recharge node ────────────────┐
│ Take:                          │
│   [1] 25%   +12 EP   +5 heat   │
│   [2] 50%   +25 EP   +5 heat   │
│   [3] 75%   +37 EP   +8 heat   │
│   [4] 100%  +50 EP  +10 heat   │
│   [Esc] cancel                 │
└────────────────────────────────┘
```

- Only options that actually add EP (ignoring overflow) are enabled — caps at `ENERGY_MAX`.
- Heat numbers are the gross gain; overflow EP is wasted but heat is still charged at the level the player picked (incentive to pick the right amount).
- Single-use: node sprite changes to spent/empty after interaction.

---

## 6. Deferred — perks needing new game features

These are out of scope until their underlying feature ships. List them in `state.md` "Stubs" so they don't get lost.

| Perk | Needs |
|---|---|
| Neural protection | ICE warning-window mechanic in hack minigame (currently ICE triggers instantly on step) |
| Surge contacts (secret passages) | Hidden passage / secret door world-gen feature |
| Mechanical arm (grenades) | Grenade item type + thrown-area-damage action |
| Trap deployer | Trap entity (placeable, triggers on enemy step, damage) |

When these features land, this plan's pricing/EP-cost rows can be adopted directly.

---

## 7. What the next phase plans (in order)

Karel called this out: implementation planning happens in subsequent phases, in this order:

1. **Energy + heat plumbing + hub shop UI + in-run cyberware menu/hotbar** (the framework).
2. **Implementable perks one by one** (the 14 in §2 marked non-deferred), grouped by hook site:
   - Damage-pipeline perks (Smartlink, Muscle implants, Skeleton-armor, weapon protocols, Strip armor, Scanner, Reflex fibres, Nanobots).
   - Perception perks (Lenses, Network scan).
   - Stealth perk (Chameleon skin) — needs enemy AI awareness logic.
3. **Feature-gated perks** (the 4 in §6) once their underlying features exist.

Each step gets its own Plan-mode pass at that time.

---

## 8. Verification (for this design — manual, with Karel)

Since this plan is mechanics, not code, "verification" is a review pass:

1. Read the rebalanced EP costs in §2 against the long-game pacing in the Context section. Are the cheap actives cheap enough that the player actually uses them, and the expensive ones rare enough to feel weighty?
2. Simulate run 1–5 progression with the §3 prices: starting 0 credits, ~500/run, what's the buy order? Does the player have a working SMG + armor + scan by run 5? (Should be yes.)
3. Check perk count vs hotbar slots: 10 active slots, ~7 active perks total — comfortable.
4. Confirm deferred list (§6) doesn't accidentally include a perk that *is* currently implementable.

If anything in the table feels wrong on review, edit the numbers in this file directly — it's the spec the next-phase implementation plans will reference.

## Critical files (for next-phase reference, not this phase)

- `dungeoneer/meta/profile.py` — `Profile.perks` dict (already exists, line 96+).
- `dungeoneer/meta/storage.py` — atomic profile save flow (reuse).
- `dungeoneer/scenes/meta_scene.py` — add cyberware nav + overlay.
- `dungeoneer/entities/player.py` — add `energy` field (line 17–72).
- `dungeoneer/core/settings.py` — add `ENERGY_START`, `ENERGY_MAX`, `RECHARGE_NODE_EP`, heat-per-EP constant.
- `dungeoneer/rendering/ui/hud.py` — energy bar.
- `dungeoneer/rendering/ui/` — new `cyberware_overlay.py` (in-run) and `cyberware_shop_overlay.py` (hub).
- `dungeoneer/combat/damage.py` — perk hook in `_weapon_roll` / `calc_*` for protocol gates and crit effects.
- `dungeoneer/minigame/hack_scene_grid.py` — Network scan loot reveal hook; (later) Neural protection ICE hook in `_on_move_into_security`.
- `dungeoneer/core/i18n.py` — new `perk.*`, `cyberware.*`, `log.perks.*` keys × 3 languages.
- `dungeoneer/rendering/ui/help_catalog.py` — new tab for cyberware controls.
