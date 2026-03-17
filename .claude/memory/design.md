---
name: Core design decisions
description: Game design rules — combat model, meta-progression goals, visual style, setting
type: project
---

## Setting
Turn-based cyberpunk roguelite. Player = freelance "Diver" exploring underground corp facilities.
Karel builds from scratch iteratively with Claude as collaborator.

## Combat Model
- **1 main action/turn**: move / attack / loot / reload / cover
- Cyberware unlocks support actions that *combine* with main action (not replace)
- Turn order: player-first; each action resolves fully, then enemies go
- 0.14s delay between turns when enemies are visible
- Enemy types: Guard (melee, chase), Drone (ranged, maintain distance)
- Damage ranged (aimed): `damage_min + round(accuracy*(damage_max-damage_min)) - defence`; accuracy ∈ [0,1], -1 = miss
- Damage melee: `roll(damage_min..damage_max) - defence`, min 1; crits on max roll
- SMG burst fire: 3 shots via AimScene (3× F), then staggered DamageEvents at 0.09s intervals via `_burst_queue`
- **Aim minigame**: rotating needle, static hit zone; F or LMB stops needle; Tab cycles targets; LMB on enemy = direct aim; menu toggle `use_aim_minigame`; enemies use `simulate_aim()` statistically

## Items & Ammo
- Ammo types: `"9mm"`, `"rifle"`, `"shell"` — stored in `player.ammo_reserves` dict
- Weapons: Combat Knife, Energy Sword (melee), Pistol, Shotgun, SMG, Rifle (ranged)
- Consumables: Stim Pack, Medkit (H = quick heal with overheal confirmation)
- Inventory: 8 slots, auto-pickup on move

## Meta-Progression
- Skill web (spider-web unlock tree) — unlocks cyberware, skills, items in loot pool, run modifiers
- Focus: **new playstyles, NOT bigger numbers** (not a power inflation game)
- Credits from loot → spent between runs

## Visuals
- Top-down 2D pixel art, 32×32 tiles
- Dithart sci-fi tileset (`tileset_for_free.png`), procedural coloured-square fallback
- Neon cyberpunk palette for UI (minigame: cyan/green/red/orange on dark bg)

## Floors & Win Condition
- 3 floors; final floor has Objective Vault instead of stairs → victory
- Stair/Objective events fire via EventBus
