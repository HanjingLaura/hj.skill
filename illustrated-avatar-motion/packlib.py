#!/usr/bin/env python3
"""Shared geometry, eye extraction, and eyeless inpaint for illustrated avatars.

Prepared `eyes.json` files from the art worker are the playback source of truth.
This module is the documented, reproducible extractor and inpaint path. It is a
generic fallback, not a claim that the four shipped cases were packed by a fully
automatic production pipeline.
"""

from __future__ import annotations

import json
import math
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

CANVAS = 744
LUMA_EYE = 45
ALPHA_MIN = 180
AREA_FRAC = (0.0025, 0.02)
ASPECT = (1.15, 2.8)


class PackError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def luminance_rgb(r: float, g: float, b: float) -> float:
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def load_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def array_of(image: Image.Image) -> np.ndarray:
    return np.asarray(image.convert("RGBA"), dtype=np.uint8)


def luma_of(pixels: np.ndarray) -> np.ndarray:
    rgb = pixels[:, :, :3].astype(np.float32)
    return 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]


def connected_components(mask: np.ndarray) -> list[dict]:
    height, width = mask.shape
    seen = np.zeros((height, width), dtype=np.uint8)
    blobs: list[dict] = []
    for y, x in np.argwhere(mask):
        y = int(y)
        x = int(x)
        if seen[y, x]:
            continue
        queue = deque([(x, y)])
        seen[y, x] = 1
        xs: list[int] = []
        ys: list[int] = []
        while queue:
            cx, cy = queue.popleft()
            xs.append(cx)
            ys.append(cy)
            for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                if nx < 0 or ny < 0 or nx >= width or ny >= height:
                    continue
                if seen[ny, nx] or not mask[ny, nx]:
                    continue
                seen[ny, nx] = 1
                queue.append((nx, ny))
        area = len(xs)
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        width_px = maxx - minx + 1
        height_px = maxy - miny + 1
        blobs.append(
            {
                "area": area,
                "minx": minx,
                "maxx": maxx,
                "miny": miny,
                "maxy": maxy,
                "cx": sum(xs) / area,
                "cy": sum(ys) / area,
                "width_px": width_px,
                "height_px": height_px,
                "aspect": max(width_px, height_px) / max(1, min(width_px, height_px)),
                "pixels": list(zip(xs, ys)),
            }
        )
    return blobs


def opaque_bounds(pixels: np.ndarray) -> tuple[int, int, int, int]:
    alpha = pixels[:, :, 3]
    ys, xs = np.where(alpha >= ALPHA_MIN)
    if len(xs) == 0:
        raise PackError("no-opaque-pixels", "The image has no opaque pixels.")
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def blob_angle(blob: dict) -> float:
    pts = np.array(blob["pixels"], dtype=np.float64)
    if len(pts) < 8:
        return 90.0
    centered = pts - pts.mean(axis=0)
    cov = np.cov(centered[:, 0], centered[:, 1])
    values, vectors = np.linalg.eigh(cov)
    axis = vectors[:, int(np.argmax(values))]
    return float(np.degrees(np.arctan2(axis[1], axis[0])) % 180)


def capsule_ok(blob: dict, image_area: int) -> bool:
    frac = blob["area"] / max(1, image_area)
    if frac < AREA_FRAC[0] or frac > AREA_FRAC[1]:
        return False
    if blob["aspect"] < ASPECT[0] or blob["aspect"] > ASPECT[1]:
        return False
    # Grokbot capsules are taller than they are wide. Horizontal dark hair is not an eye.
    if blob["height_px"] < blob["width_px"] * 1.08:
        return False
    return True


