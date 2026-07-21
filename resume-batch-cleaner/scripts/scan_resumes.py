#!/usr/bin/env python3
"""Batch classify resume files and optionally delete/move them.

Default mode is dry-run. Use --apply to delete direct rejects and move
ambiguous files into a check folder.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import sys
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree


SUPPORTED_TEXT_SUFFIXES = {".txt", ".md", ".csv", ".json"}
SUPPORTED_DOC_SUFFIXES = {".docx", ".pdf"}
SKIP_DIRS = {"check", "_resume_batch_cleaner_report"}

JUNIOR_COLLEGE_PATTERNS = [
    r"专科",
    r"大专",
    r"高职",
    r"高等职业",
    r"职业技术学院",
    r"大学专科",
    r"专科学历",
    r"associate\s+degree",
    r"junior\s+college",
    r"higher\s+vocational",
]

UPGRADE_PATTERNS = [
    r"专升本",
    r"专接本",
    r"专插本",
    r"专转本",
    r"高起本",
    r"成人本科",
    r"自考本科",
    r"函授本科",
    r"网络教育本科",
    r"开放大学本科",
    r"associate\s+to\s+bachelor",
    r"junior\s+college\s+to\s+bachelor",
    r"college\s+to\s+bachelor",
]

AMBIGUOUS_EDUCATION_PATTERNS = [
    r"继续教育",
    r"成人教育",
    r"自考",
    r"函授",
    r"网络教育",
    r"开放大学",
    r"学历提升",
]


@dataclass
class Decision:
    relative_path: str
    decision: str
    reason: str
    evidence: str
    extraction_status: str
    action: str = "dry-run"


def read_text_file(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_bytes().decode("utf-8", errors="ignore")


def read_docx(path: Path) -> str:
    parts: list[str] = []
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.startswith("word/") and name.endswith(".xml")]
        for name in names:
            try:
                root = ElementTree.fromstring(archive.read(name))
            except ElementTree.ParseError:
                continue
            for node in root.iter():
                if node.text:
                    parts.append(node.text)
    return "\n".join(parts)


def read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except Exception as exc:
            raise RuntimeError("PDF text extraction requires pypdf or PyPDF2") from exc

    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(parts)


def extract_text(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    try:
        if suffix in SUPPORTED_TEXT_SUFFIXES:
            text = read_text_file(path)
        elif suffix == ".docx":
            text = read_docx(path)
        elif suffix == ".pdf":
            text = read_pdf(path)
        else:
            return "", f"unsupported suffix: {suffix or '<none>'}"
    except Exception as exc:
        return "", f"extract failed: {exc}"

    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return "", "empty extracted text"
    return cleaned, "ok"


def load_rules(path: Path | None) -> dict[str, list[str]]:
    rules = {
        "delete_keywords": [],
        "check_keywords": [],
        "bad_school_patterns": [],
        "bad_company_patterns": [],
    }
    if not path:
        return rules
    text = read_text_file(path)

    section_map = {
        "Additional delete keywords": "delete_keywords",
        "Additional check keywords": "check_keywords",
        "Delete when the school evidence clearly matches these disqualifying patterns": "bad_school_patterns",
        "Delete when company evidence clearly matches these disqualifying patterns": "bad_company_patterns",
    }
    current: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        heading = line.strip("# ").strip(":")
        if heading in section_map:
            current = section_map[heading]
            continue
        if line.startswith("##"):
            current = None
            continue
        if current and line.startswith("-"):
            value = line[1:].strip()
            if value:
                rules[current].append(value)
    return rules


def first_match(patterns: Iterable[str], text: str) -> tuple[str, str] | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            start = max(0, match.start() - 40)
            end = min(len(text), match.end() + 40)
            return pattern, text[start:end]
    return None


def classify(path: Path, root: Path, rules: dict[str, list[str]]) -> Decision:
    rel = str(path.relative_to(root))
    text, status = extract_text(path)
    haystack = f"{path.name}\n{text}"

    if status != "ok":
        return Decision(rel, "check", "text extraction unavailable or incomplete", path.name, status)

    for label, patterns in (
        ("junior-college / associate-degree education signal", JUNIOR_COLLEGE_PATTERNS),
        ("college-to-bachelor upgrade signal", UPGRADE_PATTERNS),
        ("local delete keyword", rules["delete_keywords"]),
        ("local disqualifying school pattern", rules["bad_school_patterns"]),
        ("local disqualifying company pattern", rules["bad_company_patterns"]),
    ):
        matched = first_match(patterns, haystack)
        if matched:
            pattern, snippet = matched
            return Decision(rel, "delete", f"{label}: {pattern}", snippet, status)

    matched = first_match(AMBIGUOUS_EDUCATION_PATTERNS + rules["check_keywords"], haystack)
    if matched:
        pattern, snippet = matched
        return Decision(rel, "check", f"ambiguous signal: {pattern}", snippet, status)

    return Decision(rel, "keep", "no delete/check signal found", "", status)


def iter_resume_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        parts = {part.lower() for part in path.relative_to(root).parts[:-1]}
        if parts.intersection(SKIP_DIRS):
            continue
        yield path


def unique_destination(check_dir: Path, relative_path: str) -> Path:
    destination = check_dir / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        return destination
    stem = destination.stem
    suffix = destination.suffix
    parent = destination.parent
    index = 2
    while True:
        candidate = parent / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def apply_actions(root: Path, decisions: list[Decision]) -> None:
    check_dir = root / "check"
    for decision in decisions:
        source = root / decision.relative_path
        if decision.decision == "delete":
            try:
                source.unlink()
                decision.action = "deleted"
            except Exception as exc:
                decision.action = f"delete failed: {exc}"
        elif decision.decision == "check":
            try:
                target = unique_destination(check_dir, decision.relative_path)
                shutil.move(str(source), str(target))
                decision.action = f"moved to {target.relative_to(root)}"
            except Exception as exc:
                decision.action = f"move failed: {exc}"
        else:
            decision.action = "kept"


def write_reports(root: Path, decisions: list[Decision], apply: bool) -> Path:
    report_dir = root / "_resume_batch_cleaner_report"
    report_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    stem = f"{timestamp}-{'apply' if apply else 'dry-run'}"

    json_path = report_dir / f"{stem}.json"
    csv_path = report_dir / f"{stem}.csv"
    md_path = report_dir / f"{stem}.md"

    data = [asdict(decision) for decision in decisions]
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(data[0].keys()) if data else list(Decision("", "", "", "", "").__dict__.keys()))
        writer.writeheader()
        writer.writerows(data)

    counts = {key: sum(1 for item in decisions if item.decision == key) for key in ("delete", "check", "keep")}
    lines = [
        "# Resume Batch Cleaner Report",
        "",
        f"- Mode: {'apply' if apply else 'dry-run'}",
        f"- Delete: {counts['delete']}",
        f"- Check: {counts['check']}",
        f"- Keep: {counts['keep']}",
        "",
        "| Decision | File | Reason | Evidence | Action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for decision in decisions:
        evidence = decision.evidence.replace("|", "\\|")[:180]
        reason = decision.reason.replace("|", "\\|")
        lines.append(f"| {decision.decision} | {decision.relative_path} | {reason} | {evidence} | {decision.action} |")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch classify resume files for delete/check/keep actions.")
    parser.add_argument("resume_folder", help="Folder containing resume files")
    parser.add_argument("--rules", help="Optional local screening rules markdown file")
    parser.add_argument("--apply", action="store_true", help="Delete direct rejects and move ambiguous files to check/")
    args = parser.parse_args()

    root = Path(args.resume_folder).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"Resume folder does not exist or is not a directory: {root}", file=sys.stderr)
        return 2

    rules_path = Path(args.rules).expanduser().resolve() if args.rules else None
    if rules_path and not rules_path.exists():
        print(f"Rules file does not exist: {rules_path}", file=sys.stderr)
        return 2

    rules = load_rules(rules_path)
    decisions = [classify(path, root, rules) for path in iter_resume_files(root)]
    if args.apply:
        apply_actions(root, decisions)
    report = write_reports(root, decisions, args.apply)

    counts = {key: sum(1 for item in decisions if item.decision == key) for key in ("delete", "check", "keep")}
    print(f"Report: {report}")
    print(f"delete={counts['delete']} check={counts['check']} keep={counts['keep']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
