# Vizuální styl + modely — Dungeoneer assets

Přečíst když: vybíráš model, kontroluješ konzistenci assetu, nebo sestavuješ prompt a potřebuješ znát paletu.

---

## MODELY

### Aktuální sestava
- Base: **SDXL 1.0**
- LoRA: `pixel-art-xl-v1.1` (váha 1.0)
- Problém: LoRA je biasovaná na celé zbraně, špatně generuje izolované malé objekty

### Doporučená sestava pro item ikony (✅ nainstalováno)

| Model | URL | Umístění |
|---|---|---|
| **Illustrious XL** (checkpoint) | civitai.com/models/795765 | `models/Stable-diffusion/` |
| **Pixel Art Game UI Icons LoRA** | civitai.com/models/2443581 | `models/Lora/` |

Po stažení — prompt pro item ikony:
```
<lora:pixel-art-xl-v1.1:0.6>, <lora:pixel_art_game_ui_icons:0.8>, pixelarticon, cyberpunk, [SUBJEKT], ...
```
Trigger word: `pixelarticon` — přidat na začátek positive promptu.

### Alternativa — Pixel Art Diffusion XL (full checkpoint, ~6.5 GB)
- civitai.com/models/277680 → `models/Stable-diffusion/`
- Nevyžaduje LoRA, konzistentní quality pro game sprity

---

## VIZUÁLNÍ STYL PROJEKTU

Styl byl odvozen z existujících schválených assetů (weapon_pistol, weapon_shotgun, weapon_rifle, weapon_smg, weapon_combat_knife, weapon_energy_sword). **Každý nový asset musí odpovídat těmto pravidlům.**

### Paleta

| Role | Barva | Poznámka |
|---|---|---|
| Tělo objektu | Tmavý teal `#1a3535` – `#1f4040` | Dominantní plocha — ne šedá, ne černá |
| Highlight / hrana | Bright cyan `#00d4d4` – `#00e8e8` | Světlá linka na exponované hraně |
| Outline / stín | Velmi tmavý teal `#0d1f1f` – `#111` | Pixel outline, ne čistá černá |
| Accent (volitelný) | Bright cyan / neon teal | Vnitřní detail, trigger, scope lens |

- Maximálně **3 barvy** + průhlednost — každá plocha jednobarevná (žádný gradient)
- **Bez teplých barev** — žádná oranžová, červená, žlutá (výjimka: krev/výbuchy v herním kontextu, ne ikony)
- **Výjimka — kredity**: `credits_credits.png` má teal tělo + zlatý ¥ symbol — záměrný gold accent. Asset **negenerovat přes SD** — PIL skript.
- Energetické zbraně (energy_sword) mohou mít tělo i highlight v bright cyan → "glow" efekt

### Tvar a čitelnost

- **Silueta** okamžitě čitelná na 32×32 px — minimum detailů, žádné složité výřezy
- **Hard pixel edges** — nulový anti-aliasing, ostré přechody barev
- **Orientace item ikon**: vždy 45° diagonálně `/` — hlaveň/špička vpravo nahoře, rukojeť/základna vlevo dole (zajišťuje PCA post-processing, NE prompt)
- **Edge-to-edge pokrytí** — 1–2px padding (zajišťuje post-processing, NE prompt)

### Referenční assety

```
assets/items/weapon_pistol.png        ← pistole, základní tvar
assets/items/weapon_rifle.png         ← dlouhá zbraň, úzký profil
assets/items/weapon_shotgun.png       ← krátká tlustá hlaveň
assets/items/weapon_smg.png           ← kompaktní tělo
assets/items/weapon_combat_knife.png  ← čepel, minimalistická silueta
assets/items/weapon_energy_sword.png  ← glow varianta (uniformně bright)
```

### Checklist konzistence stylu

- [ ] Dominantní barva je tmavý teal (ne šedá, ne modrá, ne zelená)
- [ ] Highlight je bright cyan podél exponované hrany
- [ ] Max 3 barvy celkem
- [ ] Orientace 45° (platí pro item ikony)
- [ ] Silueta odpovídá objektu na 32px
- [ ] Žádné teplé barvy