def choose_pair(blobs: list[dict], bounds: tuple[int, int, int, int]) -> tuple[dict, dict] | None:
    left, top, right, bottom = bounds
    face_w = max(1, right - left)
    face_h = max(1, bottom - top)
    mid_x = (left + right) / 2
    mid_y = (top + bottom) / 2
    best = None
    best_score = 1e18
    ranked = sorted(blobs, key=lambda item: item["area"], reverse=True)[:12]
    for i, a in enumerate(ranked):
        for b in ranked[i + 1 :]:
            dx = abs(a["cx"] - b["cx"])
            dy = abs(a["cy"] - b["cy"])
            if dx < face_w * 0.12 or dx > face_w * 0.72:
                continue
            if dy > face_h * 0.28:
                continue
            pair_mid_x = (a["cx"] + b["cx"]) / 2
            pair_mid_y = (a["cy"] + b["cy"]) / 2
            if abs(pair_mid_x - mid_x) > face_w * 0.28:
                continue
            if pair_mid_y < top + face_h * 0.22 or pair_mid_y > top + face_h * 0.82:
                continue
            area_ratio = max(a["area"], b["area"]) / max(1, min(a["area"], b["area"]))
            if area_ratio > 2.4:
                continue
            aspect_gap = abs(a["aspect"] - b["aspect"])
            score = dy + abs(a["area"] - b["area"]) / 80 + area_ratio * 8 + aspect_gap * 12
            score += abs(pair_mid_x - mid_x) / face_w * 20
            if score < best_score:
                best_score = score
                left_eye, right_eye = (a, b) if a["cx"] < b["cx"] else (b, a)
                best = (left_eye, right_eye)
    return best


def eye_record(blob: dict, width: int, height: int, side: str) -> dict:
    pts = np.array(blob["pixels"], dtype=np.float64)
    centered = pts - pts.mean(axis=0)
    values, vectors = np.linalg.eigh(np.cov(centered[:, 0], centered[:, 1]))
    major = vectors[:, int(np.argmax(values))]
    minor = vectors[:, int(np.argmin(values))]
    # The dark core excludes the antialiased ring. Add one pixel for it.
    axis_height = float(np.ptp(centered @ major)) + 2.0
    axis_width = float(np.ptp(centered @ minor)) + 2.0
    return {
        "side": side,
        "center_xy": [round(blob["cx"], 2), round(blob["cy"], 2)],
        "center_normalized": [round(blob["cx"] / width, 4), round(blob["cy"] / height, 4)],
        "bbox_xyxy": [blob["minx"], blob["miny"], blob["maxx"] + 1, blob["maxy"] + 1],
        "width_px": blob["width_px"],
        "height_px": blob["height_px"],
        "axis_width_px": round(axis_width, 2),
        "axis_height_px": round(axis_height, 2),
        "area_px": blob["area"],
        "long_axis_angle_deg": round(blob_angle(blob), 2),
        "image_size": [width, height],
    }


def extract_eyes(image: Image.Image) -> dict:
    pixels = array_of(image)
    height, width = pixels.shape[:2]
    luma = luma_of(pixels)
    alpha = pixels[:, :, 3]
    left, top, right, bottom = opaque_bounds(pixels)
    band = np.zeros((height, width), dtype=bool)
    band[top:bottom, left:right] = True
    # Dark fur can join the eyes at the normal threshold. Try darker cores
    # only when the normal pass cannot find a valid capsule pair.
    pair = None
    for threshold in (LUMA_EYE, 30, 20, 10):
        mask = band & (alpha >= ALPHA_MIN) & (luma <= threshold)
        blobs = [blob for blob in connected_components(mask) if capsule_ok(blob, width * height)]
        pair = choose_pair(blobs, (left, top, right, bottom))
        if pair is not None:
            break
    if pair is None:
        raise PackError(
            "no-eyes",
            "Could not find two dark capsule eyes. Use --eyes with a prepared eyes.json, or correct the anchors by hand.",
        )
    left_eye, right_eye = pair
    eyes = [eye_record(left_eye, width, height, "left"), eye_record(right_eye, width, height, "right")]
    return {
        "image_size": [width, height],
        "eyes": eyes,
        "coordinate_system": "pixel origin top-left; left/right is viewer's left/right (smaller x is left). Angles are long-axis orientation in image degrees (atan2).",
        "detector": f"dark connected components (luma<={threshold}, alpha>=180) plus capsule/pair filters",
        "notes": "Capsule filter: area 0.25-2% of image, aspect 1.15-2.8, pair similarity + mid-face. Prepared art-worker eyes.json remains the playback source of truth when present.",
    }


def load_eyes_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    eyes = data.get("eyes")
    if not isinstance(eyes, list) or len(eyes) < 2:
        raise PackError("bad-eyes-json", f"{path} does not contain two eyes.")
    return data


def empty_eyes_doc(image: Image.Image) -> dict:
    width, height = image.size
    return {
        "image_size": [width, height],
        "eyes": [],
        "coordinate_system": "pixel origin top-left; left/right is viewer's left/right (smaller x is left).",
        "detector": "skipped",
        "notes": "Detector skipped because both manual left and right anchors were supplied.",
    }


