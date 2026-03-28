"""Post-processing pipeline for generated game assets.

Full pipeline for item icons:  rembg -> PCA rotate -> frame fill -> downscale -> validate
For sprites/entities:          rembg -> downscale -> validate
For environments:              downscale only
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ALPHA_THRESHOLD = 10


# ---------------------------------------------------------------------------
# G2: Background removal
# ---------------------------------------------------------------------------

def remove_background(img: Image.Image) -> Image.Image:
    from rembg import remove
    import io

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    result = remove(buf.getvalue())
    return Image.open(io.BytesIO(result)).convert("RGBA")


# ---------------------------------------------------------------------------
# G3: PCA auto-rotation to target angle
# ---------------------------------------------------------------------------

def pca_rotate(img: Image.Image, target_angle: float = 45, flip: bool = False) -> Image.Image:
    if flip:
        # Mirror horizontally BEFORE rotation — turns left-pointing into right-pointing
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
        print("  Mirrored horizontally (--flip)")

    arr = np.array(img)
    alpha = arr[:, :, 3]

    ys, xs = np.where(alpha > ALPHA_THRESHOLD)
    if len(xs) < 10:
        print("WARNING: too few visible pixels for PCA rotation")
        return img

    # PCA: find the principal axis
    coords = np.column_stack([xs - xs.mean(), ys - ys.mean()])
    cov = np.cov(coords.T)
    eigenvalues, eigenvectors = np.linalg.eigh(cov)
    main_axis = eigenvectors[:, np.argmax(eigenvalues)]
    current_angle = np.degrees(np.arctan2(-main_axis[1], main_axis[0])) % 180

    rotation = target_angle - current_angle
    rotated = img.rotate(rotation, resample=Image.BICUBIC, expand=True)

    print(f"  Rotated {rotation:.1f}deg (was {current_angle:.1f}deg -> target {target_angle}deg)")
    return rotated


# ---------------------------------------------------------------------------
# G4: Crop to bounding box + frame fill
# ---------------------------------------------------------------------------

def frame_fill(img: Image.Image, padding_px: int = 2, target_size: int = 32) -> Image.Image:
    arr = np.array(img)
    alpha = arr[:, :, 3]

    rows = np.any(alpha > ALPHA_THRESHOLD, axis=1)
    cols = np.any(alpha > ALPHA_THRESHOLD, axis=0)

    if not rows.any() or not cols.any():
        print("WARNING: image is fully transparent")
        return img

    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]

    cropped = img.crop((cmin, rmin, cmax + 1, rmax + 1))

    w, h = cropped.size
    content_size = max(w, h)
    # Convert padding from target pixel space to current pixel space
    pad = int(content_size * padding_px / (target_size - 2 * padding_px))
    canvas_size = content_size + 2 * pad

    square = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    square.paste(cropped, (pad + (content_size - w) // 2, pad + (content_size - h) // 2))

    print(f"  Frame fill: crop ({cmin},{rmin})–({cmax},{rmax}) -> {canvas_size}x{canvas_size}")
    return square


# ---------------------------------------------------------------------------
# G5: Downscale to target size
# ---------------------------------------------------------------------------

def downscale(img: Image.Image, target_size: int = 32) -> Image.Image:
    if target_size <= 64:
        mid = target_size * 4
        img = img.resize((mid, mid), Image.LANCZOS)
        img = img.resize((target_size, target_size), Image.NEAREST)
    else:
        img = img.resize((target_size, target_size), Image.LANCZOS)
    return img


# ---------------------------------------------------------------------------
# G6: Validation
# ---------------------------------------------------------------------------

def validate(img: Image.Image) -> list[str]:
    issues = []
    arr = np.array(img)
    alpha = arr[:, :, 3]

    # Coverage check
    coverage = (alpha > ALPHA_THRESHOLD).sum() / alpha.size
    if not (0.03 < coverage < 0.80):
        issues.append(f"Coverage out of range: {coverage:.1%}")

    # Corner transparency
    s = 3
    corners = [alpha[:s, :s], alpha[:s, -s:], alpha[-s:, :s], alpha[-s:, -s:]]
    for i, c in enumerate(corners):
        if c.mean() >= 30:
            issues.append(f"Corner {i} not transparent (mean={c.mean():.0f})")

    # Multi-object detection (vertical gap)
    rows_any = np.any(alpha > ALPHA_THRESHOLD, axis=1)
    if rows_any.any():
        filled = np.where(rows_any)[0]
        if len(filled) > 1:
            gaps = np.diff(filled)
            max_gap = gaps.max()
            span = filled[-1] - filled[0]
            if span > 0 and max_gap / span > 0.25:
                issues.append(f"Possible multiple objects (gap {max_gap}px in {span}px span)")

    print(f"  Validation: coverage={coverage:.1%}, issues={len(issues)}")
    return issues


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def process_item_icon(
    input_path: Path,
    output_path: Path,
    *,
    target_size: int = 32,
    target_angle: float = 45,
    padding_px: int = 2,
    skip_rembg: bool = False,
    skip_rotate: bool = False,
    flip: bool = False,
) -> list[str]:
    """Run the full item icon pipeline. Returns list of validation issues (empty = OK)."""
    print(f"Processing: {input_path.name}")

    img = Image.open(input_path).convert("RGBA")

    if not skip_rembg:
        img = remove_background(img)
        print(f"  Background removed")

    if not skip_rotate:
        img = pca_rotate(img, target_angle, flip=flip)

    img = frame_fill(img, padding_px=padding_px, target_size=target_size)
    img = downscale(img, target_size=target_size)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    print(f"  Saved: {output_path} ({img.size[0]}x{img.size[1]})")

    issues = validate(img)
    for issue in issues:
        print(f"  WARNING: {issue}")

    return issues


def main():
    p = argparse.ArgumentParser(description="Post-process generated game assets")
    p.add_argument("input", type=Path, help="Input image (raw SD output)")
    p.add_argument("output", type=Path, help="Output image (final)")
    p.add_argument("--target-size", type=int, default=32)
    p.add_argument("--target-angle", type=float, default=45, help="PCA rotation target angle")
    p.add_argument("--padding", type=int, default=2, help="Padding in target pixel space")
    p.add_argument("--skip-rembg", action="store_true")
    p.add_argument("--skip-rotate", action="store_true")
    p.add_argument("--flip", action="store_true", help="Rotate 180deg after PCA (fix wrong direction)")

    # Batch mode: process all PNGs in input directory
    p.add_argument("--batch", action="store_true", help="Process all PNGs in input dir -> output dir")

    args = p.parse_args()

    if args.batch:
        if not args.input.is_dir():
            p.error("--batch requires input to be a directory")
        args.output.mkdir(parents=True, exist_ok=True)
        files = sorted(args.input.glob("*.png"))
        all_issues = {}
        for f in files:
            out = args.output / f.name
            issues = process_item_icon(
                f, out,
                target_size=args.target_size, target_angle=args.target_angle,
                padding_px=args.padding, skip_rembg=args.skip_rembg,
                skip_rotate=args.skip_rotate, flip=args.flip,
            )
            if issues:
                all_issues[f.name] = issues

        print(f"\n{'='*40}")
        print(f"Processed {len(files)} files, {len(all_issues)} with issues")
        if all_issues:
            for name, issues in all_issues.items():
                print(f"  {name}: {', '.join(issues)}")
            sys.exit(1)
    else:
        issues = process_item_icon(
            args.input, args.output,
            target_size=args.target_size, target_angle=args.target_angle,
            padding_px=args.padding, skip_rembg=args.skip_rembg,
            skip_rotate=args.skip_rotate, flip=args.flip,
        )
        if issues:
            sys.exit(1)


if __name__ == "__main__":
    main()
