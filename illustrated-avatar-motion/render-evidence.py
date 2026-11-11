#!/usr/bin/env python3
"""2D look/blink evidence from prepared eye layers. No WebGL required."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

LOOKS = {
    "look-left": (-14.0, 0.0, False, "idle"),
    "look-up": (0.0, 8.0, False, "idle"),
    "look-right": (14.0, 0.0, False, "idle"),
    "look-down": (0.0, -8.0, False, "idle"),
    "closed": (0.0, 0.0, True, "sleeping"),
    "idle": (0.0, 0.0, False, "idle"),
}


def draw_frame(eyeless: Image.Image, left: Image.Image, right: Image.Image, eyes: list, yaw: float, pitch: float, closed: bool) -> tuple[Image.Image, list]:
    canvas = eyeless.copy()
    width, height = canvas.size
    dx = yaw / 15.0 * 0.018 * width
    dy = -pitch / 8.0 * 0.012 * height
    coords = []
    if not closed:
        shifted = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        shifted.paste(left, (round(dx), round(dy)), left)
        shifted.paste(right, (round(dx), round(dy)), right)
        canvas = Image.alpha_composite(canvas, shifted)
    for eye in eyes:
        coords.append(
            {
                "side": eye["side"],
                "x": eye["center_xy"][0] + dx,
                "y": eye["center_xy"][1] + dy,
                "closed": closed,
            }
        )
    return canvas, coords


def render_case(case_dir: Path, out_dir: Path) -> dict:
    eyeless = Image.open(case_dir / "layers/canonical-eyeless.png").convert("RGBA")
    left = Image.open(case_dir / "layers/eye-left.png").convert("RGBA")
    right = Image.open(case_dir / "layers/eye-right.png").convert("RGBA")
    eyes = json.loads((case_dir / "layers/eyes.json").read_text(encoding="utf-8"))["eyes"]
    frames = {}
    sheet = Image.new("RGBA", (eyeless.width * 3, eyeless.height * 2), (16, 16, 16, 255))
    for index, (name, (yaw, pitch, closed, state)) in enumerate(LOOKS.items()):
        frame, coords = draw_frame(eyeless, left, right, eyes, yaw, pitch, closed)
        path = out_dir / f"{case_dir.name}-{name}.png"
        frame.save(path)
        frames[name] = {"file": str(path), "state": state, "yaw": yaw, "pitch": pitch, "eyes": coords}
        col, row = index % 3, index // 3
        sheet.paste(frame, (col * eyeless.width, row * eyeless.height))
    sheet_path = out_dir / f"{case_dir.name}-sheet.png"
    sheet.resize((sheet.width // 2, sheet.height // 2), Image.Resampling.LANCZOS).save(sheet_path)
    left_x = frames["look-left"]["eyes"][0]["x"]
    right_x = frames["look-right"]["eyes"][0]["x"]
    closed_flag = frames["closed"]["eyes"][0]["closed"]
    idle_flag = frames["idle"]["eyes"][0]["closed"]
    return {
        "ok": left_x < right_x and closed_flag and not idle_flag,
        "id": case_dir.name,
        "lookDelta": round(right_x - left_x, 3),
        "sheet": str(sheet_path),
        "frames": frames,
    }


def main() -> int:
    out = Path(sys.argv[1])
    cases_root = Path(sys.argv[2])
    ids = sys.argv[3:]
    out.mkdir(parents=True, exist_ok=True)
    reports = [render_case(cases_root / case_id, out) for case_id in ids]
    payload = {"ok": all(item["ok"] for item in reports), "cases": reports}
    sys.stdout.write(json.dumps(payload) + "\n")
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
