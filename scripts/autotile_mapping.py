"""
Pixel-match all 48 autotile positions against the main tileset.
Produces a complete mapping table with neighbor analysis.
"""

from PIL import Image
import numpy as np

BASE = r"c:\Users\karel\Documents\Python\Dungeoneer\dungeoneer\sources\Ditharts_Free_Scifi_Tileset_v01\texture"

AUTOTILE_PATH   = BASE + r"\godot_template\godot_minimal_3x3_autotile.png"
TEMPLATE_PATH   = BASE + r"\godot_template\godot_minimal_3x3_autotile_template.png"
TILESET_PATH    = BASE + r"\tileset_for_free.png"

TILE_W, TILE_H  = 32, 32
AUTOTILE_COLS   = 12
AUTOTILE_ROWS   = 4
TILESET_COLS    = 8
TILESET_ROWS    = 15

# Sub-zone labels in reading order (NW, N, NE, W, C, E, SW, S, SE)
ZONE_NAMES = ["NW", "N", "NE", "W", "C", "E", "SW", "S", "SE"]

# Pink (wall) reference colour in the template  — approximately (255, 0, 255) or similar magenta
# We'll classify by checking whether R+B >> G (pink/magenta) vs G+B >> R (white / near-white)

def classify_pixel_wall(r, g, b):
    """Return True if pixel is pink/magenta (wall), False if white/floor."""
    # Pink: high R, low G, high B
    # White: high R, high G, high B
    return (r > 100) and (b > 100) and (g < 100)

def analyse_template_zone(template_arr, tile_col, tile_row):
    """
    For a 32×32 template tile, divide into 3×3 sub-zones (~10×10 each).
    For each zone check the center 6×6 area and classify wall vs floor.
    Returns list of 9 strings: "W" or "F" in order NW,N,NE,W,C,E,SW,S,SE.
    """
    x0 = tile_col * TILE_W
    y0 = tile_row * TILE_H

    zone_size = TILE_W // 3   # 10 pixels (with a couple leftover)
    center_pad = 2             # sample inner 6×6 of each zone

    results = []
    for zy in range(3):
        for zx in range(3):
            zx0 = x0 + zx * zone_size + center_pad
            zy0 = y0 + zy * zone_size + center_pad
            zx1 = x0 + (zx + 1) * zone_size - center_pad
            zy1 = y0 + (zy + 1) * zone_size - center_pad
            region = template_arr[zy0:zy1, zx0:zx1]  # shape (h, w, 4) or (h, w, 3)
            wall_count = 0
            floor_count = 0
            for py in range(region.shape[0]):
                for px in range(region.shape[1]):
                    pix = region[py, px]
                    r, g, b = int(pix[0]), int(pix[1]), int(pix[2])
                    if classify_pixel_wall(r, g, b):
                        wall_count += 1
                    else:
                        floor_count += 1
            results.append("W" if wall_count >= floor_count else "F")
    return results

def get_tile_pixels(img_arr, col, row):
    """Extract 32×32 tile as numpy array."""
    x0 = col * TILE_W
    y0 = row * TILE_H
    return img_arr[y0:y0 + TILE_H, x0:x0 + TILE_W]

def pixel_match(tile_a, tile_b):
    """
    Mean absolute difference using only pixels where BOTH tiles have alpha > 10.
    If no overlapping opaque pixels, return 999.
    """
    # Handle images with or without alpha channel
    if tile_a.shape[2] == 4:
        mask_a = tile_a[:, :, 3] > 10
    else:
        mask_a = np.ones((TILE_H, TILE_W), dtype=bool)

    if tile_b.shape[2] == 4:
        mask_b = tile_b[:, :, 3] > 10
    else:
        mask_b = np.ones((TILE_H, TILE_W), dtype=bool)

    mask = mask_a & mask_b
    n = mask.sum()
    if n == 0:
        return 999.0

    rgb_a = tile_a[:, :, :3].astype(float)
    rgb_b = tile_b[:, :, :3].astype(float)
    diff = np.abs(rgb_a - rgb_b)[mask]
    return diff.mean()

def main():
    autotile_img  = Image.open(AUTOTILE_PATH).convert("RGBA")
    template_img  = Image.open(TEMPLATE_PATH).convert("RGBA")
    tileset_img   = Image.open(TILESET_PATH).convert("RGBA")

    autotile_arr  = np.array(autotile_img)
    template_arr  = np.array(template_img)
    tileset_arr   = np.array(tileset_img)

    # Pre-extract all tileset tiles
    tileset_tiles = []
    for tr in range(TILESET_ROWS):
        for tc in range(TILESET_COLS):
            tileset_tiles.append(get_tile_pixels(tileset_arr, tc, tr))

    results = []

    for ar in range(AUTOTILE_ROWS):
        for ac in range(AUTOTILE_COLS):
            # 1. Get autotile tile
            auto_tile = get_tile_pixels(autotile_arr, ac, ar)

            # 2. Analyse template
            zones = analyse_template_zone(template_arr, ac, ar)
            neighbor_parts = [f"{ZONE_NAMES[i]}={zones[i]}" for i in range(9)]
            neighbor_str = " ".join(neighbor_parts)

            # 3. Pixel-match against all tileset tiles
            best_idx  = -1
            best_diff = 999.0
            for idx, ts_tile in enumerate(tileset_tiles):
                d = pixel_match(auto_tile, ts_tile)
                if d < best_diff:
                    best_diff = d
                    best_idx  = idx

            results.append((ar, ac, neighbor_str, best_idx, best_diff))

    print(f"{'autotile_col':>12} {'autotile_row':>12} | {'neighbors':<55} | best_match_index  diff")
    print("-" * 110)
    for ar, ac, neighbor_str, best_idx, best_diff in results:
        print(f"autotile_col={ac:>2} autotile_row={ar} | neighbors={neighbor_str} | best_match_index={best_idx:>3}  diff={best_diff:.1f}")

if __name__ == "__main__":
    main()
