# Perky (Cyberware) — design summary

> Aktuální stav po designovém průchodu. Implementace ještě nezačala.
> Detailní implementační plán: `.claude/plans/perks_design.md`.

---

## Klíčová rozhodnutí

- **Volná kombinace** — všechny koupené perky jsou trvale aktivní. Žádné sloty, žádné loadouty.
- **Start runu** — pouze nůž + pistole. Vše ostatní (zbraně, brnění, ICE ochrana, granáty) vyžaduje perky.
- **Energie je per-run** — startuje na 100, dobíjí se jen na recharge nodech, přetéká mezi patry.
- **Heat z perků pouze při dobíjení.** Aktivace perku samotná heat negeneruje. Tunit lze přes EP cenu, ne přes heat.
- **Pasivní perky = vždy zapnuté.** Žádný toggle.

---

## Energie & dobíjení

| Konstanta | Hodnota |
|---|---|
| `ENERGY_START` | 100 |
| `ENERGY_MAX` | 100 |
| Kapacita node | 50 EP |
| Heat za dobíjení | **+1 heat / 5 EP** |
| Nody na patro | 1–2 (tunable per difficulty) |

**Recharge node UX:** zeď, malá ikona jacku. Press `E` adjacentně → overlay s volbou 25 / 50 / 75 / 100 % (každá hodnota ukáže získané EP a heat). Jedno použití na node, pak "spent" sprite.

**Bilance per run:** 100 start + ~2 nody × 50 EP = až ~200 EP. Heat z plného dobití obou nodů = +20 heat — citelné, ale zvládnutelné.

---

## Perky — rebalanced tabulka

### Aktivní

| Done | Perk                              | Tělo  | EP           | Ikona                                | Tradeoff / poznámka                                             | Cena L1 / L2 |
| ---- | --------------------------------- | ----- | ------------ | ------------------------------------ | --------------------------------------------------------------- | ------------ |
|      | Skener citlivých míst             | Oči   | **8**        | `perk_scanner.png` (13_34)           | +20 % rychlost ručičky, +20 % dmg na příští ranged útok         | 600 / —      |
|      | Reflexní vlákna (move+shoot)      | Nohy  | **8**        | `perk_reflex_fibres.png` (13_29)     | Pohyb + střelba v jednom kole, poloviční přesnost               | 700 / —      |
|      | Chameleoní kůže (cloak)           | Tělo  | **2 / kolo** | `perk_cloak.png` (13_19)             | Toggle, drain každé kolo, ruší se útokem/hackem                 | 800 / —      |
|      | Kompenzátory (strip armor)        | Ruce  | **10 / 15**  | `perk_recoil_comp.png` (13_37)       | Příští zásah −1 / −2 armor, −20 % přesnost                      | 700 / 1800   |
|      | Nanoboti (heal)                   | Tělo  | **15**       | `perk_nanobots.png` (13_11)          | Heal 8 HP, kumulativní −20 % přesnost na příští fight           | 800 / —      |
|      | Neuronová ochrana (ICE block)     | Mozek | **15**       | `perk_neural_protection.png` (13_35) | 1× per minigame (L1), 2× (L2). Musí se trefit do warning window | 500 / 1500   |
|      | Past                              | Nohy  | **12**       | `perk_trap.png` (13_25)              | Položí past na tile                                             | *(deferred)* |
|      | Přepěťové kontakty (tajná chodba) | Ruce  | **20**       | `perk_surge_contacts.png` (13_38)    | Otevře tajnou chodbu zvenčí                                     | *(deferred)* |

### Pasivní

| Perk                            | Tělo  | Efekt                                               | Cena              |
| ------------------------------- | ----- | --------------------------------------------------- | ----------------- |
| Smartlink                       | Oči   | Ranged crit → 1 kolo stun                           | 350               |
| Svalové implantáty              | Ruce  | Melee crit → 30 % bleed/zkrat                       | 350               |
| Zesílení kostry                 | Tělo  | Odemkne brnění                                      | 400               |
| Elektronické čočky              | Oči   | +1 dohled (asymetrie vůči nepřátelům)               | 500               |
| Protokol SMG                    | Mozek | L1 odemkne SMG, L2/L3 in-run weapon upgrade         | 500 / 1500 / 3000 |
| Protokol brokovnice             | Mozek | totéž                                               | 500 / 1500 / 3000 |
| Protokol pušky                  | Mozek | totéž                                               | 500 / 1500 / 3000 |
| Protokol energomeče             | Mozek | totéž                                               | 500 / 1500 / 3000 |
| Network scan (analytický okruh) | Mozek | L1 reveals heal, L2 ammo, L3 weapons v hack minihře | 700 / 1000 / 1500 |
| Mechanické rameno               | Ruce  | Odemkne granáty                                     | *(deferred)*      |

