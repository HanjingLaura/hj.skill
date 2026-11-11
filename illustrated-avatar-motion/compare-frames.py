#!/usr/bin/env python3
"""Compare look/blink screenshots: eyes move, hair and accessories stay."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def load(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)


def head_bbox(pixels: np.ndarray) -> tuple[int, int, int, int]:
    mask = pixels.max(axis=2) > 28
    ys, xs = np.where(mask)
    if len(xs) == 0:
        raise SystemExit(f"no-head in frame shape={pixels.shape}")
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def region_diff(a: np.ndarray, b: np.ndarray, box: tuple[int, int, int, int]) -> float:
    x0, y0, x1, y1 = box
    if x1 <= x0 or y1 <= y0:
        return 0.0
    patch = np.abs(a[y0:y1, x0:x1].astype(np.int32) - b[y0:y1, x0:x1].astype(np.int32))
    return float(patch.mean())


def split_regions(box: tuple[int, int, int, int]) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
    x0, y0, x1, y1 = box
    width = x1 - x0
    height = y1 - y0
    hair = (x0, y0, x1, y0 + int(height * 0.28))
    eyes = (x0 + int(width * 0.12), y0 + int(height * 0.38), x0 + int(width * 0.78), y0 + int(height * 0.82))
    return hair, eyes


def main() -> int:
    out = Path(sys.argv[1])
    ids = sys.argv[2:]
    results = []
    ok = True
    for case_id in ids:
        idle = load(out / f"{case_id}-idle.png")
        closed = load(out / f"{case_id}-closed.png")
        left = load(out / f"{case_id}-look-left.png")
        right = load(out / f"{case_id}-look-right.png")
        sleeping = load(out / f"{case_id}-sleeping.png")
        listening = load(out / f"{case_id}-listening.png")
        box = head_bbox(idle)
        hair, eyes = split_regions(box)
        blink_eyes = region_diff(idle, closed, eyes)
        blink_hair = region_diff(idle, closed, hair)
        look_eyes = region_diff(left, right, eyes)
        look_hair = region_diff(left, right, hair)
        sleep_eyes = region_diff(idle, sleeping, eyes)
        sleep_hair = region_diff(idle, sleeping, hair)
        listen_eyes = region_diff(idle, listening, eyes)
        listen_hair = region_diff(idle, listening, hair)
        blink_ok = blink_eyes > 4 and blink_eyes > blink_hair * 1.15
        look_ok = look_eyes > 3 and look_eyes > look_hair * 1.4
        sleep_ok = sleep_eyes > 3 and sleep_eyes > sleep_hair * 1.15
        listen_ok = listen_eyes > 1.5 and listen_eyes > listen_hair * 1.05
        item = {
            "id": case_id,
            "blinkEyes": round(blink_eyes, 3),
            "blinkHair": round(blink_hair, 3),
            "lookEyes": round(look_eyes, 3),
            "lookHair": round(look_hair, 3),
            "sleepEyes": round(sleep_eyes, 3),
            "sleepHair": round(sleep_hair, 3),
            "listenEyes": round(listen_eyes, 3),
            "listenHair": round(listen_hair, 3),
            "blinkOk": blink_ok,
            "lookOk": look_ok,
            "sleepOk": sleep_ok,
            "listenOk": listen_ok,
        }
        results.append(item)
        if not blink_ok or not look_ok or not sleep_ok or not listen_ok:
            ok = False
    payload = {"ok": ok, "code": "ok" if ok else "frame-mismatch", "error": None if ok else json.dumps(results), "cases": results}
    sys.stdout.write(json.dumps(payload) + "\n")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
