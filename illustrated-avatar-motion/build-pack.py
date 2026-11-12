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
import time
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageStat

from packlib import (
    ALPHA_MIN,
    LUMA_EYE,
    PackError,
    extract_eyes,
    eye_tilt,
    fit_canvas,
    load_eyes_json,
    luma_of,
    make_eyeless,
    matte_backdrop,
    reach,
    residual_dark_fraction,
    rim_color,
    rotated_ellipse_mask,
    scale_eyes_to_canvas,
    white_backdrop,
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
    pixels = np.array(image.convert("RGBA"))
    size = pixels.shape[0]
    solid = pixels[:, :, 3] >= alpha_limit
    seed = np.zeros_like(solid)
    seed[size // 2, size // 2] = True
    if not solid[size // 2, size // 2]:
        fail("no-center-face", "No opaque face was found at the canvas center. This is not a usable head.")
    keep = reach(solid, seed)
    pixels[~keep] = 0
    kept = int(keep.sum())
    ratio = kept / (size * size)
    if ratio < 0.08:
        fail("too-small", f"The kept silhouette covers {ratio:.1%} of the canvas. Need a close head crop.")
    if ratio > 0.92:
        fail("no-silhouette", "The image fills the canvas. Need a cut-out head with transparent or keyed background.")
    return Image.fromarray(pixels, "RGBA"), kept


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
    pixels = np.asarray(image.convert("RGBA").resize((96, 96)))
    r = pixels[:, :, 0].astype(np.int16)
    g = pixels[:, :, 1].astype(np.int16)
    b = pixels[:, :, 2].astype(np.int16)
    trans = pixels[:, :, 3] < 12
    green = ~trans & (g > 150) & (g > r + 35) & (g > b + 35)
    if green.mean() > 0.06 or trans.mean() > 0.08:
        return False
    # A flat illustration on a plain white backdrop is not a photograph.
    white = white_backdrop(pixels)
    if white is not None and white.mean() > 0.08:
        return False
    small = image.convert("RGB").resize((64, 64))
    stat = ImageStat.Stat(small)
    variance = sum(stat.var) / 3
    edges = small.filter(ImageFilter.FIND_EDGES)
    edge_mean = ImageStat.Stat(edges).mean[0]
    return variance > 1800 and edge_mean > 18


def build(path: Path, out: Path, identity: str, allow_photo: bool, eyes_json: Path | None = None) -> dict:
    started = time.perf_counter()
    image = Image.open(path)
    image.load()
    if photographic(image) and not allow_photo and eyes_json is None:
        fail(
            "needs-stylization",
            "This looks like a photograph. Generate a grokbot-style tilted chibi head first, then run build-pack.",
        )
    keyed = chroma_key(crop_sheet_front(image))
    matte_done = time.perf_counter()
    source_px: int | None = None

    if eyes_json is not None:
        eyes_doc = load_eyes_json(eyes_json)
        cleaned = make_eyeless(keyed, eyes_doc)
        leftovers = [residual_dark_fraction(cleaned, eye) for eye in eyes_doc["eyes"]]
        fitted = fit_canvas(cleaned)
        cleaned, kept = flood_keep(fitted)
        before = fit_canvas(keyed)
        notes = "prepared-eyes.json"
        mouth = False
    else:
        box = keyed.getchannel("A").getbbox()
        if box is not None:
            source_px = max(box[2] - box[0], box[3] - box[1])
        fitted = fit_square(keyed)
        cleaned, kept = flood_keep(fitted)
        before = cleaned.copy()
        eyes_doc = extract_eyes(cleaned)
        cleaned = make_eyeless(cleaned, eyes_doc)
        leftovers = [residual_dark_fraction(cleaned, eye) for eye in eyes_doc["eyes"]]
        notes = "packlib.extract_eyes+make_eyeless"
    mapped, _tilt = scale_eyes_to_canvas(eyes_doc)
    tilt, tilt_source = eye_tilt(eyes_doc)
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
    if eyes_json is None:
        skin = sample_skin(cleaned, eyes)
        mouth = inpaint_mouth(cleaned, eyes, skin)
        if max(leftovers) > 0.12:
            fail("baked-eyes-remain", f"Baked eye pixels still cover {max(leftovers):.0%} of an eye region after cleanup.")
    eyes_done = time.perf_counter()
    measured = tilt_source == "eye-axis"
    # The player draws a 73 x 160 pill on a 220-unit eye canvas. Size that canvas so
    # that the drawn pill has the measured height. The cutout gets a 10% margin.
    margin = 1.1 if measured else 1.0
    pack_eyes = [
        {"x": eye["x"], "y": eye["y"], "rx": round(eye["rx"] * margin, 3), "ry": round(eye["ry"] * margin, 3)}
        for eye in mapped
    ]
    review = review_checks(cleaned, before, mapped, eyes_doc, tilt, tilt_source, leftovers, source_px)
    out.mkdir(parents=True, exist_ok=True)
    front_path = out / "front.png"
    cleaned.save(front_path)
    before.save(out / "front-before-eye-clean.png")
    pack = {
        "id": identity,
        "version": 2,
        "artwork": "front.png",
        "canvas": CANVAS,
        "cropWidth": CANVAS,
        "tiltDeg": tilt,
        "tiltSource": tilt_source,
        "eyes": pack_eyes,
        "rim": rim_color(cleaned),
        "eyePaint": "#1c1c25",
        "chinSmooth": None,
        "source": str(path),
        "notes": notes,
        "mouthRemoved": mouth,
    }
    if measured:
        mean_ry = (mapped[0]["ry"] + mapped[1]["ry"]) / 2
        pack["eyeExtent"] = round(min(19.0, max(11.0, mean_ry * 2 * 220 / 160)), 2)
    (out / "pack.json").write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")
    done = time.perf_counter()
    report = {
        "ok": True,
        "code": "ok",
        "id": identity,
        "confidence": "review" if review else "high",
        "review": review,
        "keptPixels": kept,
        "keptRatio": round(kept / (CANVAS * CANVAS), 4),
        "tiltDeg": tilt,
        "tiltSource": tilt_source,
        "eyes": pack["eyes"],
        "eyeExtent": pack.get("eyeExtent"),
        "rim": pack["rim"],
        "mouthRemoved": mouth,
        "bakedEyeRemain": leftovers,
        "front": str(front_path),
        "pack": str(out / "pack.json"),
        "notes": notes,
        "timingMs": {
            "matte": round((matte_done - started) * 1000),
            "eyes": round((eyes_done - matte_done) * 1000),
            "write": round((done - eyes_done) * 1000),
            "total": round((done - started) * 1000),
        },
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




def review_checks(
    cleaned: Image.Image,
    before: Image.Image,
    mapped: list[dict],
    eyes_doc: dict,
    tilt: float,
    tilt_source: str,
    leftovers: list[float],
    source_px: int | None,
) -> list[str]:
    """Return the reasons why a person must look at this pack before use.

    An empty list means that the measured values agree with each other. It
    does not replace a look at the moving avatar.
    """
    codes: list[str] = []
    pixels = np.asarray(cleaned)
    alpha = pixels[:, :, 3]
    with_eyes = np.asarray(before.convert("RGBA"))
    dark = (luma_of(with_eyes) <= LUMA_EYE + 18) & (with_eyes[:, :, 3] >= ALPHA_MIN)
    size = pixels.shape[0]
    first, second = eyes_doc["eyes"][0], eyes_doc["eyes"][1]
    areas = sorted([max(1, first["area_px"]), max(1, second["area_px"])])
    if areas[1] / areas[0] > 1.5:
        codes.append("eyes-differ-in-size")
    if tilt_source != "eye-axis":
        codes.append("tilt-from-eye-line")
    for eye in mapped:
        cx, cy = eye["x"] / 100 * size, eye["y"] / 100 * size
        rx, ry = eye["rx"] / 100 * size, eye["ry"] / 100 * size
        near = rotated_ellipse_mask(size, size, cx, cy, rx, ry, tilt + 90.0, 1.6)
        if (alpha[near] < ALPHA_MIN).any() and "eye-near-edge" not in codes:
            codes.append("eye-near-edge")
        ring = rotated_ellipse_mask(size, size, cx, cy, rx, ry, tilt + 90.0, 1.9) & ~rotated_ellipse_mask(
            size, size, cx, cy, rx, ry, tilt + 90.0, 1.3
        )
        if ring.any() and float(dark[ring].mean()) > 0.04 and "eye-touches-dark-area" not in codes:
            codes.append("eye-touches-dark-area")
    if max(leftovers) > 0.02:
        codes.append("eye-residue")
    if source_px is not None and source_px < 420:
        codes.append("low-resolution-source")
    ys, xs = np.nonzero(alpha >= ALPHA_MIN)
    if len(xs) and max(xs.max() - xs.min(), ys.max() - ys.min()) < size * 0.6:
        codes.append("small-silhouette")
    return codes


if __name__ == "__main__":
    raise SystemExit(main())
