# Muniční ikony — workflow

Přečíst když: generuješ muniční ikony (`ammo_ammo_*.png`).

Muniční ikony nelze spolehlivě generovat samotným SD (LoRA biasovaná na celé zbraně, na 32px jsou tvarové rozdíly nerozlišitelné). Ověřený postup:

---

## Prompty

**Diferenciátor = tvar siluety** (ne barva):
- `9mm` → střední zakulacená kulka, tupý hrot
- `rifle` → dlouhá štíhlá patrona, špičatý hrot
- `shell` → krátký tlustý válec

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

---

## Krok 1 — Vygeneruj základní náboj

Reprodukovatelný základ: seed `3947922114`:

```bash
python scripts/sd_generate.py \
  --prompt "<lora:pixel-art-xl-v1.1:1.0>, cyberpunk, 9mm pistol bullet cartridge, side view profile, elongated oval silhouette, blunt rounded tip, cylindrical body, game item icon, single object, bold clean silhouette, hard pixel edges, limited color palette, highlight along edge, dark pixel outline, solid white background, isolated object, brass amber colored body, dark gunmetal bullet tip, subtle cyan highlight" \
  --negative "bad quality, blurry, text, watermark, border, noise, jpeg artifacts, humanoid, spritesheet, pattern, multiple, duplicate, gun, weapon, firearm, realistic, 3d render, photo, hud, scanlines, drop shadow, shadow, background, floor, vignette, anti-aliasing, gradient, front view, top view, isometric" \
  --seed 3947922114 \
  --output $TMP_RAW/ammo_base.png \
  --width 1024 --height 1024
```

Pro varianty (různé délky) použij img2img s `--denoising 0.45–0.7`.

## Krok 2 — Post-processing

```bash
python scripts/asset_postprocess.py $TMP_RAW/ammo_base.png $TMP_FINAL/ammo_base.png --padding 2
```

## Krok 3 — Přebarvení hrotu (`scripts/ammo_recolor.py`)

Primární diferenciátor = barva hrotu. Tělo zůstává stejné.

```bash
cp ammo_base.png ammo_ammo_9mm.png
python scripts/ammo_recolor.py $TMP_FINAL/ammo_base.png $TMP_FINAL/ammo_ammo_rifle.png 120
python scripts/ammo_recolor.py $TMP_FINAL/ammo_base.png $TMP_FINAL/ammo_ammo_shell.png 0
```

| Typ munice | Hue | Barva hrotu |
|---|---|---|
| 9mm | 40 (výchozí) | amber/gold |
| rifle | 120 | zelená |
| shell | 0 | červená |

## Krok 4 — Složené ikony (Python, bez SD)

```python
from PIL import Image

# Zkřížené náboje (random ammo) — flip + alpha_composite
base = Image.open("ammo_ammo_9mm.png").convert("RGBA")
back = base.copy().transpose(Image.FLIP_LEFT_RIGHT)  # "\" tvar
canvas = Image.new("RGBA", base.size, (0,0,0,0))
canvas.alpha_composite(back)   # za
canvas.alpha_composite(base)   # před
canvas.save("ammo_ammo_random.png")
```

Složené ikony vždy Python (PIL), ne SD — SD z více objektů generuje spritesheet nebo chaos.

**Cílové názvy:** `ammo_ammo_9mm.png`, `ammo_ammo_rifle.png`, `ammo_ammo_shell.png`

**Design decision (2026-03-28):** Munice má jednotnou teal/cyan paletu jako zbraně. Brass/amber accent zamítnut — weapon sprites nemají teplé tóny, konzistence > realismus.