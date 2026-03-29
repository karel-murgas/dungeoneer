# Generování assetů — Cyberpunk Roguelite

Tyto instrukce používej vždy, když máš vygenerovat herní asset (sprite, ikonu, prostředí, portrét, ...).

---

## KONFIGURACE PROJEKTU

```
ASSETS_DIR=dungeoneer/assets
WEBUI_BAT=C:\Users\karel\Documents\stable-diffusion-webui\webui-user.bat
STYLE_REFERENCE=$ASSETS_DIR/style_reference.png
TMP_DIR=$ASSETS_DIR/.tmp
TMP_RAW=$TMP_DIR/raw        # raw výstup ze SD
TMP_NOBG=$TMP_DIR/nobg      # po odstranění pozadí (a frame fill)
TMP_FINAL=$TMP_DIR/final    # po downscale na cílovou velikost
```

---

## MODELY — DOPORUČENÁ SESTAVA

### Aktuální sestava (méně ideální pro item ikony)
- Base: **SDXL 1.0**
- LoRA: `pixel-art-xl-v1.1` (váha 1.0)
- Problém: LoRA je biasovaná na celé zbraně, špatně generuje izolované malé objekty (náboje, předměty)

### Doporučená sestava pro item ikony (stáhnout ručně)

| Model | URL | Umístění | Poznámka |
|---|---|---|---|
| **Illustrious XL** (checkpoint) | [civitai.com/models/795765](https://civitai.com/models/795765) | `models/Stable-diffusion/` | Nový base model, lepší pro itemy |
| **Pixel Art Game UI Icons LoRA** | [civitai.com/models/2443581](https://civitai.com/models/2443581) | `models/Lora/` | Trénovaný přímo na herní inventory ikony |

### Po stažení — nové prompty pro item ikony
```
<lora:pixel-art-xl-v1.1:0.6>, <lora:pixel_art_game_ui_icons:0.8>, pixelarticon, cyberpunk, [SUBJEKT], ...
```
Trigger word: `pixelarticon` — přidat na začátek positive promptu.

Spustit SD s Illustrious XL jako base modelem (vybrat v UI nebo přidat `--ckpt` argument).

### Alternativa — Pixel Art Diffusion XL (full checkpoint, ~6.5 GB)
- [civitai.com/models/277680](https://civitai.com/models/277680)
- Nevyžaduje LoRA, konzistentní quality pro game sprity
- Umístit do `models/Stable-diffusion/`, vybrat jako base model

---

## SPUŠTĚNÍ STABLE DIFFUSION

Spusť SD přes `launch.py` přímo Python interpretem (bat soubory nefungují spolehlivě z bashe):

```bash
powershell.exe -NoProfile -Command "Start-Process -FilePath 'C:\Users\karel\AppData\Local\Programs\Python\Python310\python.exe' -ArgumentList 'launch.py --no-half-vae --api' -WorkingDirectory 'C:\Users\karel\Documents\stable-diffusion-webui' -WindowStyle Normal"
```

SD se načítá pomalu (~3–5 min, při prvním spuštění instaluje PyTorch 2.5 GB). Čekej na port 7860:

```bash
# Běží Python?
tasklist 2>&1 | grep python

# Naslouchá server?
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:7860/

# Nebo check skript (z adresáře dungeoneer/):
python scripts/sd_generate.py --check --prompt x --output nul
```

SD musí běžet před jakýmkoliv generováním.

---

## JEDNOTNÝ VIZUÁLNÍ STYL PROJEKTU

Tento styl byl odvozen z existujících schválených assetů (weapon_pistol, weapon_shotgun, weapon_rifle, weapon_smg, weapon_combat_knife, weapon_energy_sword). **Každý nový asset musí odpovídat těmto pravidlům.**

### Paleta

| Role | Barva | Poznámka |
|---|---|---|
| Tělo objektu | Tmavý teal `#1a3535` – `#1f4040` | Dominantní plocha — ne šedá, ne černá |
| Highlight / hrana | Bright cyan `#00d4d4` – `#00e8e8` | Světlá linka na exponované hraně |
| Outline / stín | Velmi tmavý teal `#0d1f1f` – `#111` | Pixel outline, ne čistá černá |
| Accent (volitelný) | Bright cyan / neon teal | Vnitřní detail, trigger, scope lens |

- Maximálně **3 barvy** + průhlednost — každá plocha je jednobarevná (pixel art, žádný gradient)
- **Bez teplých barev** (žádná oranžová, červená, žlutá) — výjimka: krev/výbuchy v herním kontextu, ne ikony
- Energetické / futuristické zbraně (energy_sword) mohou mít tělo i highlight v podobném jasném cyan tónu → víc "glow" efekt

### Tvar a čitelnost

- **Silueta** okamžitě čitelná na 32×32 px — minimum detailů, žádné složité výřezy
- **Hard pixel edges** — nulový anti-aliasing, ostré přechody barev
- **Orientace item ikon**: vždy 45° diagonálně `/` — špička / hlaveň vpravo nahoře, rukojeť / základna vlevo dole (PCA post-processing)
- **Edge-to-edge pokrytí** — 1–2px padding, žádné velké prázdné okraje

### Referenční assety (k vizuální inspekci)

```
dungeoneer/assets/items/weapon_pistol.png       ← pistole, základní tvar
dungeoneer/assets/items/weapon_rifle.png        ← dlouhá zbraň, úzký profil
dungeoneer/assets/items/weapon_shotgun.png      ← krátká tlustá hlaveň
dungeoneer/assets/items/weapon_smg.png          ← kompaktní tělo
dungeoneer/assets/items/weapon_combat_knife.png  ← čepel, minimalistická silueta
dungeoneer/assets/items/weapon_energy_sword.png ← glow varianta (uniformně bright)
```

### Checklist konzistence stylu (použij při inspekci nového assetu)

- [ ] Dominantní barva je tmavý teal (ne šedá, ne modrá, ne zelená)
- [ ] Highlight je bright cyan podél exponované hrany
- [ ] Max 3 barvy celkem
- [ ] Orientace 45° (platí pro item ikony)
- [ ] Silueta odpovídá objektu na 32px
- [ ] Žádné teplé barvy

---

## A. Rozhodni, jaký asset generuješ

Před generováním urči typ assetu a sděl uživateli, co jsi zvolil a proč.

| Typ assetu | Příklady | Cílová velikost | Generovat na | Průhlednost | Cílový subdir |
|---|---|---|---|---|---|
| Sprite entita | nepřítel, hráč, NPC | 32×32 | 512×512 | ✅ ano | `assets/entities/` |
| UI ikona | tlačítko nápovědy, nastavení, skill | 64×64 | 512×512 | ✅ ano | `assets/ui/` |
| Item ikona | zbraň, předmět, vybavení v inventáři/na mapě | 32×32 | 1024×1024 | ✅ ano | `assets/items/` |
| Portrét / větší ilustrace | hrdina v inventáři, boss | dle zadání | 1024×1024 | dle kontextu | `assets/portraits/` |
| Prostředí / tileset | podlaha, zeď, rozvržení místnosti | dle zadání | 1024×1024 | ❌ ne | `assets/tiles/` |

Pokud typ není jasný ze zadání, zeptej se uživatele.

---

## B. Sestav prompt

### Prompty pro sprity a ikony (s průhledností)
```
<lora:pixel-art-xl-v1.1:1.0>, cyberpunk, [SUBJEKT], game asset, black background, clean edges, [DOPLŇUJÍCÍ POPIS]
```
Negative prompt:
```
bad quality, blurry, text, watermark, signature, multiple objects, border, frame, noise, jpeg artifacts
```

### Prompty pro item ikony (zbraně, předměty)

Item ikony vyžadují speciální přístup:
- LoRA generuje UI panely a scan-lines → `solid white background` + rozšířený negative prompt
- SD nedokáže spolehlivě vynutit orientaci ani pokrytí → řeší post-processing (PCA rotace + frame fill)
- img2img reference nefunguje (příliš silný shape bias) → **vždy txt2img**

**Referenční styl** (analýza `sources/Free-Melee-Weapon-Pixel-Icons-for-Cyberpunk` + `sources/Free-Guns-Icon-32x32-Pixel-Pack`):
- **Orientace**: vždy 45° diagonálně `/` — zajišťuje post-processing, NE prompt
- **Pokrytí**: edge to edge, max 1–2px padding — zajišťuje post-processing
- **Paleta**: 2–3 barvy — tmavé tělo + světlý highlight na hraně + neon accent
- **Pixel art**: hard edges, žádný anti-aliasing, čisté barevné plochy
- **Silueta**: jednoduchá, okamžitě čitelná — minimum detailů

**Positive prompt** (nechej SD generovat v přirozené orientaci):
```
<lora:pixel-art-xl-v1.1:1.0>, cyberpunk, [ZBRAŇ/PŘEDMĚT], game weapon icon, single object, bold clean silhouette, hard pixel edges, limited color palette, highlight along edge, dark pixel outline, solid white background, isolated object, no background elements, cyan neon accent, dark body
```

**Negative prompt:**
```
bad quality, blurry, text, watermark, signature, border, frame, noise, jpeg artifacts, hands, person, humanoid, grid, spritesheet, multiple panels, duplicate, two, pair, trio, comparison, variations, realistic, 3d render, photo, multiple objects, ui panel, interface, hud, rounded corners, scanlines, drop shadow, cast shadow, shadow on ground, background elements, floor, surface, vignette, anti-aliasing, smooth edges, soft edges, detailed texture, gradient background
```

**Rozlišení**: `"width": 1024, "height": 1024` — SDXL optimum.

> ⚠️ Pokud SD vygeneruje více objektů → VŽDY regenerovat, NIKDY neořezávat.

### POSTUP VÝROBY MUNIČNÍCH IKON (ověřený workflow)

Muniční ikony nelze spolehlivě generovat samotným SD — LoRA je příliš biasovaná na celé zbraně a na 32px jsou tvarové rozdíly mezi typy nábojů nerozlišitelné. Ověřený postup:

#### Krok 1 — Vygeneruj základní náboj (img2img od dobrého výsledku)

Reprodukovatelný základ: seed `3947922114`, prompt viz sekci níže.

```bash
python scripts/sd_generate.py \
  --prompt "<lora:pixel-art-xl-v1.1:1.0>, cyberpunk, 9mm pistol bullet cartridge, side view profile, elongated oval silhouette, blunt rounded tip, cylindrical body, game item icon, single object, bold clean silhouette, hard pixel edges, limited color palette, highlight along edge, dark pixel outline, solid white background, isolated object, brass amber colored body, dark gunmetal bullet tip, subtle cyan highlight" \
  --negative "bad quality, blurry, text, watermark, border, noise, jpeg artifacts, humanoid, spritesheet, pattern, multiple, duplicate, gun, weapon, firearm, realistic, 3d render, photo, hud, scanlines, drop shadow, shadow, background, floor, vignette, anti-aliasing, gradient, front view, top view, isometric" \
  --seed 3947922114 \
  --output $TMP_RAW/ammo_base.png \
  --width 1024 --height 1024
```

Pro varianty (různé délky) použij img2img z tohoto base s `--denoising 0.45–0.7`.

#### Krok 2 — Post-processing

```bash
python scripts/asset_postprocess.py $TMP_RAW/ammo_base.png $TMP_FINAL/ammo_base.png --padding 2
```

#### Krok 3 — Přebarvení hrotu (`scripts/ammo_recolor.py`)

Primární diferenciátor mezi typy munice = barva hrotu. Tělo (tmavé pouzdro + cyan pruh) zůstává stejné.

```bash
# 9mm = amber (standard, žádná změna)
cp ammo_base.png ammo_ammo_9mm.png

# rifle = zelený hrot (hue 120°)
python scripts/ammo_recolor.py $TMP_FINAL/ammo_base.png $TMP_FINAL/ammo_ammo_rifle.png 120

# shell = červený hrot (hue 0°)
python scripts/ammo_recolor.py $TMP_FINAL/ammo_base.png $TMP_FINAL/ammo_ammo_shell.png 0
```

**Hue referenční tabulka:**
| Typ munice | Hue | Barva hrotu | Soubor |
|---|---|---|---|
| 9mm (standard) | 40 (výchozí) | amber/gold | `ammo_ammo_9mm.png` |
| rifle | 120 | zelená | `ammo_ammo_rifle.png` |
| shell | 0 | červená | `ammo_ammo_shell.png` |
| nový typ | dle výběru | dle výběru | `ammo_ammo_{id}.png` |

#### Krok 4 — Složené ikony (Python, bez SD)

Pro ikony representující více nábojů (random ammo atd.) skládej v Pythonu pomocí PIL:

```python
from PIL import Image
import colorsys

# Zkřížené náboje (random ammo) — flip + alpha_composite
base = Image.open("ammo_ammo_9mm.png").convert("RGBA")
back = base.copy()
# přebarvi hrot back náboje (volitelně)
back = back.transpose(Image.FLIP_LEFT_RIGHT)   # "\" tvar
canvas = Image.new("RGBA", base.size, (0,0,0,0))
canvas.alpha_composite(back)   # za
canvas.alpha_composite(base)   # před
canvas.save("ammo_ammo_random.png")
```

**Pravidlo:** ikony složené z více nábojů dělej vždy v Pythonu, ne v SD — SD z více objektů generuje spritesheet nebo chaos.

---

### Poznatky z generování munice (praktické tipy)

**Přístup**: stejný pipeline jako zbraně (txt2img → rembg → PCA 45° → 32×32).

**Paleta**: shodná s weapons — dark teal tělo, bright cyan highlight. Žádné brass/amber akcenty (i když reálná munice má mosazné pouzdro — v tomto stylu to nerušíme, viz design decision níže).

**Primární diferenciátor = tvar siluety** (viz referenci Nuclear Throne), ne barva:
- `9mm` → střední zakulacená kulka, tupý hrot → `rounded bullet, blunt tip, medium sized, compact`
- `rifle` → dlouhá štíhlá patrona, špičatý hrot → `long slender rifle cartridge, pointed tip, narrow elongated`
- `shell` → krátký tlustý válec → `short wide shotgun shell, cylindrical, stubby, brass hull`

**Design decision** (2026-03-28): Munice má jednotnou teal/cyan paletu jako zbraně. Brass/amber accent zvažován, zamítnut — weapon sprites nemají žádné teplé tóny, konzistence je důležitější než realismus.

**Prompty pro munici:**

9mm:
```
<lora:pixel-art-xl-v1.1:1.0>, cyberpunk, 9mm pistol bullet cartridge, rounded blunt tip, compact small round, game item icon, single object, bold clean silhouette, hard pixel edges, limited color palette, highlight along edge, dark pixel outline, solid white background, isolated object, no background elements, cyan neon accent, dark teal body
```

Rifle:
```
<lora:pixel-art-xl-v1.1:1.0>, cyberpunk, rifle cartridge ammunition, long slender elongated, sharp pointed tip, bottleneck shape, game item icon, single object, bold clean silhouette, hard pixel edges, limited color palette, highlight along edge, dark pixel outline, solid white background, isolated object, no background elements, cyan neon accent, dark teal body
```

Shell:
```
<lora:pixel-art-xl-v1.1:1.0>, cyberpunk, shotgun shell, short wide cylindrical hull, stubby barrel shape, game item icon, single object, bold clean silhouette, hard pixel edges, limited color palette, highlight along edge, dark pixel outline, solid white background, isolated object, no background elements, cyan neon accent, dark teal body
```

**Cílové názvy souborů** (konvence `{itemtype}_{id}.png`):
- `ammo_ammo_9mm.png`
- `ammo_ammo_rifle.png`
- `ammo_ammo_shell.png`

---

### Poznatky z generování zbraní (praktické tipy)

**Co funguje:**
- Krátký, jednoduchý popis zbraně (1–3 klíčové rysy): `pistol handgun, short barrel, trigger guard`
- `single object` v positive + `two, pair, multiple` v negative — pomáhá, ale negarantuje single output
- `solid white background` — rembg pak funguje spolehlivě
- `dark body` / `dark steel body` — zajistí tmavý základ s cyan akcenty, ne celou zbraň cyan
- Pro moc svítící výsledky: přidat `bright, glowing, neon, colorful` do negative, `mostly dark gunmetal grey body, subtle cyan accent line` do positive
- `game weapon icon, bold clean silhouette` — konzistentní styl napříč zbraněmi

**Co nefunguje:**
- `diagonal 45 degrees, tip pointing upper right` — SD orientaci v promptu ignoruje, řešit PCA rotací v post-processingu
- `filling the frame edge to edge` — SD ignoruje, řešit frame fill v post-processingu
- `pixel art icon` — koliduje s LoRA (LoRA se aktivuje vahou, slova "pixel art" zhoršují výsledek)
- Příliš mnoho deskriptorů (dvě scope, pump grip, wooden stock, wide bore...) → přeplácnutý výsledek, raději méně slov
- `submachine gun SMG, compact body, side magazine, foregrip` — příliš detailní popis vytváří L-tvary, které PCA rotace nezvládá
- img2img se style referencí pro zbraně — přenáší shape bias, všechny zbraně pak vypadají jako reference

**Problémové zbraně (generují duplikáty častěji):**
- Nůž: `single` + `one knife only` + `pair, multiple knives` v negative; často potřebuje 2–3 pokusy
- SMG: náchylné na spritesheet; `one single` v positive pomáhá; cfg_scale nechat na 8

**Post-processing rozhodnutí (vyžaduje vizuální inspekci):**
- `--flip`: použít pokud zbraň v raw míří doleva; mirror PŘED PCA rotací
- Bez flipu: pokud míří doprava nebo nahoru
- PCA nefunguje dobře na L-tvary (SMG s gripem dolů) — preferovat generování s kompaktnějším tvarem

---

### Prompty pro prostředí a místnosti
```
<lora:pixel-art-xl-v1.1:0.8>, <lora:Stylized_Setting_SDXL:0.9>, Isometric_Setting, cyberpunk, [SUBJEKT], top-down view, dark atmosphere, neon lighting, [DOPLŇUJÍCÍ POPIS]
```
Negative prompt:
```
bad quality, blurry, text, watermark, characters, enemies, people
```

### Tipy pro cyberpunk styl
- Přidej: `neon lights, dark background, metallic surfaces, glowing circuits`
- Barvy: `cyan, magenta, purple, electric blue, orange neon`
- Vyhni se: `realistic photo, 3D render` — narušují pixel art styl

> ⚠️ Nepřidávej do promptu slova "pixel art" ani "pixelated" — LoRA pixel-art-xl se aktivuje vahou, přidání slov výsledek zhorší.

---

## C. Generování

Generování obstarává `scripts/sd_generate.py`. Nejdřív ověř, že SD běží:

```bash
python scripts/sd_generate.py --check
```

### txt2img (výchozí pro item ikony)

```bash
python scripts/sd_generate.py --prompt "ZDE_PROMPT" --negative "ZDE_NEGATIVE" --output $TMP_RAW/weapon.png
```

### img2img (pro entity sprity a animace — konzistence přes style referenci)

```bash
python scripts/sd_generate.py --mode img2img --reference $STYLE_REFERENCE --prompt "ZDE_PROMPT" --negative "ZDE_NEGATIVE" --output $TMP_RAW/sprite.png --denoising 0.5
```

`--denoising`: 0.3–0.4 = blízko referenci, 0.5–0.6 = rovnováha, 0.7+ = více změn.

> **Item ikony**: vždy `txt2img` — img2img přenáší shape bias z reference a zbraně pak vypadají jako reference.
> **Sprity/entity**: img2img se style referencí funguje lépe (konzistentní proporce postav).

### Další volby

| Flag | Default | Popis |
|---|---|---|
| `--width`, `--height` | 1024 | Rozlišení generování |
| `--steps` | 30 | Sampling steps |
| `--cfg-scale` | 8 | CFG scale |
| `--seed` | -1 | Seed (-1 = náhodný) |
| `--sd-url` | http://127.0.0.1:7860 | URL SD WebUI instance |

---

## D. Animované sprite sheety

Přístup: img2img variace z base framu (4 framy celkem).

### Krok 1 — base frame
```bash
python scripts/sd_generate.py --prompt "ZDE_PROMPT, neutral stance" --negative "ZDE_NEGATIVE" --output $TMP_RAW/frame_0.png --width 512 --height 512
```

### Krok 2 — další framy (img2img variace)
```bash
python scripts/sd_generate.py --mode img2img --reference $TMP_RAW/frame_0.png --prompt "ZDE_PROMPT, slight lean left" --negative "ZDE_NEGATIVE" --output $TMP_RAW/frame_1.png --denoising 0.4 --width 512 --height 512
```

**Pohybové deskriptory:**

| Animace | Frame 0 | Frame 1 | Frame 2 | Frame 3 |
|---|---|---|---|---|
| idle | neutral stance | slight lean left | neutral stance | slight lean right |
| walk | left leg forward | neutral stride | right leg forward | neutral stride |
| death | standing upright | falling forward | collapsed halfway | lying flat |

> `--denoising` 0.35–0.4 pro 32×32 sprity — vyšší = více variace, ale riziko ztráty konzistence.

### Krok 3 — post-processing každého framu
```bash
python scripts/asset_postprocess.py $TMP_RAW/frame_0.png $TMP_FINAL/frame_0.png --skip-rotate
```

### Krok 4 — složi spritesheet
```bash
python -c "
from PIL import Image
from pathlib import Path
frames = sorted(Path('$TMP_FINAL').glob('frame_*.png'))
imgs = [Image.open(f).convert('RGBA') for f in frames]
W, H = imgs[0].size
sheet = Image.new('RGBA', (W * len(imgs), H), (0, 0, 0, 0))
for i, img in enumerate(imgs):
    sheet.paste(img, (i * W, 0))
sheet.save('$TMP_FINAL/spritesheet.png')
print(f'Spritesheet: {W * len(imgs)}x{H}, {len(imgs)} frames')
"
```

---

## E. Post-processing

Veškerá post-processing logika je ve skriptu `scripts/asset_postprocess.py`.

### Jeden soubor

```bash
python scripts/asset_postprocess.py $TMP_RAW/weapon.png $TMP_FINAL/weapon.png
```

Pipeline: rembg → PCA rotace na 45° → crop + frame fill → downscale 32×32 → validace.

### Batch (celá složka najednou)

```bash
python scripts/asset_postprocess.py $TMP_RAW $TMP_FINAL --batch
```

### Volby

| Flag | Default | Popis |
|---|---|---|
| `--target-size` | 32 | Cílová velikost v px |
| `--target-angle` | 45 | Cílový úhel PCA rotace (stupně) |
| `--padding` | 2 | Padding ve finálním pixel prostoru |
| `--skip-rembg` | false | Přeskočit odstranění pozadí (pro prostředí) |
| `--skip-rotate` | false | Přeskočit PCA rotaci (pro sprity/entity) |

### Příklady pro různé typy assetů

```bash
# Item ikony (plný pipeline)
python scripts/asset_postprocess.py raw/pistol.png final/pistol.png

# Sprity/entity (bez rotace)
python scripts/asset_postprocess.py raw/enemy.png final/enemy.png --skip-rotate

# Prostředí (bez rembg ani rotace, jiná velikost)
python scripts/asset_postprocess.py raw/floor.png final/floor.png --skip-rembg --skip-rotate --target-size 128
```

> Skript vrátí exit code 1 pokud validace selže → regeneruj, neopravuj ručně.

---

## F. Zkontroluj výsledek

Přečti výsledný obrázek Read toolem a projdi checklist pro daný typ assetu.

### Obecný checklist (všechny typy)
- **Čitelnost**: je subjekt rozpoznatelný ve finální velikosti?
- **Průhlednost**: je pozadí čistě odstraněné bez artefaktů?
- **Styl**: odpovídá cyberpunk pixel art estetice?
- **Konzistence**: pokud existuje style reference, odpovídá jí palette a styl?

### Checklist pro item ikony (zbraně, předměty)
- **Silueta**: odpovídá tvar zadanému typu zbraně? (nůž vypadá jako nůž, brokovnice jako brokovnice)
- **Orientace**: špička/hlaveň vpravo nahoře, rukojeť/pažba vlevo dole (45° `/`) — zajišťuje E3
- **Pokrytí**: objekt vyplňuje celý rámec od kraje ke kraji — zajišťuje E4
- **Jediný objekt**: žádné duplikáty — kontroluje E6
- **Styl sady**: odpovídá paletě ostatních ikon (cyan accent, dark body)

### Checklist pro spritesheets (animace)
- Jsou framy konzistentní — tvar, palette, kontura postavy?

**Pokud nevyhovuje** (max 3 pokusy automaticky, pak se zeptej uživatele):
- Špatný typ objektu → uprav prompt, buď specifičtější v popisu tvaru
- Více objektů → regeneruj (nikdy neořezávej)
- Artefakty, šum → zvyš `steps` na 35, přidej do negative promptu
- Pozadí baked-in → přidej do negative, zkontroluj `solid white background`
- Nesedí styl → zjednodušit prompt (méně deskriptorů = konzistentnější výstup)

---

## G. Ulož schválený asset

Po schválení uživatelem zkopíruj z `$TMP_FINAL/` do správného subadresáře:

```bash
cp $TMP_FINAL/weapon_pistol.png   $ASSETS_DIR/items/weapon_pistol.png
cp $TMP_FINAL/enemy_drone.png     $ASSETS_DIR/entities/enemy_drone.png
cp $TMP_FINAL/btn_help.png        $ASSETS_DIR/ui/btn_help.png
```

Pojmenování: lowercase, bez mezer, výstižné (`weapon_pistol.png`, `enemy_drone.png`).

**Povinná konvence pro item ikony** (`assets/items/`): název souboru musí být `{itemtype}_{id}.png`, kde:
- `itemtype` = `item.item_type.name.lower()` → `weapon`, `consumable`, `armor`, `ammo`
- `id` = `item.id` z kódu (např. `combat_knife`, `energy_sword`, `smg`, `basic_armor`)

Příklady: `weapon_pistol.png`, `weapon_combat_knife.png`, `consumable_stimpack.png`, `armor_basic_armor.png`.

Kód načítá ikony přímo podle tohoto vzoru bez mapovací tabulky — odlišný název = ikona se nezobrazí.

> **Seed** pro reprodukovatelnost: `sd_generate.py` vypisuje seed při každém generování. Zapiš ho do poznámky u assetu.
