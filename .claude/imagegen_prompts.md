# Prompty pro assety — Dungeoneer

Přečíst když: sestavuješ prompt pro konkrétní typ assetu.

> ⚠️ Nepřidávej do promptu slova "pixel art" ani "pixelated" — LoRA `pixel-art-xl-v1.1` se aktivuje vahou, přidání slov výsledek zhorší.

---

## Sprity a entity (s průhledností)

```
<lora:pixel-art-xl-v1.1:1.0>, cyberpunk, [SUBJEKT], game asset, black background, clean edges, [DOPLŇUJÍCÍ POPIS]
```
Negative:
```
bad quality, blurry, text, watermark, signature, multiple objects, border, frame, noise, jpeg artifacts
```

---

## Item ikony — zbraně a předměty

Item ikony vyžadují speciální přístup:
- LoRA generuje UI panely a scan-lines → `solid white background` + rozšířený negative
- SD nedokáže vynutit orientaci ani pokrytí → řeší post-processing (PCA 45° + frame fill)
- img2img nefunguje (shape bias) → **vždy txt2img**

**Positive:**
```
<lora:pixel-art-xl-v1.1:1.0>, cyberpunk, [ZBRAŇ/PŘEDMĚT], game weapon icon, single object, bold clean silhouette, hard pixel edges, limited color palette, highlight along edge, dark pixel outline, solid white background, isolated object, no background elements, cyan neon accent, dark body
```

**Negative:**
```
bad quality, blurry, text, watermark, signature, border, frame, noise, jpeg artifacts, hands, person, humanoid, grid, spritesheet, multiple panels, duplicate, two, pair, trio, comparison, variations, realistic, 3d render, photo, multiple objects, ui panel, interface, hud, rounded corners, scanlines, drop shadow, cast shadow, shadow on ground, background elements, floor, surface, vignette, anti-aliasing, smooth edges, soft edges, detailed texture, gradient background
```

**Rozlišení**: `--width 1024 --height 1024` — SDXL optimum.

> ⚠️ SD vygeneruje více objektů → VŽDY regenerovat, NIKDY neořezávat.

---

## Tipy pro generování zbraní

**Co funguje:**
- Krátký popis (1–3 rysy): `pistol handgun, short barrel, trigger guard`
- `single object` v positive + `two, pair, multiple` v negative
- `solid white background` — rembg pak funguje spolehlivě
- `dark body` / `dark steel body` — zajistí tmavý základ s cyan akcenty
- Moc svítící: přidat `bright, glowing, neon, colorful` do negative, `mostly dark gunmetal grey body, subtle cyan accent line` do positive
- `game weapon icon, bold clean silhouette`

**Co nefunguje:**
- `diagonal 45 degrees, tip pointing upper right` — SD ignoruje, řeší PCA post-processing
- `filling the frame edge to edge` — SD ignoruje, řeší frame fill post-processing
- `pixel art icon` — koliduje s LoRA
- Příliš mnoho deskriptorů → přeplácnutý výsledek
- img2img se style referencí — přenáší shape bias

**Problémové zbraně:**
- Nůž: `single` + `one knife only` + `pair, multiple knives` v negative; 2–3 pokusy
- SMG: `one single` v positive; cfg_scale 8; náchylné na spritesheet

**`--flip` v post-processingu:**
- Použít pokud zbraň v raw míří doleva (mirror PŘED PCA rotací)
- Bez flipu: míří doprava nebo nahoru

---

## Prostředí a místnosti

```
<lora:pixel-art-xl-v1.1:0.8>, <lora:Stylized_Setting_SDXL:0.9>, Isometric_Setting, cyberpunk, [SUBJEKT], top-down view, dark atmosphere, neon lighting, [DOPLŇUJÍCÍ POPIS]
```
Negative:
```
bad quality, blurry, text, watermark, characters, enemies, people
```

Cyberpunk tipy: `neon lights, dark background, metallic surfaces, glowing circuits` / barvy `cyan, magenta, purple, electric blue`

Muniční ikony → [imagegen_ammo.md](.claude/imagegen_ammo.md)
