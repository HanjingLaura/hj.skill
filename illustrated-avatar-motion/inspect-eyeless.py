#!/usr/bin/env python3
"""Zoom-crop committed eyeless bases and reject leftover black eye rims."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from packlib import inspect_crops, luma_of, load_eyes_json, load_rgba


def hole_stats(image: Image.Image, eye: dict) -> dict:
    pixels = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    luma = luma_of(pixels)
    x0, y0, x1, y1 = eye["bbox_xyxy"]
    cx, cy = eye["center_xy"]
    rx = max(eye["width_px"] / 2 * 0.7, 8)
    ry = max(eye["height_px"] / 2 * 0.7, 10)
    ys, xs = np.ogrid[0 : pixels.shape[0], 0 : pixels.shape[1]]
    inner = ((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2 <= 1.0
    opaque = inner & (pixels[:, :, 3] >= 180)
    values = luma[opaque]
    dark = int((values <= 45).sum()) if values.size else 0
    return {
        "side": eye["side"],
        "count": int(values.size),
        "minLuma": None if values.size == 0 else round(float(values.min()), 2),
        "p5": None if values.size == 0 else round(float(np.quantile(values, 0.05)), 2),
        "mean": None if values.size == 0 else round(float(values.mean()), 2),
        "dark45": dark,
        "ok": values.size > 20 and dark == 0 and float(values.min()) > 60,
        "bbox": [x0, y0, x1, y1],
    }


def main() -> int:
    out = Path(sys.argv[1])
    cases_root = Path(sys.argv[2])
    ids = sys.argv[3:]
    out.mkdir(parents=True, exist_ok=True)
    cases = []
    ok = True
    for case_id in ids:
        eyeless = load_rgba(cases_root / case_id / "layers/canonical-eyeless.png")
        eyes = load_eyes_json(cases_root / case_id / "layers/eyes.json")
        inspect_crops(eyeless, eyes, out, case_id)
        stats = [hole_stats(eyeless, eye) for eye in eyes["eyes"]]
        case_ok = all(item["ok"] for item in stats)
        ok = ok and case_ok
        cases.append({"id": case_id, "ok": case_ok, "eyes": stats})
    payload = {"ok": ok, "code": "ok" if ok else "black-rims", "cases": cases, "error": None if ok else json.dumps(cases)}
    sys.stdout.write(json.dumps(payload) + "\n")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
