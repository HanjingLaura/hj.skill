#!/usr/bin/env python3
"""Inventory, hash-deduplicate, and extract mixed resume folders.

This script intentionally does not decide candidate quality.  It creates the
private audit surface used by the skill's evidence-based review workflow.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Iterable


SUPPORTED = {".pdf", ".docx", ".doc", ".jpg", ".jpeg", ".png"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        action="append",
        dest="inputs",
        required=True,
        help="Resume folder. Repeat for multiple batches.",
    )
    parser.add_argument("--output", required=True, help="Private output directory.")
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional maximum files for a smoke test; 0 means all.",
    )
    return parser.parse_args()


def iter_files(roots: list[Path]) -> Iterable[tuple[str, Path]]:
    for index, root in enumerate(roots, 1):
        if not root.is_dir():
            raise FileNotFoundError(f"Input directory not found: {root}")
        batch = root.name or f"batch-{index}"
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix.lower() in SUPPORTED:
                yield batch, path


def digest_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def require_module(module_name: str, package_name: str):
    try:
        return __import__(module_name)
    except ImportError as exc:
        raise RuntimeError(
            f"Missing dependency {package_name!r}. Install it in the active "
            f"Python environment before extracting this file type."
        ) from exc


def extract_pdf(path: Path) -> str:
    pypdf = require_module("pypdf", "pypdf")
    reader = pypdf.PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def extract_docx(path: Path) -> str:
    docx = require_module("docx", "python-docx")
    document = docx.Document(str(path))
    parts = [paragraph.text for paragraph in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            parts.append("\t".join(cell.text for cell in row.cells))
    return "\n".join(parts)


def extract_text(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    try:
        if suffix == ".pdf":
            text = extract_pdf(path)
        elif suffix == ".docx":
            text = extract_docx(path)
        else:
            return "", f"manual-review-required:{suffix}"
    except Exception as exc:  # preserve the file in the audit instead of aborting
        return "", f"extract-error:{type(exc).__name__}:{exc}"

    normalized = text.strip()
    if len(normalized) < 80:
        return normalized, "manual-review-required:low-text"
    return normalized, "ok"


def filename_hints(path: Path) -> dict[str, object]:
    stem = path.stem
    cleaned = re.sub(r"[【\[].*?[】\]]", "", stem)
    parts = [part.strip() for part in cleaned.split("-") if part.strip()]
    years_match = re.search(r"工作\s*(\d+)\s*年", stem)
    return {
        "role_hint": parts[0] if parts else "",
        "name_hint": parts[1] if len(parts) > 1 else "",
        "work_years_hint": int(years_match.group(1)) if years_match else None,
    }


def write_outputs(output: Path, records: list[dict[str, object]]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    text_dir = output / "text"
    text_dir.mkdir(exist_ok=True)

    for record in records:
        text = record.pop("_text", "")
        if text:
            text_path = text_dir / f"{record['sha256']}.txt"
            text_path.write_text(str(text), encoding="utf-8")
            record["text_path"] = str(text_path.resolve())
        else:
            record["text_path"] = ""

    with (output / "inventory.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    columns = [
        "batch",
        "source_path",
        "filename",
        "extension",
        "size_bytes",
        "sha256",
        "duplicate_of",
        "role_hint",
        "name_hint",
        "work_years_hint",
        "extraction_status",
        "text_chars",
        "text_path",
    ]
    with (output / "inventory.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

    unique = [record for record in records if not record["duplicate_of"]]
    summary = {
        "files": len(records),
        "unique_resumes": len(unique),
        "exact_duplicates": len(records) - len(unique),
        "extraction_ok": sum(
            record["extraction_status"] == "ok" for record in unique
        ),
        "manual_review_required": sum(
            record["extraction_status"] != "ok" for record in unique
        ),
    }
    (output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))


def main() -> int:
    args = parse_args()
    roots = [Path(value).expanduser().resolve() for value in args.inputs]
    output = Path(args.output).expanduser().resolve()
    seen: dict[str, str] = {}
    records: list[dict[str, object]] = []

    for number, (batch, path) in enumerate(iter_files(roots), 1):
        if args.limit and number > args.limit:
            break
        digest = digest_file(path)
        duplicate_of = seen.get(digest, "")
        text, status = ("", "duplicate") if duplicate_of else extract_text(path)
        if not duplicate_of:
            seen[digest] = str(path.resolve())
        hints = filename_hints(path)
        records.append(
            {
                "batch": batch,
                "source_path": str(path.resolve()),
                "filename": path.name,
                "extension": path.suffix.lower(),
                "size_bytes": path.stat().st_size,
                "sha256": digest,
                "duplicate_of": duplicate_of,
                **hints,
                "extraction_status": status,
                "text_chars": len(text),
                "_text": text,
            }
        )

    write_outputs(output, records)
    return 0


if __name__ == "__main__":
    sys.exit(main())
