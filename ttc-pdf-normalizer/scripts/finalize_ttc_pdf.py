#!/usr/bin/env python3
"""Validate, optionally clean, and atomically finalize a TTC resume PDF."""

from __future__ import annotations

import argparse
from datetime import datetime
from io import BytesIO
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unicodedata


INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
TRAILING_TTC = re.compile(r"(?:[\s_-]*TTC)(?:-\d{6,})?(?:\.pdf)?$", re.IGNORECASE)
STAMPED_OUTPUT = re.compile(r"-TTC-(?P<date>\d{4})(?P<sequence>\d{2,})\.pdf$", re.IGNORECASE)
BOSS_NUMERIC_WATERMARK = re.compile(r"\d{8,20}")


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


def validate_date_mmdd(value: str) -> str:
    if not re.fullmatch(r"\d{4}", value):
        raise ValueError("--date-mmdd must use exactly four digits in MMDD format")
    try:
        datetime.strptime(value, "%m%d")
    except ValueError as exc:
        raise ValueError("--date-mmdd must be a valid MMDD date") from exc
    return value


def _is_light_color(color: object) -> bool:
    """Return True only for colors safely close to a white page background."""
    if isinstance(color, (int, float)):
        return float(color) >= 0.55
    if not isinstance(color, (tuple, list)):
        return False
    try:
        values = [float(item) for item in color]
    except (TypeError, ValueError):
        return False
    if len(values) == 1:
        return values[0] >= 0.55
    if len(values) == 3:
        return min(values) >= 0.55
    if len(values) == 4:
        cyan, magenta, yellow, black = values
        red = 1.0 - min(1.0, cyan + black)
        green = 1.0 - min(1.0, magenta + black)
        blue = 1.0 - min(1.0, yellow + black)
        return min(red, green, blue) >= 0.55
    return False


def detect_boss_numeric_watermarks(
    source: Path,
) -> tuple[dict[int, list[tuple[float, float, float, float]]], list[str]]:
    """Find high-confidence small, light numeric marks in the top-right page margin."""
    warnings: list[str] = []
    try:
        import pdfplumber  # type: ignore
    except ImportError:
        warnings.append("Boss watermark auto-check skipped: pdfplumber is unavailable")
        return {}, warnings

    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    matches: dict[int, list[tuple[float, float, float, float]]] = {}
    try:
        with pdfplumber.open(str(source)) as document:
            for page_index, page in enumerate(document.pages):
                if int(page.rotation or 0) % 360:
                    warnings.append(
                        f"Boss watermark auto-check skipped on rotated page {page_index + 1}"
                    )
                    continue
                try:
                    words = page.extract_words(extra_attrs=["size", "non_stroking_color"])
                except Exception as exc:  # malformed third-party PDFs vary widely
                    warnings.append(
                        f"Boss watermark auto-check failed on page {page_index + 1}: {exc}"
                    )
                    continue
                for word in words:
                    text = re.sub(r"[\s_-]+", "", unicodedata.normalize("NFKC", word["text"]))
                    if BOSS_NUMERIC_WATERMARK.fullmatch(text) is None:
                        continue
                    x0 = float(word["x0"])
                    x1 = float(word["x1"])
                    top = float(word["top"])
                    bottom = float(word["bottom"])
                    size = float(word.get("size") or (bottom - top))
                    in_top_right_margin = x0 >= float(page.width) * 0.70 and top <= min(
                        72.0, float(page.height) * 0.10
                    )
                    safely_small = size <= 10.5 and (bottom - top) <= 13.0
                    light = _is_light_color(word.get("non_stroking_color"))
                    if in_top_right_margin and safely_small and light:
                        matches.setdefault(page_index, []).append((x0, top, x1, bottom))
    except Exception as exc:
        warnings.append(f"Boss watermark auto-check failed: {exc}")
        return {}, warnings
    return matches, warnings


def visually_cover_watermarks(
    source: Path,
    destination: Path,
    boxes_by_page: dict[int, list[tuple[float, float, float, float]]],
) -> int:
    """Cover detected marks with white rectangles while preserving all source pages."""
    try:
        from pypdf import PdfReader, PdfWriter  # type: ignore
        from reportlab.pdfgen import canvas  # type: ignore
    except ImportError as exc:
        raise RuntimeError(f"Boss watermark removal dependency is unavailable: {exc}") from exc

    source_reader = PdfReader(str(source))
    overlay_stream = BytesIO()
    overlay_canvas = canvas.Canvas(overlay_stream, invariant=1, pageCompression=1)
    removed = 0
    for page_index, source_page in enumerate(source_reader.pages):
        width = float(source_page.mediabox.width)
        height = float(source_page.mediabox.height)
        overlay_canvas.setPageSize((width, height))
        overlay_canvas.setFillColorRGB(1.0, 1.0, 1.0)
        for x0, top, x1, bottom in boxes_by_page.get(page_index, []):
            padding = 1.5
            pdf_y = height - bottom
            overlay_canvas.rect(
                max(0.0, x0 - padding),
                max(0.0, pdf_y - padding),
                min(width - x0 + padding, x1 - x0 + padding * 2),
                min(height - pdf_y + padding, bottom - top + padding * 2),
                stroke=0,
                fill=1,
            )
            removed += 1
        overlay_canvas.showPage()
    overlay_canvas.save()
    overlay_stream.seek(0)

    overlay_reader = PdfReader(overlay_stream)
    writer = PdfWriter()
    for page_index, source_page in enumerate(source_reader.pages):
        source_page.merge_page(overlay_reader.pages[page_index], over=True)
        writer.add_page(source_page)
    if source_reader.metadata:
        clean_metadata = {
            str(key): str(value)
            for key, value in source_reader.metadata.items()
            if key and value is not None
        }
        if clean_metadata:
            writer.add_metadata(clean_metadata)
    with destination.open("wb") as output_stream:
        writer.write(output_stream)
    return removed


