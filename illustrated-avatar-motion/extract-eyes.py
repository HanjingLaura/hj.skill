#!/usr/bin/env python3
"""Extract two capsule-eye anchors from a grokbot-style head.

This is the documented generic extractor. Prepared art-worker `eyes.json` files
are still the playback source of truth for the four shipped cases. Use this
script to check drift, to seed a new upload, or to write a manual correction.

Example:

  python3 scripts/illustrated-avatar/extract-eyes.py path/to/canonical.png --json
  python3 scripts/illustrated-avatar/extract-eyes.py path/to/canonical.png \\
      --correct left=116.7,313.33,40,65 right=255.49,377.83,40,65 --out eyes.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from packlib import PackError, apply_manual_eyes, empty_eyes_doc, extract_eyes, eye_tilt, load_eyes_json, load_rgba


def parse_correct(text: str) -> tuple[str, tuple[float, float, float, float]]:
    side, values = text.split("=", 1)
    parts = [float(item) for item in values.split(",")]
    if side not in {"left", "right"} or len(parts) != 4:
        raise argparse.ArgumentTypeError("Need left=cx,cy,width,height or right=cx,cy,width,height")
    return side, (parts[0], parts[1], parts[2], parts[3])


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract or correct capsule-eye anchors.")
    parser.add_argument("image", help="Canonical PNG with two dark capsule eyes")
    parser.add_argument("--eyes", help="Start from this eyes.json instead of detecting")
    parser.add_argument(
        "--correct",
        action="append",
        default=[],
        type=parse_correct,
        help="Manual override: left=cx,cy,w,h and/or right=cx,cy,w,h in pixels",
    )
    parser.add_argument("--out", help="Write eyes.json here")
    parser.add_argument("--json", action="store_true", help="Write the document to stdout")
    args = parser.parse_args()
    image_path = Path(args.image)
    try:
        image = load_rgba(image_path)
        corrections = dict(args.correct)
        both_manual = set(corrections) >= {"left", "right"}
        if args.eyes:
            doc = load_eyes_json(Path(args.eyes))
            if corrections:
                doc = apply_manual_eyes(doc, corrections)
        elif both_manual:
            doc = apply_manual_eyes(empty_eyes_doc(image), corrections)
        else:
            doc = extract_eyes(image)
            if corrections:
                doc = apply_manual_eyes(doc, corrections)
        doc["canonical"] = str(image_path)
        doc["case_id"] = image_path.parent.parent.name if image_path.parent.name == "canonical" else image_path.stem
    except PackError as error:
        payload = {"ok": False, "code": error.code, "error": error.message}
        sys.stdout.write(json.dumps(payload) + "\n")
        return 2
    if args.out:
        Path(args.out).write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    report = {
        "ok": True,
        "code": "ok",
        "id": doc.get("case_id"),
        "image_size": doc["image_size"],
        "eyes": [
            {
                "side": eye["side"],
                "x": round(eye["center_normalized"][0] * 100, 3),
                "y": round(eye["center_normalized"][1] * 100, 3),
                "cx": eye["center_xy"][0],
                "cy": eye["center_xy"][1],
                "width_px": eye["width_px"],
                "height_px": eye["height_px"],
                "long_axis_angle_deg": eye.get("long_axis_angle_deg"),
            }
            for eye in doc["eyes"]
        ],
        "tiltDeg": eye_tilt(doc)[0],
        "tiltSource": eye_tilt(doc)[1],
        "source": "manual" if args.correct or args.eyes else "extract-eyes",
        "eyes_json": args.out,
    }
    if args.json:
        sys.stdout.write(json.dumps(report) + "\n")
    else:
        sys.stdout.write(f"ok {report['id']} tilt {report['tiltDeg']}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
