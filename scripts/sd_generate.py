"""Generate images via Stable Diffusion WebUI API (txt2img / img2img)."""

import argparse
import base64
import json
import sys
import urllib.request
from pathlib import Path

DEFAULT_SD_URL = "http://127.0.0.1:7860"


def _post(url: str, payload: dict, timeout: int = 300) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def _save_image(result: dict, output: Path, index: int = 0) -> None:
    img_bytes = base64.b64decode(result["images"][index])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(img_bytes)


def _extract_seed(result: dict) -> int:
    info = json.loads(result["info"])
    return info["seed"]


def check_running(sd_url: str = DEFAULT_SD_URL) -> bool:
    try:
        req = urllib.request.Request(f"{sd_url}/sdapi/v1/options")
        urllib.request.urlopen(req, timeout=3)
        return True
    except Exception:
        return False


def txt2img(
    prompt: str,
    negative_prompt: str,
    output: Path,
    *,
    width: int = 1024,
    height: int = 1024,
    steps: int = 30,
    cfg_scale: float = 8,
    sampler: str = "DPM++ 2M Karras",
    seed: int = -1,
    sd_url: str = DEFAULT_SD_URL,
) -> dict:
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "steps": steps,
        "width": width,
        "height": height,
        "cfg_scale": cfg_scale,
        "sampler_name": sampler,
        "seed": seed,
    }
    result = _post(f"{sd_url}/sdapi/v1/txt2img", payload)
    _save_image(result, output)
    seed_used = _extract_seed(result)
    print(f"Saved: {output} (seed={seed_used})")
    return result


def img2img(
    prompt: str,
    negative_prompt: str,
    reference: Path,
    output: Path,
    *,
    denoising_strength: float = 0.5,
    width: int = 1024,
    height: int = 1024,
    steps: int = 30,
    cfg_scale: float = 8,
    sampler: str = "DPM++ 2M Karras",
    seed: int = -1,
    sd_url: str = DEFAULT_SD_URL,
) -> dict:
    ref_b64 = base64.b64encode(reference.read_bytes()).decode()
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "init_images": [ref_b64],
        "denoising_strength": denoising_strength,
        "steps": steps,
        "width": width,
        "height": height,
        "cfg_scale": cfg_scale,
        "sampler_name": sampler,
        "seed": seed,
    }
    result = _post(f"{sd_url}/sdapi/v1/img2img", payload)
    _save_image(result, output)
    seed_used = _extract_seed(result)
    print(f"Saved: {output} (seed={seed_used})")
    return result


def main():
    p = argparse.ArgumentParser(description="Generate image via SD WebUI API")
    p.add_argument("--mode", choices=["txt2img", "img2img"], default="txt2img")
    p.add_argument("--prompt", required=True)
    p.add_argument("--negative", default="")
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--reference", type=Path, help="Reference image for img2img")
    p.add_argument("--width", type=int, default=1024)
    p.add_argument("--height", type=int, default=1024)
    p.add_argument("--steps", type=int, default=30)
    p.add_argument("--cfg-scale", type=float, default=8)
    p.add_argument("--denoising", type=float, default=0.5)
    p.add_argument("--seed", type=int, default=-1)
    p.add_argument("--sd-url", default=DEFAULT_SD_URL)
    p.add_argument("--check", action="store_true", help="Just check if SD is running")
    args = p.parse_args()

    if args.check:
        running = check_running(args.sd_url)
        print("running" if running else "stopped")
        sys.exit(0 if running else 1)

    if args.mode == "txt2img":
        txt2img(
            args.prompt, args.negative, args.output,
            width=args.width, height=args.height, steps=args.steps,
            cfg_scale=args.cfg_scale, seed=args.seed, sd_url=args.sd_url,
        )
    else:
        if not args.reference:
            p.error("--reference is required for img2img")
        img2img(
            args.prompt, args.negative, args.reference, args.output,
            denoising_strength=args.denoising,
            width=args.width, height=args.height, steps=args.steps,
            cfg_scale=args.cfg_scale, seed=args.seed, sd_url=args.sd_url,
        )


if __name__ == "__main__":
    main()