def prepare_source(
    source: Path, output_dir: Path, remove_boss_watermark: bool
) -> tuple[Path, Path | None, int, list[int], list[str]]:
    """Return a clean working PDF and any temporary path that must be deleted."""
    if not remove_boss_watermark:
        return source, None, 0, [], []
    boxes_by_page, warnings = detect_boss_numeric_watermarks(source)
    if not boxes_by_page:
        return source, None, 0, [], warnings

    with tempfile.NamedTemporaryFile(
        prefix=".boss-watermark-cleaned-",
        suffix=".pdf.tmp",
        dir=output_dir,
        delete=False,
    ) as temp_stream:
        cleaned = Path(temp_stream.name)
    try:
        removed = visually_cover_watermarks(source, cleaned, boxes_by_page)
    except Exception as exc:
        cleaned.unlink(missing_ok=True)
        warnings.append(f"Boss watermark removal failed: {exc}")
        return source, None, 0, [], warnings
    return cleaned, cleaned, removed, [index + 1 for index in sorted(boxes_by_page)], warnings


def allocate_destination(
    source: Path,
    safe_name: str,
    output_dir: Path,
    date_mmdd: str,
    daily_sequence: int | None = None,
) -> tuple[Path, int, bool]:
    """Reuse this candidate's same-content daily file, else allocate the next daily sequence."""
    highest_sequence = 0
    same_name_prefix = f"{safe_name}-TTC-{date_mmdd}"
    for entry in output_dir.glob(f"*-TTC-{date_mmdd}*.pdf"):
        match = STAMPED_OUTPUT.search(entry.name)
        if match is None or match.group("date") != date_mmdd:
            continue
        highest_sequence = max(highest_sequence, int(match.group("sequence")))
        if entry.name.startswith(same_name_prefix) and same_file_content(source, entry):
            return entry, int(match.group("sequence")), True

    if daily_sequence is not None:
        destination = output_dir / f"{safe_name}-TTC-{date_mmdd}{daily_sequence:02d}.pdf"
        return destination, daily_sequence, False

    sequence = highest_sequence + 1
    return output_dir / f"{safe_name}-TTC-{date_mmdd}{sequence:02d}.pdf", sequence, False


def finalize(
    source: Path,
    name: str,
    output_dir: Path,
    overwrite: bool,
    date_mmdd: str,
    daily_sequence: int | None = None,
    remove_boss_watermark: bool = True,
) -> dict[str, object]:
    source = source.expanduser().resolve()
    page_count, warnings = inspect_pdf(source)
    safe_name = candidate_name(name)
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    working_source, cleanup_path, removed, watermark_pages, cleanup_warnings = prepare_source(
        source, output_dir, remove_boss_watermark
    )
    warnings.extend(cleanup_warnings)
    try:
        destination, sequence, reused = allocate_destination(
            working_source, safe_name, output_dir, date_mmdd, daily_sequence
        )

        if destination == working_source:
            reused = True
        elif destination.exists():
            if same_file_content(working_source, destination):
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
                    prefix=f".{safe_name}-TTC-{date_mmdd}{sequence:02d}-",
                    suffix=".pdf.tmp",
                    dir=output_dir,
                    delete=False,
                ) as temp_stream:
                    temp_path = Path(temp_stream.name)
                shutil.copy2(working_source, temp_path)
                os.replace(temp_path, destination)
            finally:
                if temp_path is not None and temp_path.exists():
                    temp_path.unlink()
    finally:
        if cleanup_path is not None:
            cleanup_path.unlink(missing_ok=True)

    final_pages, final_warnings = inspect_pdf(destination)
    warnings.extend(item for item in final_warnings if item not in warnings)
    return {
        "output": str(destination),
        "filename": destination.name,
        "date_mmdd": date_mmdd,
        "daily_sequence": sequence,
        "bytes": destination.stat().st_size,
        "sha256": sha256(destination),
        "pages": final_pages if final_pages is not None else page_count,
        "reused": reused,
        "source_preserved": True,
        "boss_watermark_cleanup": "removed" if removed else "not_detected",
        "boss_watermarks_removed": removed,
        "boss_watermark_pages": watermark_pages,
        "warnings": warnings,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and copy a PDF to <candidate-name>-TTC-MMDDNN.pdf."
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
        "--date-mmdd",
        default=datetime.now().strftime("%m%d"),
        help="Calendar date for the filename in MMDD form; defaults to the local date",
    )
    parser.add_argument(
        "--daily-sequence",
        type=int,
        help="User-specified daily sequence, e.g. 4 produces 04 and overrides automatic allocation",
    )
    parser.add_argument(
        "--keep-boss-watermark",
        action="store_true",
        help="Disable the default conservative removal of a detected Boss top-right numeric watermark",
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
        if args.daily_sequence is not None and args.daily_sequence < 1:
            raise ValueError("--daily-sequence must be a positive integer")
        result = finalize(
            args.source_pdf,
            decoded_name(args),
            args.output_dir,
            args.overwrite,
            validate_date_mmdd(args.date_mmdd),
            args.daily_sequence,
            not args.keep_boss_watermark,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