def apply_manual_eyes(base: dict, overrides: dict[str, tuple[float, float, float, float]]) -> dict:
    by_side = {eye["side"]: dict(eye) for eye in base.get("eyes") or []}
    width, height = base["image_size"]
    for side, (cx, cy, w, h) in overrides.items():
        record = by_side.get(side, {"side": side, "long_axis_angle_deg": 110.0, "image_size": [width, height]})
        record.update(
            {
                "side": side,
                "center_xy": [cx, cy],
                "center_normalized": [round(cx / width, 4), round(cy / height, 4)],
                "bbox_xyxy": [int(cx - w / 2), int(cy - h / 2), int(cx + w / 2), int(cy + h / 2)],
                "width_px": w,
                "height_px": h,
                "area_px": int(math.pi * (w / 2) * (h / 2)),
                "image_size": [width, height],
            }
        )
        by_side[side] = record
    if "left" not in by_side or "right" not in by_side:
        raise PackError("bad-eyes-json", "Manual correction needs both left and right anchors.")
    base["eyes"] = [by_side["left"], by_side["right"]]
    base["notes"] = (base.get("notes") or "") + " Manual eye-anchor correction applied."
    return base


def rotated_ellipse_mask(
    height: int,
    width: int,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    angle_deg: float,
    scale: float = 1.0,
) -> np.ndarray:
    ys, xs = np.indices((height, width), dtype=np.float32)
    theta = math.radians(angle_deg - 90.0)
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)
    dx = xs - cx
    dy = ys - cy
    local_x = dx * cos_t + dy * sin_t
    local_y = -dx * sin_t + dy * cos_t
    return (local_x / max(rx * scale, 1.0)) ** 2 + (local_y / max(ry * scale, 1.0)) ** 2 <= 1.0


def dilate(mask: np.ndarray, steps: int) -> np.ndarray:
    out = mask.copy()
    for _ in range(max(0, steps)):
        nxt = out.copy()
        nxt[1:] |= out[:-1]
        nxt[:-1] |= out[1:]
        nxt[:, 1:] |= out[:, :-1]
        nxt[:, :-1] |= out[:, 1:]
        out = nxt
    return out


def clone_from_ring(pixels: np.ndarray, hole: np.ndarray) -> np.ndarray:
    """Fill a hole by growing known colors inward from its boundary.

    A global plane stamps a peach oval on a cat blaze. Growing from the rim
    keeps orange fur on the orange side and white blaze on the white side.
    """
    height, width = hole.shape
    result = pixels.astype(np.float32).copy()
    unknown = hole.copy()
    offsets = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
    for _ in range(max(height, width)):
        frontier = dilate(~unknown, 1) & unknown
        if not frontier.any():
            break
        fy, fx = np.nonzero(frontier)
        chosen = np.zeros(len(fx), dtype=bool)
        for dy, dx in offsets:
            remaining = ~chosen
            if not remaining.any():
                break
            ny = fy + dy
            nx = fx + dx
            inside = (ny >= 0) & (ny < height) & (nx >= 0) & (nx < width)
            nyi = np.clip(ny, 0, height - 1)
            nxi = np.clip(nx, 0, width - 1)
            known = remaining & inside & ~unknown[nyi, nxi]
            if not known.any():
                continue
            result[fy[known], fx[known]] = result[nyi[known], nxi[known]]
            chosen[known] = True
        if not chosen.any():
            break
        unknown[fy[chosen], fx[chosen]] = False
    return np.clip(result, 0, 255).astype(np.uint8)


def eye_hole_mask(pixels: np.ndarray, eye: dict, dilate_px: int = 2) -> np.ndarray:
    height, width = pixels.shape[:2]
    luma = luma_of(pixels)
    alpha = pixels[:, :, 3]
    rx = max(eye["width_px"] / 2, 4)
    ry = max(eye["height_px"] / 2, 6)
    x0, y0, x1, y1 = eye["bbox_xyxy"]
    pad = max(2, int(max(rx, ry) * 0.08))
    bbox = np.zeros((height, width), dtype=bool)
    bbox[max(0, y0 - pad) : min(height, y1 + pad), max(0, x0 - pad) : min(width, x1 + pad)] = True
    dark = bbox & (alpha >= 80) & (luma <= LUMA_EYE + 18)
    return dilate(dark, dilate_px)


