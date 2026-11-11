#!/usr/bin/env python3
"""Flood-matte a white or chroma-green JPEG into an RGBA PNG.

GenerateImage often returns a white backdrop. This script does not invent
native model alpha. It keys chroma green and corner-connected near-white.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from packlib import PackError, load_rgba, matte_backdrop


def main() -> int:
    parser = argparse.ArgumentParser(description="Matte a stylized head onto transparency.")
    parser.add_argument("image", help="Stylized head JPEG/PNG from GenerateImage")
    parser.add_argument("--out", required=True, help="Output RGBA PNG")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        image = matte_backdrop(load_rgba(Path(args.image)))
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        image.save(out)
    except PackError as error:
        payload = {"ok": False, "code": error.code, "error": error.message}
        sys.stdout.write(json.dumps(payload) + "\n")
        return 2
    payload = {"ok": True, "code": "ok", "out": str(out), "alpha": "corner-flood / chroma-green matte. Not native model transparency."}
    if args.json:
        sys.stdout.write(json.dumps(payload) + "\n")
    else:
        sys.stdout.write(f"ok {out}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
