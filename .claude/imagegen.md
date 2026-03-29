# Generování assetů — Cyberpunk Roguelite

Tyto instrukce používej vždy, když máš vygenerovat herní asset.
Podrobnosti jsou v separátních souborech — načti je jen když je potřebuješ.

| Potřebuješ | Přečti |
|---|---|
| Vizuální styl, paletu, modely | [imagegen_style.md](.claude/imagegen_style.md) |
| Prompty pro konkrétní typy assetů | [imagegen_prompts.md](.claude/imagegen_prompts.md) |
| Muniční ikony (ammo workflow) | [imagegen_ammo.md](.claude/imagegen_ammo.md) |
| Animované spritesheety | [imagegen_sprites.md](.claude/imagegen_sprites.md) |

---

## KONFIGURACE

```
ASSETS_DIR=dungeoneer/assets
TMP_RAW=$ASSETS_DIR/.tmp/raw        # raw výstup ze SD
TMP_NOBG=$ASSETS_DIR/.tmp/nobg      # po odstranění pozadí
TMP_FINAL=$ASSETS_DIR/.tmp/final    # po downscale na cílovou velikost
STYLE_REFERENCE=$ASSETS_DIR/style_reference.png
```

---

## SPUŠTĚNÍ STABLE DIFFUSION

```bash
powershell.exe -NoProfile -Command "Start-Process -FilePath 'C:\Users\karel\AppData\Local\Programs\Python\Python310\python.exe' -ArgumentList 'launch.py --no-half-vae --api' -WorkingDirectory 'C:\Users\karel\Documents\stable-diffusion-webui' -WindowStyle Normal"
```

SD se načítá pomalu (~3–5 min). Ověř, že běží:

```bash
python scripts/sd_generate.py --check --prompt x --output nul
```

SD musí běžet před jakýmkoliv generováním.

---

## A. Rozhodni, jaký asset generuješ

Před generováním urči typ a sděl uživateli volbu.

| Typ assetu | Příklady | Cílová velikost | Generovat na | Průhlednost | Rotace 45° | Cílový subdir |
|---|---|---|---|---|---|---|
| Sprite entita | nepřítel, hráč, NPC | 32×32 | 512×512 | ✅ ano | ❌ `--skip-rotate` | `assets/entities/` |
| UI ikona | tlačítko, skill | 64×64 | 512×512 | ✅ ano | ❌ `--skip-rotate` | `assets/ui/` |
| Item ikona — podlouhlá | zbraně, nože, náboje | 32×32 | 1024×1024 | ✅ ano | ✅ PCA 45° | `assets/items/` |
| Item ikona — čtvercová | armor, granát | 32×32 | 1024×1024 | ✅ ano | ❌ `--skip-rotate` | `assets/items/` |
| Item ikona — PIL | credits_credits | 32×32 | PIL přímo | ✅ ano | ❌ | `assets/items/` |
| Portrét | hrdina, boss | dle zadání | 1024×1024 | dle kontextu | ❌ `--skip-rotate` | `assets/portraits/` |
| Prostředí | podlaha, zeď, tileset | dle zadání | 1024×1024 | ❌ ne | ❌ `--skip-rotate` | `assets/tiles/` |

Pokud typ není jasný, zeptej se uživatele.
Prompty pro každý typ → [imagegen_prompts.md](.claude/imagegen_prompts.md).

---

## B. Generování (`scripts/sd_generate.py`)

### txt2img (výchozí pro item ikony)
```bash
python scripts/sd_generate.py --prompt "ZDE_PROMPT" --negative "ZDE_NEGATIVE" --output $TMP_RAW/weapon.png
```

### img2img (pro entity sprity — konzistence přes style referenci)
```bash
python scripts/sd_generate.py --mode img2img --reference $STYLE_REFERENCE \
  --prompt "ZDE_PROMPT" --negative "ZDE_NEGATIVE" \
  --output $TMP_RAW/sprite.png --denoising 0.5
```
`--denoising`: 0.3–0.4 = blízko referenci, 0.5–0.6 = rovnováha, 0.7+ = více změn.

> **Item ikony**: vždy `txt2img` — img2img přenáší shape bias.
> **Sprity/entity**: img2img se style referencí (konzistentní proporce postav).

### Další volby
| Flag | Default | Popis |
|---|---|---|
| `--width`, `--height` | 1024 | Rozlišení generování |
| `--steps` | 30 | Sampling steps |
| `--cfg-scale` | 8 | CFG scale |
| `--seed` | -1 | Seed (-1 = náhodný) |

---

## C. Post-processing (`scripts/asset_postprocess.py`)

Pipeline: rembg → PCA rotace na 45° → crop + frame fill → downscale → validace.

```bash
# Jeden soubor
python scripts/asset_postprocess.py $TMP_RAW/weapon.png $TMP_FINAL/weapon.png

# Batch
python scripts/asset_postprocess.py $TMP_RAW $TMP_FINAL --batch

# Sprite/entita (bez rotace)
python scripts/asset_postprocess.py raw/enemy.png final/enemy.png --skip-rotate

# Prostředí (bez rembg ani rotace)
python scripts/asset_postprocess.py raw/floor.png final/floor.png --skip-rembg --skip-rotate --target-size 128
```

| Flag | Default | Popis |
|---|---|---|
| `--target-size` | 32 | Cílová velikost v px |
| `--padding` | 2 | Padding ve finálním pixel prostoru |
| `--skip-rembg` | false | Přeskočit odstranění pozadí |
| `--skip-rotate` | false | Přeskočit PCA rotaci |

> Skript vrátí exit code 1 pokud validace selže → regeneruj, neopravuj ručně.

---

## D. Zkontroluj výsledek

Přečti výsledný obrázek Read toolem.

**Obecný checklist:**
- Subjekt rozpoznatelný ve finální velikosti?
- Pozadí čistě odstraněné bez artefaktů?
- Odpovídá cyberpunk pixel art estetice?

**Item ikony navíc:**
- Správný typ objektu (nůž = nůž)?
- Orientace 45° `/` (hlaveň vpravo nahoře)?
- Jeden objekt (žádné duplikáty)?
- Paleta: tmavý teal tělo + cyan highlight?

**Pokud nevyhovuje** (max 3 pokusy automaticky, pak se zeptej):
- Špatný typ → uprav prompt, buď specifičtější
- Více objektů → regeneruj (nikdy neořezávej)
- Artefakty → zvyš `--steps` na 35, přidej do negative
- Nesedí styl → méně deskriptorů = konzistentnější výsledek

---

## E. Ulož schválený asset

Po schválení uživatelem zkopíruj z `$TMP_FINAL/` do správného subadresáře:

```bash
cp $TMP_FINAL/weapon_pistol.png   $ASSETS_DIR/items/weapon_pistol.png
cp $TMP_FINAL/enemy_drone.png     $ASSETS_DIR/entities/enemy_drone.png
cp $TMP_FINAL/btn_help.png        $ASSETS_DIR/ui/btn_help.png
```

**Konvence pro item ikony** (`assets/items/`): `{itemtype}_{id}.png`
- `itemtype` = `item.item_type.name.lower()` → `weapon`, `consumable`, `armor`, `ammo`
- `id` = `item.id` z kódu

Příklady: `weapon_pistol.png`, `consumable_stimpack.png`, `armor_basic_armor.png`.
Kód načítá ikony přímo podle vzoru — odlišný název = ikona se nezobrazí.

> **Seed** pro reprodukovatelnost: `sd_generate.py` vypisuje seed. Zapiš ho pro případ regenerace.