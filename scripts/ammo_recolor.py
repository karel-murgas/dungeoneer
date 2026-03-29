"""
ammo_recolor.py — Recolor the amber/gold tip of a bullet icon to a target hue.

Usage:
    python scripts/ammo_recolor.py <src.png> <dst.png> <hue_degrees>

Hue reference (0–360):
    0   = red      (ammo_shell)
    40  = amber    (ammo_9mm, standard — no change needed)
    120 = green    (ammo_rifle)

The script identifies amber/gold pixels (hue 25–55°, saturation > 0.4, value > 0.3)
and rotates their hue to the target value, keeping saturation and brightness unchanged.
The dark casing and cyan stripe are untouched.

Example:
    python scripts/ammo_recolor.py assets/.tmp/raw/ammo_base.png \\
                                   assets/.tmp/raw/ammo_rifle.png 120
"""

import sys
import colorsys
from PIL import Image


def recolor_tip(src_path: str, dst_path: str, target_hue_deg: float) -> None:
    img = Image.open(src_path).convert("RGBA")
    pixels = img.load()
    w, h = img.size

    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a < 10:
                continue
            hv, sv, vv = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            hue_deg = hv * 360
            # amber/gold range: hue 25–55°, saturation > 0.4, value > 0.3
            if 25 <= hue_deg <= 55 and sv > 0.4 and vv > 0.3:
                new_h = target_hue_deg / 360
                nr, ng, nb = colorsys.hsv_to_rgb(new_h, sv, vv)
                pixels[x, y] = (int(nr * 255), int(ng * 255), int(nb * 255), a)

    img.save(dst_path)
    print(f"Saved: {dst_path}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    recolor_tip(sys.argv[1], sys.argv[2], float(sys.argv[3]))
