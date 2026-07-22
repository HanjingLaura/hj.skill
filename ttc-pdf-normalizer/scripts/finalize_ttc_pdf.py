#!/usr/bin/env python3
"""Validate a PDF and copy it atomically to <candidate-name>-TTC.pdf."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unicodedata


INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
TRAILING_TTC = re.compile(r"(?:[\s_-]*TTC)(?:\.pdf)?$", re.IGNORECASE)


def candidate_name(raw_name: str) -> str:
    name = unicodedata.normalize("NFC", raw_name).replace("\u00a0", " ").strip()
    if name.lower().endswith(".pdf"):
        name = name[:-4].rstrip()
    name = TRAILING_TTC.sub("", name).strip()
    name = INVALID_FILENAME_CHARS.sub("_", name)
    name = re.sub(r"\s+", " ", name).strip(" .-_")
    if not name:
        raise ValueError("candidate name is empty after filename sanitization")
    if len(name) > 120:
        raise ValueError("candidate name is longer than 120 characters")
    return name


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_pdf(path: Path) -> tuple[int | None, list[str]]:
    if not path.is_file():
        raise ValueError(f"PDF does not exist: {path}")
    if path.stat().st_size < 100:
        raise ValueError("file is too small to be a valid PDF")

    with path.open("rb") as stream:
        header = stream.read(1024)
        stream.seek(max(0, path.stat().st_size - 8192))
        trailer = stream.read()
    if b"%PDF-" not in header:
        raise ValueError("file does not contain a PDF header")
    if b"%%EOF" not in trailer:
        raise ValueError("file does not contain a PDF end marker")

    warnings: list[str] = []
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(path))
        if reader.is_encrypted:
            raise ValueError("PDF is encrypted; unlock it before finalization")
        pages = len(reader.pages)
        if pages < 1:
            raise ValueError("PDF contains no pages")
        return pages, warnings
    except ImportError:
        warnings.append("pypdf is unavailable; page count was not checked")
        return None, warnings


def same_file_content(first: Path, second: Path) -> bool:
    return first.stat().st_size == second.stat().st_size and sha256(first) == sha256(second)


def finalize(source: Path, name: str, output_dir: Path, overwrite: bool) -> dict[str, object]:
    source = source.expanduser().resolve()
    page_count, warnings = inspect_pdf(source)
    safe_name = candidate_name(name)
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"{safe_name}-TTC.pdf"

    reused = False
    if destination == source:
        reused = True
    elif destination.exists():
        if same_file_content(source, destination):
            reused = True
        elif not overwrite:
            raise FileExistsError(
                f"destination exists with different content: {destination}; "
                "rerun with --overwrite only after replacement is authorized"
            )

    if not reused:
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                prefix=f".{safe_name}-TTC-",
                suffix=".pdf.tmp",
                dir=output_dir,
                delete=False,
            ) as temp_stream:
                temp_path = Path(temp_stream.name)
            shutil.copy2(source, temp_path)
            os.replace(temp_path, destination)
        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()

    final_pages, final_warnings = inspect_pdf(destination)
    warnings.extend(item for item in final_warnings if item not in warnings)
    return {
        "output": str(destination),
        "filename": destination.name,
        "bytes": destination.stat().st_size,
        "sha256": sha256(destination),
        "pages": final_pages if final_pages is not None else page_count,
        "reused": reused,
        "source_preserved": True,
        "warnings": warnings,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a PDF and copy it to <candidate-name>-TTC.pdf."
    )
    parser.add_argument("source_pdf", type=Path, help="Converted PDF to finalize")
    name_group = parser.add_mutually_exclusive_group(required=True)
    name_group.add_argument("--name", help="Candidate's verified name")
    name_group.add_argument(
        "--name-utf8-hex",
        help="Candidate name encoded as hexadecimal UTF-8 bytes; use if the shell corrupts Unicode",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for the final PDF",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace a different existing destination file",
    )
    return parser.parse_args()


def decoded_name(args: argparse.Namespace) -> str:
    if args.name is not None:
        return args.name
    try:
        return bytes.fromhex(args.name_utf8_hex).decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("--name-utf8-hex must contain valid hexadecimal UTF-8 bytes") from exc


def main() -> int:
    args = parse_args()
    try:
        result = finalize(args.source_pdf, decoded_name(args), args.output_dir, args.overwrite)
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
