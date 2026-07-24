#!/usr/bin/env python3
"""Render a daily recruiting feedback review from normalized JSONL records."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import date as local_date
from pathlib import Path


JUDGMENT_LABELS = {
    "hit": "命中",
    "partial": "部分命中",
    "miss": "失配",
    "pending": "待判断",
}
CONFIDENCE_LABELS = {"high": "高", "medium": "中", "low": "低"}
GENERALIZABILITY_LABELS = {
    "candidate-specific": "人选个案",
    "company-role-specific": "公司/岗位",
    "mechanism-general": "通用机制",
}
RULE_ACTION_LABELS = {
    "apply": "落规则",
    "observe": "继续观察",
    "no_change": "不改规则",
}
ALLOWED_ISSUE_TYPES = {
    "none",
    "false-positive",
    "false-negative",
    "role-understanding",
    "depth-or-level",
    "hard-constraint",
    "evidence-gap",
    "preference-mismatch",
    "timing-or-process",
    "data-quality",
    "external-factor",
    "pending",
}
TABLE_COLUMNS = [
    ("date", "日期"),
    ("company", "公司"),
    ("role", "岗位"),
    ("candidate", "候选人"),
    ("recommendation_display", "原推荐 / 分数"),
    ("feedback_display", "实际反馈 / 结果"),
    ("judgment_display", "机制判断"),
    ("issue_type", "主误差类型"),
    ("mechanism_note", "机制说明"),
    ("generalizability_display", "泛化范围"),
    ("generalizable_lesson", "可复用结论"),
    ("confidence_display", "置信度"),
    ("rule_action_display", "规则动作"),
    ("next_action", "下一步"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="UTF-8 JSONL input")
    parser.add_argument(
        "--date",
        default=local_date.today().isoformat(),
        help="Review date in YYYY-MM-DD format",
    )
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace existing generated outputs",
    )
    return parser.parse_args()


def clean(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value).strip()


def display(value: str) -> str:
    return value if value else "待确认"


def inline(value: str) -> str:
    return display(value).replace("\r", " ").replace("\n", " ").strip()


def md_cell(value: str) -> str:
    return inline(value).replace("|", "\\|")


def load_records(path: Path, review_date: str) -> list[dict[str, str]]:
    if not path.is_file():
        raise ValueError(f"Input file not found: {path}")

    records: list[dict[str, str]] = []
    errors: list[str] = []

    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if not raw_line.strip():
                continue
            try:
                parsed = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_number}: invalid JSON ({exc.msg})")
                continue
            if not isinstance(parsed, dict):
                errors.append(f"line {line_number}: expected a JSON object")
                continue

            record = {key: clean(value) for key, value in parsed.items()}
            record_date = record.get("date") or review_date
            if record_date != review_date:
                continue
            record["date"] = record_date
            if not (record.get("company") or record.get("role") or record.get("candidate")):
                errors.append(
                    f"line {line_number}: company, role, and candidate cannot all be blank"
                )
                continue

            judgment = record.get("mechanism_judgment") or "pending"
            if judgment not in JUDGMENT_LABELS:
                errors.append(
                    f"line {line_number}: invalid mechanism_judgment '{judgment}'"
                )
                continue
            record["mechanism_judgment"] = judgment

            issue_type = record.get("issue_type") or (
                "none" if judgment == "hit" else "pending"
            )
            if issue_type not in ALLOWED_ISSUE_TYPES:
                errors.append(f"line {line_number}: invalid issue_type '{issue_type}'")
                continue
            record["issue_type"] = issue_type

            confidence = record.get("confidence") or "low"
            if confidence not in CONFIDENCE_LABELS:
                errors.append(f"line {line_number}: invalid confidence '{confidence}'")
                continue
            record["confidence"] = confidence

            scope = record.get("generalizability") or "candidate-specific"
            if scope not in GENERALIZABILITY_LABELS:
                errors.append(
                    f"line {line_number}: invalid generalizability '{scope}'"
                )
                continue
            record["generalizability"] = scope

            action = record.get("rule_action") or "no_change"
            if action not in RULE_ACTION_LABELS:
                errors.append(f"line {line_number}: invalid rule_action '{action}'")
                continue
            record["rule_action"] = action
            records.append(record)

    if errors:
        raise ValueError("\n".join(errors))
    if not records:
        raise ValueError(f"No records found for {review_date}")
    return records


def enrich(record: dict[str, str]) -> dict[str, str]:
    recommendation_parts = [
        part
        for part in (
            record.get("original_recommendation", ""),
            record.get("original_score", ""),
        )
        if part
    ]
    feedback_parts = [
        part
        for part in (record.get("feedback", ""), record.get("outcome", ""))
        if part
    ]
    enriched = dict(record)
    enriched["recommendation_display"] = " / ".join(recommendation_parts)
    enriched["feedback_display"] = " / ".join(feedback_parts)
    enriched["judgment_display"] = JUDGMENT_LABELS[record["mechanism_judgment"]]
    enriched["confidence_display"] = CONFIDENCE_LABELS[record["confidence"]]
    enriched["generalizability_display"] = GENERALIZABILITY_LABELS[
        record["generalizability"]
    ]
    enriched["rule_action_display"] = RULE_ACTION_LABELS[record["rule_action"]]
    return enriched


def percent(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "暂无有效样本"
    return f"{numerator / denominator:.1%}"


def unique_nonempty(records: list[dict[str, str]], key: str) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for record in records:
        value = record.get(key, "")
        if value and value not in seen:
            seen.add(value)
            values.append(value)
    return values


def render_review(records: list[dict[str, str]], review_date: str) -> str:
    counts = Counter(record["mechanism_judgment"] for record in records)
    decided = counts["hit"] + counts["partial"] + counts["miss"]
    lines = [
        f"# 每日匹配反馈复盘｜{review_date}",
        "",
        "## 今日概览",
        "",
        f"- 反馈事件：{len(records)} 条",
        f"- 有结论事件：{decided} 条",
        (
            f"- 机制判断：命中 {counts['hit']}｜部分命中 {counts['partial']}"
            f"｜失配 {counts['miss']}｜待判断 {counts['pending']}"
        ),
        f"- 严格命中率：{percent(counts['hit'], decided)}",
        (
            "- 方向有效率："
            f"{percent(counts['hit'] + counts['partial'], decided)}"
        ),
    ]
    if decided < 5:
        lines.append("- 样本提示：有效反馈少于 5 条，仅作方向性观察，不视为稳定指标。")

    lines.extend(["", "## 公司与岗位补充", ""])
    grouped: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for record in records:
        grouped[display(record.get("company", ""))][
            display(record.get("role", ""))
        ].append(record)

    for company, roles in grouped.items():
        lines.extend([f"### {company}", ""])
        for role, role_records in roles.items():
            lines.extend([f"#### {role}", ""])
            supplements = unique_nonempty(role_records, "role_supplement")
            if supplements:
                lines.append("岗位补充：")
                lines.append("")
                for item in supplements:
                    lines.append(f"- {inline(item)}")
            else:
                lines.append("- 岗位补充：无新增已确认内容")

            lines.extend(["", "反馈摘要：", ""])
            for record in role_records:
                candidate = display(record.get("candidate", ""))
                feedback = record.get("feedback") or "尚无明确反馈"
                source = record.get("feedback_source") or "来源待确认"
                outcome = record.get("outcome")
                suffix = f"；结果：{inline(outcome)}" if outcome else ""
                lines.append(
                    f"- {candidate}：{inline(feedback)}（{inline(source)}{suffix}）"
                )
            lines.append("")

    lines.extend(["## 对匹配机制的反馈", "", "### 已确认可落地调整", ""])
    applied = [
        record
        for record in records
        if record["rule_action"] == "apply"
        and record["confidence"] == "high"
        and record["generalizability"] != "candidate-specific"
    ]
    if applied:
        for record in applied:
            lesson = record.get("generalizable_lesson") or record.get(
                "mechanism_note", ""
            )
            lines.append(
                f"- [{display(record.get('company', ''))}｜"
                f"{display(record.get('role', ''))}] {inline(lesson)}"
            )
    else:
        lines.append("- 今日没有达到直接落规则标准的新增结论。")

    lines.extend(["", "### 继续观察", ""])
    observed = [
        record
        for record in records
        if record["rule_action"] == "observe"
        or (
            record.get("generalizable_lesson")
            and record not in applied
            and record["generalizability"] != "candidate-specific"
        )
    ]
    if observed:
        for record in observed:
            lesson = record.get("generalizable_lesson") or record.get(
                "mechanism_note", ""
            )
            lines.append(
                f"- [{display(record.get('company', ''))}｜"
                f"{display(record.get('role', ''))}] {inline(lesson)}"
            )
    else:
        lines.append("- 暂无需要累计样本的新增观察。")

    lines.extend(["", "### 仅解释个案、不改规则", ""])
    individual = [
        record
        for record in records
        if record["generalizability"] == "candidate-specific"
        or record["rule_action"] == "no_change"
    ]
    if individual:
        for record in individual:
            note = record.get("mechanism_note") or record.get("feedback") or "待补充"
            lines.append(
                f"- {display(record.get('candidate', ''))}：{inline(note)}"
            )
    else:
        lines.append("- 无。")

    lines.extend(["", "## 待补信息与下一步", ""])
    next_steps = unique_nonempty(records, "next_action")
    pending = [
        record
        for record in records
        if record["mechanism_judgment"] == "pending" and not record.get("next_action")
    ]
    for item in next_steps:
        lines.append(f"- {inline(item)}")
    for record in pending:
        lines.append(
            f"- 补充 {display(record.get('company', ''))}｜"
            f"{display(record.get('role', ''))}｜"
            f"{display(record.get('candidate', ''))} 的明确下游反馈。"
        )
    if not next_steps and not pending:
        lines.append("- 今日无新增待办。")

    return "\n".join(lines).rstrip() + "\n"


def render_markdown_table(records: list[dict[str, str]], review_date: str) -> str:
    headers = [label for _, label in TABLE_COLUMNS]
    lines = [
        f"# 匹配机制反馈表｜{review_date}",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for record in records:
        lines.append(
            "| "
            + " | ".join(md_cell(record.get(key, "")) for key, _ in TABLE_COLUMNS)
            + " |"
        )
    return "\n".join(lines) + "\n"


def ensure_writable(paths: list[Path], force: bool) -> None:
    existing = [path for path in paths if path.exists()]
    if existing and not force:
        joined = "\n".join(str(path) for path in existing)
        raise ValueError(
            "Refusing to replace existing output(s) without --force:\n" + joined
        )


def write_csv(path: Path, records: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[label for _, label in TABLE_COLUMNS],
            extrasaction="ignore",
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    label: inline(record.get(key, ""))
                    for key, label in TABLE_COLUMNS
                }
            )


def main() -> int:
    args = parse_args()
    try:
        records = [enrich(record) for record in load_records(args.input, args.date)]
        args.output_dir.mkdir(parents=True, exist_ok=True)
        review_path = args.output_dir / f"daily-matching-review.{args.date}.md"
        table_path = args.output_dir / f"matching-feedback-table.{args.date}.md"
        csv_path = args.output_dir / f"matching-feedback-table.{args.date}.csv"
        ensure_writable([review_path, table_path, csv_path], args.force)
        review_path.write_text(
            render_review(records, args.date), encoding="utf-8"
        )
        table_path.write_text(
            render_markdown_table(records, args.date), encoding="utf-8"
        )
        write_csv(csv_path, records)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {review_path}")
    print(f"Wrote {table_path}")
    print(f"Wrote {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
