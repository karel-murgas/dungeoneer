"""
locker_tile_make.py — přebarví container_locker raw PNG na projektovou paletu
a vyexportuje 32×32 opaque tile pro vsazení do zdi.

Vstup:  dungeoneer/assets/.tmp/raw/container_locker_7788990.png
Výstup: dungeoneer/assets/.tmp/final/container_locker.png

Paleta projektu:
  shadow   #0d1f1f  (nejtemněší — obrys, stín)
  body     #1a3535  (dominantní plocha — teal)
  body2    #1f4040  (střední tón — vnitřní detail)
  edge     #2a5555  (světlejší tón těla)
  cyan     #00d4d4  (highlight hrana, aktivní prvky)
  screen   #00ff88  (zelená obrazovka — zachováme jako accent)
  dark_sym #0a2020  (symboly / vnitřní linka)
"""

from pathlib import Path
from PIL import Image
import colorsys
import sys

RAW = Path("dungeoneer/assets/.tmp/raw/container_locker_7788990.png")
OUT = Path("dungeoneer/assets/.tmp/final/container_locker.png")

# --- Cílové barvy projektu ---
C_SHADOW  = (0x0d, 0x1f, 0x1f)
C_BODY    = (0x1a, 0x35, 0x35)
C_BODY2   = (0x1f, 0x40, 0x40)
C_EDGE    = (0x2a, 0x55, 0x55)
C_CYAN    = (0x00, 0xd4, 0xd4)
C_SCREEN  = (0x00, 0xff, 0x88)   # zachovat green screen
C_DARK    = (0x0a, 0x20, 0x20)


def rgb_to_hsv(r, g, b):
    return colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)


def is_green_screen(r, g, b):
    """Rozpozná zelenou obrazovku — G dominantní, R a B výrazně nižší."""
    return g > 200 and g > r + 100 and g > b + 80


def remap_pixel(r, g, b):
    """Přemapuje pixel z originální světlé palety na tmavý teal."""

    # Zelená obrazovka — zachovat accent
    if is_green_screen(r, g, b):
        # Přebarvit na projektovou C_SCREEN (bright teal-green)
        lum = (r * 0.2126 + g * 0.7152 + b * 0.0722) / 255
        if lum > 0.7:
            return C_SCREEN
        return (0x00, 0xaa, 0x55)  # tmavší variant pro stíny obrazovky

    # Luminance
    lum = (r * 0.2126 + g * 0.7152 + b * 0.0722) / 255
    h, s, v = rgb_to_hsv(r, g, b)

    # Velmi tmavé pixely (obrysy, černé linie)
    if v < 0.20:
        return C_SHADOW

    # Tmavé — body (střední a tmavé šedé / modré)
    if v < 0.50:
        return C_BODY

    # Střední tóny — body2
    if v < 0.65:
        return C_BODY2

    # Světlejší hrany
    if v < 0.80:
        return C_EDGE

    # Velmi světlé → cyan highlight
    return C_CYAN


def process(raw_path: Path, out_path: Path, target: int = 32):
    img = Image.open(raw_path).convert("RGB")
    w, h = img.size

    # Crop na čtverec (center crop)
    side = min(w, h)
    left = (w - side) // 2
    top  = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))

    # Přebarvi pixel po pixelu
    out = Image.new("RGB", img.size)
    pixels_in  = img.load()
    pixels_out = out.load()

    for y in range(img.height):
        for x in range(img.width):
            r, g, b = pixels_in[x, y]
            pixels_out[x, y] = remap_pixel(r, g, b)

    # Downscale na 32×32 (nearest-neighbor pro pixel art)
    out = out.resize((target, target), Image.NEAREST)

    # Uložit jako RGBA (opaque) — plně vyplněný tile
    out_rgba = out.convert("RGBA")
    # Ujisti se, že alfa je plná (žádná průhlednost)
    r_ch, g_ch, b_ch, a_ch = out_rgba.split()
    import PIL.ImageChops as IC
    full_alpha = Image.new("L", out_rgba.size, 255)
    out_rgba = Image.merge("RGBA", (r_ch, g_ch, b_ch, full_alpha))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_rgba.save(out_path)
    print(f"Saved: {out_path}  ({target}x{target}, fully opaque)")


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else RAW
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT
    process(src, dst)
