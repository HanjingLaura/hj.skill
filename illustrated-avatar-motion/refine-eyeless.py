#!/usr/bin/env python3
"""Rebuild canonical-eyeless.png from a canonical head and eyes.json.

Does not keep a previous median fill. Each capsule is cloned from a ring just
outside the measured eye so skin stays even and fur/blaze boundaries stay local.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from packlib import inspect_crops, load_eyes_json, load_rgba, make_eyeless, residual_dark_fraction


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild an eyeless base.")
    parser.add_argument("canonical")
    parser.add_argument("--eyes", required=True, help="Prepared or extracted eyes.json")
    parser.add_argument("--out", required=True, help="Write canonical-eyeless.png here")
    parser.add_argument("--inspect", help="Write zoom crops to this directory")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    canonical = load_rgba(Path(args.canonical))
    eyes = load_eyes_json(Path(args.eyes))
    eyeless = make_eyeless(canonical, eyes)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    eyeless.save(out)
    leftovers = [residual_dark_fraction(eyeless, eye) for eye in eyes["eyes"]]
    if args.inspect:
        inspect_crops(eyeless, eyes, Path(args.inspect), Path(args.out).stem)
    report = {
        "ok": max(leftovers) < 0.02,
        "code": "ok" if max(leftovers) < 0.02 else "baked-eyes-remain",
        "out": str(out),
        "bakedEyeRemain": leftovers,
    }
    if args.json:
        sys.stdout.write(json.dumps(report) + "\n")
    else:
        sys.stdout.write(f"{report['code']} remain={leftovers}\n")
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
