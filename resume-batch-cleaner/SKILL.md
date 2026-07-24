---
name: resume-batch-cleaner
description: "Batch-screen, deduplicate, score, rank, rename, and package technical resumes from one or more folders. Use when the user wants to keep technical candidates only, hard-reject any resume containing junior-college/higher-vocational, college-to-bachelor upgrade, or private-bachelor education, rank survivors with an auditable 100-point technical rubric, name files as rank-name-expected-location, and receive a final ZIP plus score workbook without changing source files."
---

# Resume Batch Cleaner

Use this skill for multi-file technical-resume screening and ranking. Treat every source folder as read-only unless the user separately and explicitly asks to mutate it.

## Required Workflow

1. Resolve all input folders and a separate output directory.
   - Accept repeated input folders.
   - Never use an input folder as the output folder.
   - Inventory supported files before screening and record counts by folder and extension.
2. Read `references/decision-policy.md` and `references/technical-ranking-policy.md` completely.
3. Obtain a current authoritative institution list when Chinese institution ownership or level matters.
   - Prefer an official Ministry of Education list.
   - Keep the downloaded source and converted lookup table in a temporary working directory.
   - Treat historical independent-college/private-bachelor names conservatively and review their historical status when needed.
4. Run `scripts/process_technical_resumes.py` without `--package` first.
5. Review every `review` case and obvious classifier boundary case.
   - Render or visually inspect image-only and layout-dependent resumes.
   - Use the resume body, not the enclosing folder or filename, to determine the actual role.
   - Confirm the resume-internal name and only explicit expected-location evidence.
   - Store candidate-specific corrections in a local overrides JSON outside this skill directory, for example `.hj-skill-local/resume-batch-cleaner/technical-resume-overrides.local.json`.
6. Reapply reviewed overrides, deduplicate again, and require zero unresolved `review` records before final packaging.
7. Score and sort retained candidates with the 100-point rubric in `references/technical-ranking-policy.md`.
8. Copy retained resumes into a new output folder and rename them:
   - `001-姓名-期望地点.ext`
   - Use the name printed inside the resume. Use a resume-displayed alias only when no other name is present.
   - Use `未提及` when no explicit expected location is stated. Do not infer it from current city, employer city, address, school city, or source-folder name.
9. Create an auditable `.xlsx` workbook containing:
   - statistics by input batch;
   - retained ranking and all score components;
   - excluded and duplicate records with reasons;
   - scoring rules and hard filters.
10. Create one final ZIP containing the renamed retained resumes, workbook, manifest, and a short rules/result note.
11. Verify file counts, sequential numbering, filename format, copied-file hashes, archive entries, formulas, and a visual render of every workbook sheet.

## Hard Screening Rules

- Keep only roles with clear engineering, coding, algorithm, experiment, testing, hardware, structural, materials-R&D, or technical-art implementation evidence.
- Exclude legal, marketing, sales, BD, investment, operations, product, pure visual/industrial/UX design, and pure project-management roles.
- Technical-art roles may be kept when they contain engine, rendering, shader, scripting, pipeline, simulation, or tool-development work.
- Technical program/project managers are excluded under the strict hands-on policy unless the user explicitly broadens the role boundary.
- Hard-reject the resume when any education segment contains:
  - junior college, higher vocational college, associate degree, adult junior college, or equivalent;
  - college-to-bachelor upgrade paths such as 专升本、专接本、专插本、高起本;
  - a private Chinese bachelor's institution or historical independent-college bachelor's program.
- A later public bachelor, master, or doctorate never overrides a disqualifying earlier education segment.
- If the complete education chain cannot be reliably verified, do not put the candidate in the final retained package under conservative mode; record the reason in the audit sheet.

## Evidence Rules

- Role classification must use resume-body evidence. Filenames and folder names are hints only.
- Education classification must inspect the full education section and relevant history, not only the highest degree.
- Do not treat text such as “十大专利”“专科专病”“最高职级” as junior-college evidence.
- Expected location must be tied to explicit labels such as `期望城市`, `意向城市`, `期望地点`, or an unambiguous job-intention line.
- Preserve the original extension and contents of every copied resume.
- Deduplicate by exact hash first, then by strong contact identifiers such as email or phone. Keep the most complete usable copy.

## Primary Script

Analysis pass:

```bash
python scripts/process_technical_resumes.py \
  --input "path/to/batch-1" \
  --input "path/to/batch-2" \
  --output-dir "path/to/output" \
  --institution-csv "path/to/institutions.csv" \
  --overrides "path/to/technical-resume-overrides.local.json"
```

Package after review:

```bash
python scripts/process_technical_resumes.py \
  --input "path/to/batch-1" \
  --input "path/to/batch-2" \
  --output-dir "path/to/output" \
  --institution-csv "path/to/institutions.csv" \
  --overrides "path/to/technical-resume-overrides.local.json" \
  --package
```

Supported inputs include PDF, DOCX, legacy DOC through Word conversion when available, common images, TXT, and Markdown. Unreadable or image-only files require visual review.

## Privacy and Local Data

- Do not store resumes, candidate details, contact information, client blacklists, or candidate-specific overrides inside this skill.
- Keep downloaded institution lists, extracted text, rendered previews, overrides, workbooks, and packages in the task workspace or temporary output area.
- Do not browse for candidate personal information; judge only the supplied resumes and authoritative institution references.

## Reference Files

- `references/decision-policy.md`: hard-screen and review decision policy.
- `references/technical-ranking-policy.md`: score weights, anchors, tie-breaks, and naming rules.
- `scripts/process_technical_resumes.py`: multi-folder extraction, screening, scoring, deduplication, and packaging pipeline.
- `scripts/scan_resumes.py`: legacy single-folder dry-run scanner; use only when that narrower workflow is explicitly needed.
