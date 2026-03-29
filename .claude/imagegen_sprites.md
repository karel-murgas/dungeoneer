# Animované sprite sheety — Dungeoneer

Přečíst když: generuješ animovaný sprite (idle, walk, death, ...).

Přístup: img2img variace z base framu (4 framy celkem).

---

## Krok 1 — base frame

```bash
python scripts/sd_generate.py \
  --prompt "ZDE_PROMPT, neutral stance" \
  --negative "ZDE_NEGATIVE" \
  --output $TMP_RAW/frame_0.png \
  --width 512 --height 512
```

## Krok 2 — další framy (img2img variace)

```bash
python scripts/sd_generate.py \
  --mode img2img \
  --reference $TMP_RAW/frame_0.png \
  --prompt "ZDE_PROMPT, slight lean left" \
  --negative "ZDE_NEGATIVE" \
  --output $TMP_RAW/frame_1.png \
  --denoising 0.4 \
  --width 512 --height 512
```

`--denoising` 0.35–0.4 pro 32×32 sprity — vyšší = více variace, riziko ztráty konzistence.

**Pohybové deskriptory:**

| Animace | Frame 0 | Frame 1 | Frame 2 | Frame 3 |
|---|---|---|---|---|
| idle | neutral stance | slight lean left | neutral stance | slight lean right |
| walk | left leg forward | neutral stride | right leg forward | neutral stride |
| death | standing upright | falling forward | collapsed halfway | lying flat |

## Krok 3 — post-processing každého framu

```bash
python scripts/asset_postprocess.py $TMP_RAW/frame_0.png $TMP_FINAL/frame_0.png --skip-rotate
```

## Krok 4 — složení spritesheetu

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

## Checklist

- Jsou framy konzistentní — tvar, palette, kontura postavy?
- Animace vypadá přirozeně při 4 fps?