### Implementovatelné teď vs. deferred

- **Hned implementovatelné (14 perků):** Smartlink, Svaly, Skener, Reflexní vlákna, Cloak, Kompenzátory L1+L2, Nanoboti, Kostra, 4× weapon protocols (po 3 levelech), Čočky, Network scan
- **Deferred (potřebují novou featuru):**
  - Neuronová ochrana → potřebuje warning-window mechaniku v hack minigame a hlavně předělat negativní nody na opakovaný efekt
  - Tajné chodby → potřebuje secret-door world-gen feature
  - Granáty → potřebuje grenade item + thrown-damage action
  - Past → potřebuje trap entitu

---

## UI — hub (mezi runy)

Nová položka v `MetaScene` top-nav baru: **[Cyberware]** mezi [Game] a [Preferences].

**`CyberwareShopOverlay`:**
- Záložky podle částí těla: Brain / Eyes / Hands / Body / Legs.
- Levý sloupec: scrollable list perků v dané záložce (✓ owned, ⨯ locked, šedý = deferred).
- Pravý sloupec: detail vybraného perku — popis, EP cost, [Buy] / [Upgrade L2] tlačítko.
- Confirm-buy přes existující `QuitConfirmDialog` pattern.
- Zápis do `Profile.perks` (už existuje v `meta/profile.py`), credits přes existující save flow.

---

## UI — in-run

### HUD
- **Nový energy bar** pod heat barem (top-center). Neon-blue, 180×10 px, label `EP / MAX`.

### Cyberware menu (klávesa **K**)
- Modální overlay jako inventář.
- 2 sekce: ACTIVE (s EP cenami a hotbar slot indikátorem) a PASSIVE (always on, jen list).
- Klikem na aktivní perk → přiřazení do hotbar slotu (1–0).

### Hotbar
- Tenká řada nad/vedle HUD, sloty 1–0.
- Stisk 1–0 v gameplay → triggne perk (pokud je dost EP a stav hry to dovolí).
- Targetované perky (Strip armor, Past) přejdou do target-pick módu.

### Recharge node overlay
```
Take:
  [1] 25%   +12 EP   +3 heat
  [2] 50%   +25 EP   +5 heat
  [3] 75%   +37 EP   +8 heat
  [4] 100%  +50 EP  +10 heat
```

---

## TODO list

### Fáze 1 — framework (nejdřív) ✅ HOTOVO (2026-05-03)
- [x] `Player.energy` field + settings konstanty (`ENERGY_START`, `ENERGY_MAX`, `RECHARGE_NODE_EP`, heat-per-EP)
- [x] HUD energy bar
- [x] `CyberwareShopOverlay` v hubu (pricing tabulka výše)
- [x] In-run `CyberwareMenuOverlay` (klávesa K) + hotbar 1–0
- [x] Recharge node entity + spawn logika v dungeon generátoru + interaction overlay
- [x] i18n klíče (`perk.*`, `cyberware.*`, `log.perks.*`) v en/cs/es
- [x] Help catalog tab pro cyberware

### Fáze 2 — implementovatelné perky (per skupinu)
- [ ] Damage-pipeline perky: Smartlink, Svalové implantáty, Skeleton (armor unlock), 4× weapon protocols, Strip armor, Skener, Reflexní vlákna, Nanoboti
- [ ] Perception perky: Elektronické čočky, Network scan
- [ ] Stealth: Chameleoní kůže (potřebuje úpravu enemy AI awareness)

### Fáze 3 — feature-gated perky (po implementaci základních feature)
- [ ] Implementovat ICE warning-window v hack minigame → **Neuronová ochrana**
- [ ] Implementovat secret doors ve world-genu → **Přepěťové kontakty**
- [ ] Implementovat grenade item + thrown action → **Mechanické rameno**
- [ ] Implementovat trap entitu → **Past**

### Open questions / ladění (live)
- Heat-per-EP 1:5 — možná upravit po prvním playtestu (pokud hráč moc často/málo dobíjí)
- Počet recharge nodů per patro a per difficulty
- Cloak 2 EP/turn — playtest ověřit, jestli "escape z encountru + buffer" funguje
- ICE warning window timing (až bude implementováno)
