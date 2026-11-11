#!/usr/bin/env python3
"""Import the four prepared art-worker cases into demo pack directories.

Playback uses the prepared eyes.json anchors. Eyeless bases are rebuilt by
refine-eyeless so faint oval stamps are not shipped. Original Wikimedia photos
stay out of the repo; only the head-crop / official avatar used as the demo
source is copied. CC BY-SA 2.0 attribution is written next to cases 03 and 04.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from packlib import (
    CANVAS,
    checker_composite,
    fit_canvas,
    inspect_crops,
    load_eyes_json,
    load_rgba,
    make_eyeless,
    residual_dark_fraction,
    rim_color,
    scale_eyes_to_canvas,
)

CASES = (
    {
        "id": "01-diplo",
        "title": "Diplo official avatar",
        "source_rel": "sources/avatar-official.png",
        "source_name": "source.png",
        "license": "All rights reserved by the bot owner. Private-repo demo fixture only.",
        "alpha": "Native RGBA on the official 512 file. Canonical equals official.",
        "identity": "White/silver fluffy hair, blue-gray streaks, topknot, blue diamond charm.",
        "keep_prepared_eyeless": True,
    },
    {
        "id": "02-test",
        "title": "Test official avatar",
        "source_rel": "sources/avatar-official.png",
        "source_name": "source.png",
        "license": "All rights reserved by the bot owner. Private-repo demo fixture only.",
        "alpha": "Native RGBA on the official 1024 file. Canonical is a conservative yellow-fringe cleanup.",
        "identity": "Blonde/gold curls, black and silver streaks, crescent-moon charm.",
        "keep_prepared_eyeless": True,
    },
    {
        "id": "03-short-bob-woman",
        "title": "Short brown bob, red earrings",
        "source_rel": "sources/head-crop.jpg",
        "source_name": "source.jpg",
        "license": "CC BY-SA 2.0",
        "alpha": "RGBA from edge-flood matting of a white JPEG. Not native model transparency.",
        "identity": "Short dark-brown bob, red drop earrings, warm skin, peach blush.",
    },
    {
        "id": "04-orange-tabby-cat",
        "title": "Orange and white tabby cat",
        "source_rel": "sources/head-crop.jpg",
        "source_name": "source.jpg",
        "license": "CC BY-SA 2.0",
        "alpha": "RGBA from edge-flood matting of a white JPEG. White muzzle kept. Not native model transparency.",
        "identity": "Orange tabby, white blaze and muzzle, pink nose, cat ears. Not a humanoid haircut.",
    },
)


def copy_if(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def import_case(root: Path, spec: dict, out_root: Path, inspect_root: Path | None) -> dict:
    src = root / spec["id"]
    dest = out_root / spec["id"]
    dest.mkdir(parents=True, exist_ok=True)
    layers = dest / "layers"
    layers.mkdir(parents=True, exist_ok=True)

    canonical_src = src / "canonical" / "canonical.png"
    eyes_src = src / "layers" / "eyes.json"
    if not canonical_src.is_file() or not eyes_src.is_file():
        raise FileNotFoundError(f"Missing canonical or eyes.json for {spec['id']}")

    canonical = load_rgba(canonical_src)
    eyes_doc = load_eyes_json(eyes_src)
    eyes_doc["canonical"] = "canonical.png"
    eyes_doc["case_id"] = spec["id"]
    prepared_eyeless = src / "layers" / "canonical-eyeless.png"
    if spec.get("keep_prepared_eyeless") and prepared_eyeless.is_file():
        eyeless = load_rgba(prepared_eyeless)
        eyeless_note = "art-worker prepared eyeless (already clean)"
    else:
        eyeless = make_eyeless(canonical, eyes_doc)
        eyeless_note = "refine-eyeless plane fill from canonical + prepared eyes.json"
    leftovers = [residual_dark_fraction(eyeless, eye) for eye in eyes_doc["eyes"]]
    if max(leftovers) >= 0.02:
        raise RuntimeError(f"{spec['id']} still has baked-eye leftovers {leftovers}")

    copy_if(canonical_src, dest / "canonical.png")
    source_src = src / spec["source_rel"]
    if source_src.is_file():
        copy_if(source_src, dest / spec["source_name"])
    for name in ("eye-left.png", "eye-right.png", "eyes-both.png"):
        layer = src / "layers" / name
        if layer.is_file():
            copy_if(layer, layers / name)
    (layers / "eyes.json").write_text(json.dumps(eyes_doc, indent=2) + "\n", encoding="utf-8")
    eyeless.save(layers / "canonical-eyeless.png")

    front = fit_canvas(eyeless, CANVAS)
    front.save(dest / "front.png")
    mapped, tilt = scale_eyes_to_canvas(eyes_doc, CANVAS)
    pack = {
        "id": spec["id"],
        "version": 1,
        "artwork": "front.png",
        "canvas": CANVAS,
        "cropWidth": CANVAS,
        "tiltDeg": tilt,
        "eyes": mapped,
        "rim": rim_color(front),
        "eyePaint": "#1c1c25",
        "chinSmooth": None,
        "source": spec["source_name"],
        "canonical": "canonical.png",
        "eyeless": "layers/canonical-eyeless.png",
        "eyeLayers": {"left": "layers/eye-left.png", "right": "layers/eye-right.png"},
        "eyesJson": "layers/eyes.json",
        "license": spec["license"],
        "alphaStatus": spec["alpha"],
        "identity": spec["identity"],
        "title": spec["title"],
        "anchorsSource": "prepared-eyes.json",
        "eyelessSource": eyeless_note,
    }
    (dest / "pack.json").write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")
    if inspect_root is not None:
        inspect_crops(eyeless, eyes_doc, inspect_root, spec["id"])
        checker_composite(eyeless).resize((256, 256)).save(inspect_root / f"{spec['id']}-checker.png")
    report = {
        "ok": True,
        "id": spec["id"],
        "tiltDeg": tilt,
        "eyes": mapped,
        "bakedEyeRemain": leftovers,
        "front": str(dest / "front.png"),
    }
    (dest / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def write_attribution(root: Path, out_root: Path) -> None:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    lines = [
        "# Attribution",
        "",
        "Cases 01 and 02 are official bot avatars. They ship in this private Ani-2.0",
        "repository for a local demo. Do not publish them if the repository becomes public.",
        "Do not treat this copy as a license to relicense those files.",
        "",
        "Cases 03 and 04 are chibi derivatives of Wikimedia photographs. The photographs",
        "are CC BY-SA 2.0. The derivatives keep that license. PolyForm Noncommercial on",
        "the rest of the repository does not relicense these files.",
        "",
    ]
    for case in manifest.get("cases", []):
        license_info = case.get("license") or {}
        lines.append(f"## {case['id']}")
        lines.append("")
        lines.append(f"- Subject: {case.get('subject')}")
        if license_info:
            lines.append(f"- License: {license_info.get('license')} ({license_info.get('license_url')})")
            lines.append(f"- Author: {license_info.get('author')}")
            lines.append(f"- Credit: {license_info.get('credit')}")
            lines.append(f"- Commons: {license_info.get('commons_page')}")
            lines.append(f"- Derivative notice: {license_info.get('attribution_for_derivative')}")
        else:
            lines.append("- Official bot avatar. Private-repo demo fixture. Not a public-domain release.")
        alpha = case.get("alpha_status")
        if alpha:
            lines.append(f"- Alpha: {alpha}")
        lines.append("")
    (out_root / "ATTRIBUTION.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Import the four prepared avatar cases.")
    parser.add_argument("--from", dest="source", required=True, help="Unpacked zip root (manifest.json + 01-diplo/...)")
    parser.add_argument("--out", default="scripts/illustrated-avatar/cases")
    parser.add_argument("--inspect", help="Write zoom crops")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = Path(args.source)
    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)
    inspect_root = Path(args.inspect) if args.inspect else None
    reports = []
    for spec in CASES:
        reports.append(import_case(root, spec, out_root, inspect_root))
    write_attribution(root, out_root)
    payload = {"ok": all(item["ok"] for item in reports), "cases": reports}
    if args.json:
        sys.stdout.write(json.dumps(payload) + "\n")
    else:
        for item in reports:
            sys.stdout.write(f"ok {item['id']} tilt {item['tiltDeg']} remain={item['bakedEyeRemain']}\n")
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
