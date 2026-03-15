---
name: project_dungeoneer
description: Core context — setting, mechanics, tech stack, current state, architecture overview
type: project
---

# Dungeoneer — projekt overview

Cyberpunk dungeon crawler (roguelike). Hráč je "Diver" pronikající do korporátní základny přes procedurálně generovaná podlaží. Cíl: dostat se do trezoru na posledním patře a uniknout.

**Why:** Osobní projekt v rané fázi vývoje. Technicky funkční, herní smyčka běží end-to-end.

---

## Tech stack

- Python + **pygame-ce** ≥ 2.5.0 (grafika, okno)
- **tcod** ≥ 16.0.0 (FOV algoritmus)
- **numpy** ≥ 1.26.0 (tile arrays)
- **pytest** ≥ 8.0.0 (testy)
- Entry point: `main.py` → `dungeoneer/core/game.py` (`GameApp`)
- Okno: 1280×720, 60 FPS, tile size 32px, mapa 60×40

---

## Aktuální stav (2026-03-15)

MVP + post-MVP UI polish vrstva:

- Procedurální generování dungeonů (BSP)
- Tahový systém (hráč → nepřátelé), 0.14s delay při visible nepřátelích
- Dva typy nepřátel (Guard melee, Drone ranged)
- Inventář (8 slotů), zbraně, spotřební předměty, munice
- FOV (viditelnost), kamera sledující hráče
- **UI:** HUD, CombatLog, InventoryUI, WeaponPickerUI (`C`), HelpScreen (`F1`), AlertBanner (`!`)
- **Tileset:** Dithart sci-fi tileset s 4-bit autotile mapping; procedurální fallback sprites
- **Lokalizace:** `core/i18n.py` — en / cs, klíče přes `t("key")`, jazyk v `settings.LANGUAGE`
- Audio manager (integrován přes event bus)
- 3 patra, na posledním Objective Vault = výhra
- Difficulty presets: Easy / Normal / Hard
- SMG burst fire: staggered DamageEvents (0.09 s intervaly)
- H quick-heal s overheal potvrzením

### Stubs (zatím nefunkční)
- `cyberware/` — framework existuje, není napojený
- `skills/` — prázdný adresář
- `meta/` — stub

---

## Architektura

```
dungeoneer/
├── core/         # GameApp, SceneManager, EventBus, settings, difficulty, logging, i18n
├── entities/     # Entity, Actor, Player, Enemy, ItemEntity, ContainerEntity
├── items/        # Item, Weapon, Consumable, Ammo, Inventory
├── combat/       # TurnManager, Action, ActionResolver, damage, LOS
├── ai/           # Brain, BehaviorState (Idle/Combat), Pathfinder (A*), perception
├── world/        # DungeonGenerator (BSP), DungeonMap, Floor, Tile, FOV
├── rendering/    # Renderer, Camera, TileRenderer, EntityRenderer, ProceduralSprites
│   └── ui/       # HUD, CombatLog, InventoryUI, WeaponPickerUI, HelpScreen, AlertBanner,
│                 #   FloatingNumbers, RangeOverlay
├── audio/        # AudioManager
├── scenes/       # GameScene, GameOverScene
├── data/         # Definice nepřátel, itemů
├── skills/       # (stub)
├── cyberware/    # (stub)
└── meta/         # (stub)
```

---

## Entity systém

**Player ("Diver"):** 30 HP (normal), Pistol (8 nábojů) + Combat Knife, 8 inventárních slotů
**Guard (Corp Guard):** 12 HP, útok 3, obrana 1 — melee, chasing
**Drone (Sec Drone):** 8 HP, útok 2, obrana 0 — ranged, udržuje vzdálenost 4 tilesů

**Zbraně:** Combat Knife, Pistol, Shotgun, SMG (burst), Rifle, Heavy Baton
**Consumables:** Stim Pack (malé léčení), Medkit (velké léčení)
**Ammo:** 9mm, Shotgun shells, Rifle rounds

---

## Bojový systém

- Výpočet poškození: roll(weapon_dmg) + actor.attack − defender.defence, min 1
- Kritické zásahy: implementovány
- Ranged vyžaduje LOS (raycast)
- Akce: Move, MeleeAttack, RangedAttack, Wait, Reload, Equip, UseItem, DropItem, OpenContainer, Stair

---

## Herní smyčka

1. Floor 1–3: BSP dungeon, nepřátelé, kontejnery, schody dolů
2. Floor 3: místo schodů Objective Vault → otevřít = výhra
3. Hráč zemře → Game Over

**Turn delay:** 0.14s když jsou nepřátelé visible (pacing)
**Auto-pickup:** pohyb přes item → sebrání (ammo → rezervy, duplikát zbraně → ammostripování)

---

## Roadmap

1. **MVP** ✅ — dungeon gen, combat, 2 enemy types, win/lose
2. **UI Polish** ✅ — weapon picker, help screen, alert banner, i18n, tileset
3. **Content** — main menu, více nepřátel/itemů, multi-floor polish, save/load
4. **Cyberware + Skills** — implants, action combining, status effects
5. **Meta-progression** — skill web UI, JSON save, run modifiers
6. **Polish** — animace, particles, audio, více obsahu
