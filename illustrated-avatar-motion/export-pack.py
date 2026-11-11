"""Export one avatar and its local viewer without unrelated case fixtures."""
import argparse
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("id")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    case = (ROOT / "cases" / args.id).resolve()
    if case.parent != (ROOT / "cases").resolve():
        parser.error("id must be one case directory name")
    for name in ("pack.json", "front.png", "preview.html", "preview.js"):
        if not (case / name).is_file():
            parser.error(f"missing {name}")
    output = Path(args.out).resolve()
    if output.is_relative_to(case):
        parser.error("output must be outside the case")
    files = []
    for folder in (case, ROOT / "runtime", ROOT / "demo"):
        files.extend(p for p in folder.rglob("*") if p.is_file() and not p.is_symlink() and "__pycache__" not in p.parts)
    for name in ("serve.py", "build-pack.py", "packlib.py", "requirements.txt"):
        files.append(ROOT / name)
    attribution = ROOT / "cases" / "ATTRIBUTION.md"
    if attribution.exists():
        files.append(attribution)
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as bundle:
        for file in files:
            bundle.write(file, file.relative_to(ROOT).as_posix())
        bundle.writestr("START.txt", f"Run python serve.py here. Open http://127.0.0.1:8766/cases/{args.id}/preview.html\nInstall requirements.txt for image upload/build.\n")
    print(json.dumps({"ok": True, "id": args.id, "zip": str(output), "files": len(files)}))

if __name__ == "__main__":
    main()