def make_eyeless(canonical: Image.Image, eyes_doc: dict) -> Image.Image:
    """Rebuild an eyeless base from the canonical image and measured capsules.

    Each hole is cloned from the nearest ring pixel so a cat blaze is not
    replaced by a peach oval. A short relaxation then removes the clone
    streaks in blush and gradients.
    """
    pixels = array_of(canonical)
    filled = pixels
    for eye in eyes_doc["eyes"]:
        hole = eye_hole_mask(pixels, eye, dilate_px=hole_growth(eye)) & (pixels[:, :, 3] >= 80)
        filled = clone_from_ring(filled, hole)
        short_px = eye.get("axis_width_px", eye["width_px"])
        filled = relax_hole(filled, hole, int(min(60, max(8, short_px * 0.5))))
    rgba = filled.copy()
    rgba[:, :, 3] = pixels[:, :, 3]
    return Image.fromarray(rgba, "RGBA")


def residual_dark_fraction(eyeless: Image.Image, eye: dict) -> float:
    pixels = array_of(eyeless)
    luma = luma_of(pixels)
    alpha = pixels[:, :, 3]
    height, width = pixels.shape[:2]
    cx, cy = eye["center_xy"]
    rx = max(eye["width_px"] / 2, 4)
    ry = max(eye["height_px"] / 2, 6)
    mask = rotated_ellipse_mask(height, width, cx, cy, rx, ry, eye.get("long_axis_angle_deg", 110.0), 0.92)
    inside = mask & (alpha >= ALPHA_MIN)
    total = int(inside.sum())
    if total == 0:
        return 0.0
    dark = int((inside & (luma <= LUMA_EYE + 20)).sum())
    return dark / total


def fit_canvas(image: Image.Image, size: int = CANVAS) -> Image.Image:
    if image.width == size and image.height == size:
        return image
    return image.resize((size, size), Image.Resampling.LANCZOS)


def scale_eyes_to_canvas(eyes_doc: dict, canvas: int = CANVAS) -> tuple[list[dict], float]:
    """Map pixel eyes to 0-100 units. rx and ry are half the short and long axis."""
    width, height = eyes_doc["image_size"]
    mapped = []
    for eye in eyes_doc["eyes"]:
        nx, ny = eye["center_normalized"]
        short_px = eye.get("axis_width_px", eye["width_px"])
        long_px = eye.get("axis_height_px", eye["height_px"])
        mapped.append(
            {
                "x": round(nx * 100, 3),
                "y": round(ny * 100, 3),
                "rx": round((short_px / 2) / width * 100, 3),
                "ry": round((long_px / 2) / height * 100, 3),
            }
        )
    tilt, _source = eye_tilt(eyes_doc)
    _ = canvas
    return mapped, tilt


