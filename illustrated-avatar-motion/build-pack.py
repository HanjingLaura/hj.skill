#!/usr/bin/env python3
"""Build an Ani illustrated-avatar pack from one image.

The script does not call a hosted model. Feed a grokbot-style tilted head, or
the original gray-avatar sheet. Photographs and images with no face fail.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from PIL import Image, ImageDraw, ImageFilter, ImageStat

from packlib import (
    PackError,
    extract_eyes,
    fit_canvas,
    load_eyes_json,
    make_eyeless,
    matte_backdrop,
    residual_dark_fraction,
    scale_eyes_to_canvas,
)

CANVAS = 744
KNOWN_GRAY_EYES = ((37.47, 57.83), (57.75, 62.73))


def fail(code: str, message: str) -> None:
    raise PackError(code, message)


def luminance(pixel: tuple[int, int, int, int]) -> float:
    r, g, b, _a = pixel
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def chroma_key(image: Image.Image) -> Image.Image:
    return matte_backdrop(image)


def crop_sheet_front(image: Image.Image) -> Image.Image:
    width, height = image.size
    if width >= height * 1.8:
        cell = width // 3
        return image.crop((0, 0, cell, height))
    return image


def fit_square(image: Image.Image, size: int = CANVAS) -> Image.Image:
    bbox = image.getbbox()
    if bbox is None:
        fail("no-opaque-pixels", "The image has no opaque pixels after background removal.")
    left, top, right, bottom = bbox
    pad = int(max(right - left, bottom - top) * 0.08)
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(image.width, right + pad)
    bottom = min(image.height, bottom + pad)
    cropped = image.crop((left, top, right, bottom))
    side = max(cropped.width, cropped.height)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(cropped, ((side - cropped.width) // 2, (side - cropped.height) // 2))
    return square.resize((size, size), Image.Resampling.LANCZOS)


def flood_keep(image: Image.Image, alpha_limit: int = 100) -> tuple[Image.Image, int]:
    size = image.size[0]
    pixels = image.load()
    seen = bytearray(size * size)
    queue = deque()

    def add(x: int, y: int) -> None:
        if x < 0 or y < 0 or x >= size or y >= size:
            return
        index = y * size + x
        if seen[index]:
            return
        if pixels[x, y][3] < alpha_limit:
            return
        seen[index] = 1
        queue.append((x, y))

    add(size // 2, size // 2)
    if not queue:
        fail("no-center-face", "No opaque face was found at the canvas center. This is not a usable head.")
    while queue:
        x, y = queue.popleft()
        add(x - 1, y)
        add(x + 1, y)
        add(x, y - 1)
        add(x, y + 1)
    kept = 0
    for y in range(size):
        row = y * size
        for x in range(size):
            if seen[row + x]:
                kept += 1
            else:
                pixels[x, y] = (0, 0, 0, 0)
    ratio = kept / (size * size)
    if ratio < 0.08:
        fail("too-small", f"The kept silhouette covers {ratio:.1%} of the canvas. Need a close head crop.")
    if ratio > 0.92:
        fail("no-silhouette", "The image fills the canvas. Need a cut-out head with transparent or keyed background.")
    return image, kept


def opaque_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    bbox = image.getbbox()
    if bbox is None:
        fail("no-opaque-pixels", "The cleaned canvas is empty.")
    return bbox


def components(mask: list[list[bool]]) -> list[dict]:
    height = len(mask)
    width = len(mask[0]) if height else 0
    seen = [[False] * width for _ in range(height)]
    blobs: list[dict] = []
    for y in range(height):
        for x in range(width):
            if not mask[y][x] or seen[y][x]:
                continue
            queue = deque([(x, y)])
            seen[y][x] = True
            xs: list[int] = []
            ys: list[int] = []
            while queue:
                cx, cy = queue.popleft()
                xs.append(cx)
                ys.append(cy)
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if nx < 0 or ny < 0 or nx >= width or ny >= height or seen[ny][nx] or not mask[ny][nx]:
                        continue
                    seen[ny][nx] = True
                    queue.append((nx, ny))
            blobs.append(
                {
                    "area": len(xs),
                    "minx": min(xs),
                    "maxx": max(xs),
                    "miny": min(ys),
                    "maxy": max(ys),
                    "cx": sum(xs) / len(xs),
                    "cy": sum(ys) / len(ys),
                    "pixels": list(zip(xs, ys)),
                }
            )
    return blobs


def is_skin(pixel: tuple[int, int, int, int]) -> bool:
    r, g, b, a = pixel
    if a < 180:
        return False
    return r > 175 and r >= g + 8 and g >= b - 12 and luminance(pixel) > 145


def sample_skin(image: Image.Image, eyes: list[dict]) -> tuple[int, int, int]:
    pixels = image.load()
    size = image.size[0]
    samples: list[tuple[int, int, int]] = []
    for eye in eyes:
        for scale in (0.7, 1.0, 1.3, 1.6):
            for step in range(16):
                angle = step / 16 * math.pi * 2
                radius = max(eye["width"], eye["height"]) * scale
                x = int(eye["px"] + math.cos(angle) * radius)
                y = int(eye["py"] + math.sin(angle) * radius)
                if x < 0 or y < 0 or x >= size or y >= size:
                    continue
                pixel = pixels[x, y]
                if not is_skin(pixel):
                    continue
                samples.append((pixel[0], pixel[1], pixel[2]))
    if not samples:
        return (252, 215, 200)
    n = len(samples)
    return (sum(s[0] for s in samples) // n, sum(s[1] for s in samples) // n, sum(s[2] for s in samples) // n)


def inpaint_ellipse(image: Image.Image, eye: dict, color: tuple[int, int, int], scale: float = 1.35) -> None:
    draw = ImageDraw.Draw(image)
    cx, cy = eye["px"], eye["py"]
    rx = eye["width"] / 2 * scale
    ry = eye["height"] / 2 * scale
    box = [cx - rx, cy - ry, cx + rx, cy + ry]
    draw.ellipse(box, fill=(*color, 255))


def remaining_dark(image: Image.Image, eye: dict) -> float:
    pixels = image.load()
    total = 0
    dark = 0
    rx = eye["width"] / 2 * 1.05
    ry = eye["height"] / 2 * 1.05
    for x, y in eye["pixels"]:
        total += 1
        dx = (x - eye["px"]) / max(rx, 1)
        dy = (y - eye["py"]) / max(ry, 1)
        if dx * dx + dy * dy > 1:
            continue
        if luminance(pixels[x, y]) < 80 and pixels[x, y][3] > 180:
            dark += 1
    return 0 if total == 0 else dark / total


def inpaint_mouth(image: Image.Image, eyes: list[dict], color: tuple[int, int, int]) -> bool:
    size = image.size[0]
    pixels = image.load()
    left, top, right, bottom = opaque_bbox(image)
    eye_bottom = max(eye["py"] + eye["height"] / 2 for eye in eyes)
    band_top = int(eye_bottom + 8)
    band_bottom = int(top + (bottom - top) * 0.92)
    mid = (eyes[0]["px"] + eyes[1]["px"]) / 2
    mask = [[False] * size for _ in range(size)]
    for y in range(max(band_top, 0), min(band_bottom, size)):
        for x in range(left, right):
            pixel = pixels[x, y]
            if pixel[3] < 180:
                continue
            if abs(x - mid) > (right - left) * 0.22:
                continue
            r, g, b, a = pixel
            redder = r > g + 20 and r > b + 20 and r > 120
            skin_luma = 0.2126 * color[0] + 0.7152 * color[1] + 0.0722 * color[2]
            darker = skin_luma - luminance(pixel) > 28 and luminance(pixel) > 70
            if redder or darker:
                mask[y][x] = True
    blobs = [blob for blob in components(mask) if 80 <= blob["area"] <= 4000]
    if not blobs:
        return False
    blob = max(blobs, key=lambda item: item["area"])
    if blob["cy"] <= eye_bottom:
        return False
    draw = ImageDraw.Draw(image)
    pad = 6
    draw.ellipse(
        [blob["minx"] - pad, blob["miny"] - pad, blob["maxx"] + pad, blob["maxy"] + pad],
        fill=(*color, 255),
    )
    return True


def photographic(image: Image.Image) -> bool:
    rgba = image.convert("RGBA").resize((96, 96))
    pixels = rgba.load()
    count = 96 * 96
    green = 0
    trans = 0
    for y in range(96):
        for x in range(96):
            r, g, b, a = pixels[x, y]
            if a < 12:
                trans += 1
            elif g > 150 and g > r + 35 and g > b + 35:
                green += 1
    if green > count * 0.06 or trans > count * 0.08:
        return False
    small = image.convert("RGB").resize((64, 64))
    stat = ImageStat.Stat(small)
    variance = sum(stat.var) / 3
    edges = small.filter(ImageFilter.FIND_EDGES)
    edge_mean = ImageStat.Stat(edges).mean[0]
    return variance > 1800 and edge_mean > 18


def rim_color(image: Image.Image) -> str:
    pixels = image.load()
    size = image.size[0]
    samples: list[tuple[int, int, int]] = []
    for angle_i in range(64):
        angle = angle_i / 64 * math.pi * 2
        for radius in range(size // 2 - 2, 8, -1):
            x = int(size / 2 + radius * math.cos(angle))
            y = int(size / 2 + radius * math.sin(angle))
            if x < 0 or y < 0 or x >= size or y >= size:
                continue
            r, g, b, a = pixels[x, y]
            if a > 180:
                samples.append((r, g, b))
                break
    if not samples:
        return "#b9bbbd"
    n = len(samples)
    return "#{:02x}{:02x}{:02x}".format(sum(s[0] for s in samples) // n, sum(s[1] for s in samples) // n, sum(s[2] for s in samples) // n)


def tilt_of(eyes: list[dict]) -> float:
    dx = eyes[1]["px"] - eyes[0]["px"]
    dy = eyes[1]["py"] - eyes[0]["py"]
    return round(math.degrees(math.atan2(dy, dx)), 2)


def build(path: Path, out: Path, identity: str, allow_photo: bool, eyes_json: Path | None = None) -> dict:
    image = Image.open(path)
    if photographic(image) and not allow_photo and eyes_json is None:
        fail(
            "needs-stylization",
            "This looks like a photograph. Generate a grokbot-style tilted chibi head first, then run build-pack.",
        )
    keyed = chroma_key(crop_sheet_front(image))

    if eyes_json is not None:
        eyes_doc = load_eyes_json(eyes_json)
        cleaned = make_eyeless(keyed, eyes_doc)
        fitted = fit_canvas(cleaned)
        cleaned, kept = flood_keep(fitted)
        before = fit_canvas(keyed)
        mapped, tilt_override = scale_eyes_to_canvas(eyes_doc)
        eyes = [
            {
                **mapped[i],
                "px": mapped[i]["x"] / 100 * CANVAS,
                "py": mapped[i]["y"] / 100 * CANVAS,
                "width": mapped[i]["rx"] / 100 * CANVAS * 2,
                "height": mapped[i]["ry"] / 100 * CANVAS * 2,
                "pixels": [],
            }
            for i in range(2)
        ]
        notes = "prepared-eyes.json"
        leftovers = [residual_dark_fraction(cleaned, eye) for eye in eyes_doc["eyes"]]
        mouth = False
        _ = tilt_override
    else:
        fitted = fit_square(keyed)
        cleaned, kept = flood_keep(fitted)
        before = cleaned.copy()
        eyes_doc = extract_eyes(cleaned)
        cleaned = make_eyeless(cleaned, eyes_doc)
        mapped, tilt_override = scale_eyes_to_canvas(eyes_doc)
        eyes = [
            {
                **mapped[i],
                "px": mapped[i]["x"] / 100 * CANVAS,
                "py": mapped[i]["y"] / 100 * CANVAS,
                "width": mapped[i]["rx"] / 100 * CANVAS * 2,
                "height": mapped[i]["ry"] / 100 * CANVAS * 2,
                "pixels": [],
            }
            for i in range(2)
        ]
        notes = "packlib.extract_eyes+make_eyeless"
        leftovers = [residual_dark_fraction(cleaned, eye) for eye in eyes_doc["eyes"]]
        skin = sample_skin(cleaned, eyes)
        mouth = inpaint_mouth(cleaned, eyes, skin)
        _ = tilt_override
        if max(leftovers) > 0.12:
            fail("baked-eyes-remain", f"Baked eye pixels still cover {max(leftovers):.0%} of an eye region after cleanup.")
    out.mkdir(parents=True, exist_ok=True)
    front_path = out / "front.png"
    cleaned.save(front_path)
    before.save(out / "front-before-eye-clean.png")
    tilt = tilt_of(eyes)
    pack = {
        "id": identity,
        "version": 1,
        "artwork": "front.png",
        "canvas": CANVAS,
        "cropWidth": CANVAS,
        "tiltDeg": tilt,
        "eyes": [{"x": eye["x"], "y": eye["y"], "rx": eye["rx"], "ry": eye["ry"]} for eye in eyes],
        "rim": rim_color(cleaned),
        "eyePaint": "#1c1c25",
        "chinSmooth": None,
        "source": str(path),
        "notes": notes,
        "mouthRemoved": mouth,
    }
    (out / "pack.json").write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")
    report = {
        "ok": True,
        "code": "ok",
        "id": identity,
        "keptPixels": kept,
        "keptRatio": round(kept / (CANVAS * CANVAS), 4),
        "tiltDeg": tilt,
        "eyes": pack["eyes"],
        "rim": pack["rim"],
        "mouthRemoved": mouth,
        "bakedEyeRemain": leftovers,
        "front": str(front_path),
        "pack": str(out / "pack.json"),
        "notes": notes,
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an illustrated avatar pack.")
    parser.add_argument("image", help="Source PNG/JPEG/WebP")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--id", default="custom")
    parser.add_argument("--allow-photo", action="store_true", help="Skip the photograph rejection. Still requires two dark eyes.")
    parser.add_argument("--eyes", help="Use prepared eyes.json instead of detecting. Also rebuilds the eyeless base.")
    parser.add_argument("--json", action="store_true", help="Write the report to stdout")
    args = parser.parse_args()
    try:
        report = build(Path(args.image), Path(args.out), args.id, args.allow_photo, Path(args.eyes) if args.eyes else None)
    except PackError as error:
        payload = {"ok": False, "code": error.code, "error": error.message}
        if args.json:
            sys.stdout.write(json.dumps(payload) + "\n")
        else:
            sys.stderr.write(f"{error.code}: {error.message}\n")
        return 2
    if args.json:
        sys.stdout.write(json.dumps(report) + "\n")
    else:
        sys.stdout.write(f"ok {report['pack']}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
