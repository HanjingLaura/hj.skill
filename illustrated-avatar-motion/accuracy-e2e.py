#!/usr/bin/env python3
"""E2E accuracy check for the upload-to-pack path.

The script draws heads with known eyes, backdrop and eyeless base. It sends
each one through build-pack.py as the upload route does, then compares the
pack with the known values. It writes
evidence/accuracy/report.json and exits non-zero when
a value is out of tolerance.

  python accuracy-e2e.py
"""
import json, math, subprocess, sys, time
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SS = 2
N = 1024
SKIN = (252, 215, 200); HAIR = (120, 90, 200); DARK = (34, 30, 38); EYE = (28, 28, 37)

def capsule(size, cx, cy, rx, ry, tilt, fill):
    layer = Image.new("L", (size, size), 0)
    box = Image.new("L", (int(ry * 4), int(ry * 4)), 0)
    c = box.size[0] / 2
    ImageDraw.Draw(box).rounded_rectangle((c - rx, c - ry, c + rx, c + ry), radius=rx, fill=255)
    box = box.rotate(-tilt, resample=Image.BICUBIC)
    layer.paste(box, (int(cx - c), int(cy - c)))
    return layer

def make(case):
    s = N * SS
    k = SS
    subj = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(subj)
    ox, oy, sc = case.get("ox", 0), case.get("oy", 0), case.get("sc", 1.0)
    def P(v): return v * sc * k
    def X(v): return (v * sc + ox) * k
    def Y(v): return (v * sc + oy) * k
    d.ellipse((X(140), Y(220), X(884), Y(900)), fill=SKIN + (255,))
    hair = DARK if case.get("dark") else HAIR
    d.pieslice((X(110), Y(120), X(914), Y(760)), 180, 360, fill=hair + (255,))
    if case.get("fringe"):
        d.polygon([(X(300), Y(430)), (X(520), Y(430)), (X(430), Y(530))], fill=hair + (255,))
    if case.get("blush"):
        bl = Image.new("L", (s, s), 0)
        bd = ImageDraw.Draw(bl)
        for cx, cy in ((330, 640), (690, 690)):
            bd.ellipse((X(cx - 110), Y(cy - 70), X(cx + 110), Y(cy + 70)), fill=150)
        bl = bl.filter(ImageFilter.GaussianBlur(P(28)))
        pink = Image.new("RGBA", (s, s), (255, 150, 160, 255))
        a = np.array(subj)[:, :, 3]
        bl = Image.fromarray((np.array(bl) * (a > 0)).astype(np.uint8))
        subj.paste(pink, (0, 0), bl)
    if case.get("clip"):
        d.rounded_rectangle((X(600), Y(250), X(700), Y(300)), radius=P(20), fill=(60, 200, 90, 255))
    if case.get("gap"):
        d.ellipse((X(250), Y(250), X(330), Y(400)), fill=(0, 0, 0, 0))
    eyeless = subj.copy()
    tilt = case.get("tilt", 20)
    rx, ry = case.get("rx", 30), case.get("ry", 60)
    eyes = [(400, 600), (610, 650)]
    for cx, cy in eyes:
        m = capsule(s, X(cx), Y(cy), P(rx), P(ry), tilt, 255)
        subj.paste(Image.new("RGBA", (s, s), EYE + (255,)), (0, 0), m)
    bg = case.get("bg", (0, 255, 0))
    full = Image.new("RGBA", (s, s), bg + (255,))
    full.alpha_composite(subj)
    full = full.resize((N, N), Image.LANCZOS).convert("RGB")
    truth = eyeless.resize((N, N), Image.LANCZOS)
    meta = {"eyes": [[cx * sc + ox, cy * sc + oy] for cx, cy in eyes], "rx": rx * sc, "ry": ry * sc, "tilt": tilt, "clip": [600 * sc + ox, 250 * sc + oy, 700 * sc + ox, 300 * sc + oy] if case.get("clip") else None}
    return full, truth, meta

CASES = {
    "base": {},
    "blush": {"blush": True},
    "green-clip": {"clip": True},
    "hair-gap": {"gap": True},
    "dark-hair-fringe": {"dark": True, "fringe": True},
    "small-offcenter": {"sc": 0.62, "ox": 60, "oy": 300, "blush": True},
    "upright-round-eyes": {"tilt": 0, "rx": 34, "ry": 46},
    "tilt-30": {"tilt": 30, "blush": True},
    "white-bg": {"bg": (255, 255, 255)},
}

def bbox_alpha(img, thr=128):
    a = np.array(img)[:, :, 3]
    ys, xs = np.where(a > thr)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1