def rim_color(image: Image.Image) -> str:
    """Return the dominant hair or fur color of the upper silhouette.

    The mean of the full outline mixes hair with skin. The upper half is hair
    or fur on a head, so only that half is sampled.
    """
    pixels = array_of(image)
    size = pixels.shape[0]
    samples: list[tuple[int, int, int]] = []
    for step in range(96):
        angle = math.pi + step / 95 * math.pi
        for radius in range(size // 2 - 2, 8, -1):
            x = int(size / 2 + radius * math.cos(angle))
            y = int(size / 2 + radius * math.sin(angle))
            if x < 0 or y < 0 or x >= size or y >= size or pixels[y, x, 3] <= ALPHA_MIN:
                continue
            # Step inside the antialiased edge.
            inner = max(8, radius - 4)
            x = int(size / 2 + inner * math.cos(angle))
            y = int(size / 2 + inner * math.sin(angle))
            if pixels[y, x, 3] > ALPHA_MIN:
                samples.append((int(pixels[y, x, 0]), int(pixels[y, x, 1]), int(pixels[y, x, 2])))
            break
    if not samples:
        return "#b9bbbd"
    bins: dict[tuple[int, int, int], list[tuple[int, int, int]]] = {}
    for sample in samples:
        bins.setdefault((sample[0] // 40, sample[1] // 40, sample[2] // 40), []).append(sample)
    main = max(bins.values(), key=len)
    n = len(main)
    return "#{:02x}{:02x}{:02x}".format(sum(s[0] for s in main) // n, sum(s[1] for s in main) // n, sum(s[2] for s in main) // n)


def matte_backdrop(image: Image.Image) -> Image.Image:
    """Remove a chroma-green or near-white backdrop. Keep clean native alpha.

    Use this after GenerateImage when the model returns an opaque backdrop.
    Green edges get soft alpha and lose the green spill. This is derived
    alpha, not native model transparency.
    """
    image = image.convert("RGBA")
    pixels = np.array(image)
    if has_native_alpha(pixels):
        return image
    backdrop = green_backdrop(pixels)
    if backdrop is not None:
        edge = dilate(backdrop, 2) & dilate(~backdrop, 2)
        rgb = pixels[:, :, :3].astype(np.float32)
        spill = np.clip(rgb[:, :, 1] - np.maximum(rgb[:, :, 0], rgb[:, :, 2]), 0, 255)
        alpha = np.where(backdrop, 0.0, 1.0).astype(np.float32)
        alpha[edge] = 1.0 - spill[edge] / 255.0
        alpha[alpha < 0.06] = 0.0
        safe = np.maximum(alpha, 0.06)[:, :, None]
        key = np.array([0.0, 255.0, 0.0], dtype=np.float32)
        restored = (rgb - (1.0 - alpha[:, :, None]) * key) / safe
        soft = edge & (alpha > 0)
        rgb[soft] = np.clip(restored[soft], 0, 255)
        rgb[alpha == 0] = 0
        pixels[:, :, :3] = rgb.astype(np.uint8)
        pixels[:, :, 3] = np.round(alpha * 255).astype(np.uint8)
        return Image.fromarray(pixels, "RGBA")
    backdrop = white_backdrop(pixels)
    if backdrop is not None:
        pixels[backdrop] = 0
        return Image.fromarray(pixels, "RGBA")
    return image


def inspect_crops(eyeless: Image.Image, eyes_doc: dict, out_dir: Path, prefix: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    pixels = array_of(eyeless)
    luma = luma_of(pixels)
    for eye in eyes_doc["eyes"]:
        x0, y0, x1, y1 = eye["bbox_xyxy"]
        pad = 24
        crop = eyeless.crop((max(0, x0 - pad), max(0, y0 - pad), min(eyeless.width, x1 + pad), min(eyeless.height, y1 + pad)))
        crop.save(out_dir / f"{prefix}-{eye['side']}-eyeless.png")
        region = luma[max(0, y0 - pad) : min(eyeless.height, y1 + pad), max(0, x0 - pad) : min(eyeless.width, x1 + pad)]
        if region.size == 0:
            continue
        stretched = (region - region.min()) / max(1.0, float(region.max() - region.min()))
        contrast = Image.fromarray((stretched * 255).astype(np.uint8), "L").convert("RGB")
        contrast.save(out_dir / f"{prefix}-{eye['side']}-eyeless-contrast.png")


def checker_composite(image: Image.Image, cell: int = 16) -> Image.Image:
    width, height = image.size
    board = Image.new("RGBA", (width, height), (180, 180, 180, 255))
    draw = ImageDraw.Draw(board)
    for y in range(0, height, cell):
        for x in range(0, width, cell):
            if ((x // cell) + (y // cell)) % 2 == 0:
                draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(220, 220, 220, 255))
    return Image.alpha_composite(board, image.convert("RGBA"))


def reach(mask: np.ndarray, seed: np.ndarray) -> np.ndarray:
    """Return the pixels of `mask` that are 4-connected to `seed`.

    A coarse grid finds most of the region. Full-resolution growth then makes
    the result exact, so thin parts such as whiskers stay connected.
    """
    height, width = mask.shape
    factor = 4
    sh, sw = -(-height // factor), -(-width // factor)
    padded = np.zeros((sh * factor, sw * factor), dtype=bool)
    padded[:height, :width] = mask
    seeds = np.zeros_like(padded)
    seeds[:height, :width] = seed & mask
    small = padded.reshape(sh, factor, sw, factor).all(axis=(1, 3))
    small_seed = seeds.reshape(sh, factor, sw, factor).any(axis=(1, 3)) & small
    seen = small_seed.copy()
    queue = deque((int(x), int(y)) for y, x in np.argwhere(small_seed))
    while queue:
        cx, cy = queue.popleft()
        for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
            if nx < 0 or ny < 0 or nx >= sw or ny >= sh or seen[ny, nx] or not small[ny, nx]:
                continue
            seen[ny, nx] = True
            queue.append((nx, ny))
    current = np.repeat(np.repeat(seen, factor, axis=0), factor, axis=1)[:height, :width] | (seed & mask)
    for _ in range(height + width):
        grown = dilate(current, 1) & mask
        if grown.sum() == current.sum():
            break
        current = grown
    return current


def border_of(shape: tuple[int, int]) -> np.ndarray:
    border = np.zeros(shape, dtype=bool)
    border[0, :] = border[-1, :] = border[:, 0] = border[:, -1] = True
    return border


def has_native_alpha(pixels: np.ndarray) -> bool:
    return float((pixels[:, :, 3] < 250).mean()) > 0.02


def green_backdrop(pixels: np.ndarray) -> np.ndarray | None:
    """Return the chroma-green backdrop mask, or None when there is no green screen.

    Green that touches the border is backdrop. Enclosed green is backdrop only
    when it contains near-pure key green, so a green accessory stays.
    """
    r = pixels[:, :, 0].astype(np.int16)
    g = pixels[:, :, 1].astype(np.int16)
    b = pixels[:, :, 2].astype(np.int16)
    loose = (g > 150) & (g > r + 35) & (g > b + 35)
    outer = reach(loose, border_of(loose.shape))
    if float(outer.mean()) < 0.02:
        return None
    inner = loose & ~outer
    enclosed = inner & (g > 215) & (r < 70) & (b < 70)
    if enclosed.any():
        enclosed = reach(inner, enclosed)
    return outer | enclosed


def white_backdrop(pixels: np.ndarray) -> np.ndarray | None:
    """Return the border-connected near-white backdrop mask, or None."""
    height, width = pixels.shape[:2]
    corners = [pixels[0, 0], pixels[0, width - 1], pixels[height - 1, 0], pixels[height - 1, width - 1]]
    if not all(c[3] > 200 and luminance_rgb(float(c[0]), float(c[1]), float(c[2])) > 220 for c in corners):
        return None
    seed = corners[0].astype(np.int16)
    rgb = pixels[:, :, :3].astype(np.int16)
    similar = (np.abs(rgb - seed[:3]).max(axis=2) < 18) & (luma_of(pixels) > 210) & (pixels[:, :, 3] >= 8)
    return reach(similar, border_of(similar.shape))


def line_tilt(eyes_doc: dict) -> float:
    lcx, lcy = eyes_doc["eyes"][0]["center_xy"]
    rcx, rcy = eyes_doc["eyes"][1]["center_xy"]
    return round(math.degrees(math.atan2(rcy - lcy, rcx - lcx)), 2)


def eye_tilt(eyes_doc: dict) -> tuple[float, str]:
    """Return the tilt of the eye capsules and its source.

    The player rotates each eye by `tiltDeg`, so the value is the long-axis
    tilt of the capsules. The line between the eyes is the fallback for round
    or hand-entered eyes, where the long axis is not reliable.
    """
    tilts = []
    for eye in eyes_doc["eyes"]:
        angle = eye.get("long_axis_angle_deg")
        long_px = eye.get("axis_height_px")
        short_px = eye.get("axis_width_px")
        if angle is None or long_px is None or short_px is None or long_px < short_px * 1.2:
            return line_tilt(eyes_doc), "eye-line"
        tilts.append(angle - 90.0)
    if abs(tilts[0] - tilts[1]) > 20:
        return line_tilt(eyes_doc), "eye-line"
    return round(sum(tilts) / len(tilts), 2), "eye-axis"


def hole_growth(eye: dict) -> int:
    """Pixels to grow the dark core so that the antialiased ring is inside the hole."""
    short_px = eye.get("axis_width_px", eye["width_px"])
    return int(min(5, max(2, round(short_px * 0.06))))


def relax_hole(pixels: np.ndarray, hole: np.ndarray, steps: int) -> np.ndarray:
    """Smooth the cloned fill inside the hole. Pixels outside the hole do not change."""
    ys, xs = np.nonzero(hole)
    if len(xs) == 0:
        return pixels
    y0, y1 = max(0, ys.min() - 2), min(hole.shape[0], ys.max() + 3)
    x0, x1 = max(0, xs.min() - 2), min(hole.shape[1], xs.max() + 3)
    window = pixels[y0:y1, x0:x1, :3].astype(np.float32)
    inside = hole[y0:y1, x0:x1]
    for _ in range(steps):
        padded = np.pad(window, ((1, 1), (1, 1), (0, 0)), mode="edge")
        mean = (padded[:-2, 1:-1] + padded[2:, 1:-1] + padded[1:-1, :-2] + padded[1:-1, 2:]) / 4
        window[inside] = mean[inside]
    out = pixels.copy()
    out[y0:y1, x0:x1, :3] = np.clip(window, 0, 255).astype(np.uint8)
    return out
