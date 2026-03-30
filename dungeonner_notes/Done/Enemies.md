## Enemy Roster — Tier systém

Nepřátelé mají 3 tiery. Heat mechanic (5 tierů) určuje, kteří nepřátelé spawnují:
- Heat tier 1–2 → spawn z Tier 1
- Heat tier 3 → spawn z Tier 1–2
- Heat tier 4–5 → spawn z Tier 1–3

Gradace obtížnosti = vyšší tiery nepřátel + větší počty.

---

### Tier 1 — Standardní facility security

| Jméno | Styl | HP | Def | Pohyb | Zbraň |
|---|---|---|---|---|---|
| Guard (Stráž) | Melee | 12 | 1 | 1 | combat_knife |
| Drone (Strážní dron) | Ranged | 8 | 0 | 1 | pistol |
| Dog (Strážní pes K9) | Melee | 6 | 0 | 2 | k9_bite |

**Guard** — melee chaser, standardní hlídač.

**Drone** — ranged, udržuje vzdálenost ~4 tile. Ustoupí pokud se hráč přibližuje a neútočí na Drona.

**Dog** — 2 pohyby za tah, ale útočí jen jednou. Fragile — nebezpečný ve skupině. k9_bite má nízký dmg (1–3), aby hráče nesežral příliš rychle.

---

### Tier 2 — Posílená odpověď

| Jméno | Styl | HP | Def | Pohyb | Zbraň |
|---|---|---|---|---|---|
| Heavy (Těžký) | Ranged | 15 | 3 | 1 | pistol |
| Turret (Automatická věž) | Ranged | 12 | 1 | 0 | pistol |

**Heavy** — přiblíží se na ~4 tile, pak střílí. Nikdy neustupuje. Def=3 = odolný.

**Turret** — nehybná. 2 výstřely za tah. Pokud ztratí LOS, přejde zpět do Idle. Spawnuje v místnostech.

---

### Tier 3 — Taktické jednotky

| Jméno | Styl | HP | Def | Pohyb | Zbraň |
|---|---|---|---|---|---|
| Sniper Drone (Ostrostřelec) | Ranged | 6 | 0 | 1 | rifle |
| Riot Guard (Těžkooděnec) | Melee | 16 | 4 | 1 | combat_knife |

**Sniper Drone** — udržuje maximální vzdálenost (~7+ tile). Vždy ustupuje pokud se hráč přiblíží. aim_skill=6.0. Prioritní cíl — fragile ale nebezpečný.

**Riot Guard** — obrnění melee. Def=4 nutí hráče střílet. Slouží jako "shield" před ostatními nepřáteli.