def evaluate(pipeline: Path, out: Path, py: str):
    rows = []
    for name, case in CASES.items():
        d = out / name
        d.mkdir(parents=True, exist_ok=True)
        full, truth, meta = make(case)
        src = d / "upload.png"
        full.save(src); truth.save(d / "truth-eyeless.png")
        t0 = time.perf_counter()
        child = subprocess.run([py, str(pipeline / "build-pack.py"), str(src), "--out", str(d / "pack"), "--id", name, "--json"], capture_output=True, text=True)
        dt = time.perf_counter() - t0
        try:
            rep = json.loads(child.stdout.strip().splitlines()[-1])
        except Exception:
            rep = {"ok": False, "code": "crash", "error": child.stderr[-300:]}
        row = {"case": name, "ok": rep.get("ok"), "code": rep.get("code"), "sec": round(dt, 2), "confidence": rep.get("confidence"), "review": rep.get("review")}
        if rep.get("ok"):
            pack = json.loads((d / "pack" / "pack.json").read_text())
            front = Image.open(d / "pack" / "front.png").convert("RGBA")
            C = front.size[0]
            tb = bbox_alpha(truth); fb = bbox_alpha(front)
            sc = ((fb[2] - fb[0]) / (tb[2] - tb[0]) + (fb[3] - fb[1]) / (tb[3] - tb[1])) / 2
            offx = fb[0] - tb[0] * sc; offy = fb[1] - tb[1] * sc
            unit = 100 / C
            cerr = []
            for (tx, ty), e in zip(meta["eyes"], pack["eyes"]):
                cerr.append(math.hypot((tx * sc + offx) * unit - e["x"], (ty * sc + offy) * unit - e["y"]))
            trx = meta["rx"] * sc * unit; try_ = meta["ry"] * sc * unit
            row.update({
                "fill%": round((fb[2] - fb[0]) / C * 100, 1),
                "eye_center_err": round(max(cerr), 2),
                "rx(got/true)": f"{pack['eyes'][0]['rx']:.2f}/{trx:.2f}",
                "ry(got/true)": f"{pack['eyes'][0]['ry']:.2f}/{try_:.2f}",
                "tilt(got/true)": f"{pack['tiltDeg']:.1f}/{meta['tilt']}",
                "eyeExtent": pack.get("eyeExtent"),
                "rim": pack["rim"],
            })
            tm = Image.new("RGBA", (C, C), (0, 0, 0, 0))
            tw = truth.resize((round(N * sc), round(N * sc)), Image.LANCZOS)
            tm.paste(tw, (round(offx), round(offy)))
            F = np.array(front).astype(np.int16); T = np.array(tm).astype(np.int16)
            fa, ta = F[:, :, 3], T[:, :, 3]
            row["holes_px"] = int(((ta > 250) & (fa < 50)).sum())
            row["bg_kept_px"] = int(((ta < 5) & (fa > 128)).sum())
            g = F[:, :, 1]; r = F[:, :, 0]; b = F[:, :, 2]
            greenish = (fa > 128) & (g > r + 35) & (g > b + 35)
            if meta["clip"]:
                x0, y0, x1, y1 = [int(v * sc + (offx if i % 2 == 0 else offy)) for i, v in enumerate(meta["clip"])]
                greenish[max(0, y0 - 3):y1 + 3, max(0, x0 - 3):x1 + 3] = False
            row["green_fringe_px"] = int(greenish.sum())
            ys, xs = np.indices((C, C))
            errs = []
            for tx, ty in meta["eyes"]:
                cx, cy = tx * sc + offx, ty * sc + offy
                m = (((xs - cx) / (meta["rx"] * sc * 1.7)) ** 2 + ((ys - cy) / (meta["ry"] * sc * 1.4)) ** 2 <= 1) & (ta > 250) & (fa > 250)
                diff = np.abs(F[:, :, :3] - T[:, :, :3]).max(axis=2)[m]
                errs.append((float(diff.mean()), int(np.percentile(diff, 99))))
            row["fill_err(mean/p99)"] = f"{max(e[0] for e in errs):.1f}/{max(e[1] for e in errs)}"
        else:
            row["error"] = (rep.get("error") or "")[:90]
        rows.append(row)
    return rows

MARGIN = 1.1


def failures(row: dict) -> list[str]:
    if not row.get("ok"):
        return [f"build failed: {row.get('code')}"]
    bad = []
    got_tilt, true_tilt = (float(v) for v in row["tilt(got/true)"].split("/"))
    if abs(got_tilt - true_tilt) > 1.0:
        bad.append(f"tilt {got_tilt} against {true_tilt}")
    for key in ("rx(got/true)", "ry(got/true)"):
        got, true = (float(v) for v in row[key].split("/"))
        if abs(got / MARGIN - true) / true > 0.08:
            bad.append(f"{key} {got / MARGIN:.2f} against {true}")
    if row["eye_center_err"] > 0.4:
        bad.append(f"eye center error {row['eye_center_err']}")
    if row["holes_px"] > 50:
        bad.append(f"{row['holes_px']} subject pixels removed")
    if row["bg_kept_px"] > 50 or row["green_fringe_px"] > 20:
        bad.append(f"backdrop left: {row['bg_kept_px']} kept, {row['green_fringe_px']} green")
    mean, p99 = (float(v) for v in row["fill_err(mean/p99)"].split("/"))
    if mean > 4 or p99 > 14:
        bad.append(f"eyeless fill error {mean}/{p99}")
    return bad


def main() -> int:
    here = Path(__file__).resolve().parent
    out = here / "evidence" / "accuracy"
    rows = evaluate(here, out, sys.executable)
    failed = 0
    for row in rows:
        row["failures"] = failures(row)
        failed += bool(row["failures"])
        sys.stdout.write(json.dumps(row, ensure_ascii=False) + "\n")
    (out / "report.json").write_text(json.dumps({"ok": failed == 0, "cases": rows}, indent=2) + "\n", encoding="utf-8")
    sys.stdout.write(f"{len(rows) - failed}/{len(rows)} cases in tolerance. Report: {out / 'report.json'}\n")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
