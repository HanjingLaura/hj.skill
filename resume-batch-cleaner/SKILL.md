---
name: resume-batch-cleaner
description: "Batch-clean a folder of resume files by strict education and background screening rules. Use when the user provides a directory of resumes and wants Codex to delete files with any junior-college or associate-degree education segment, rigorously catch college-to-bachelor upgrade paths, delete clearly weak school/company-background matches under local rules, and move ambiguous or risky cases into a check folder with an audit log."
---

# Resume Batch Cleaner

## Core Workflow

1. Resolve the target resume folder from the user's message. If no folder is provided, ask for it.
2. Resolve local screening rules.
   - Prefer a user-provided rules file.
   - Otherwise look for `.hj-skill-local/resume-batch-cleaner/screening-rules.local.md` under the current workspace.
   - If no local rules exist, read `references/screening-rules.template.md` and ask for the missing school/company background rules before judging "obviously weak background."
3. Read `references/decision-policy.md` before making final file actions.
4. Run `scripts/scan_resumes.py <resume-folder> --rules <rules-file>` first without `--apply` to produce a dry-run report.
5. Review the dry-run categories:
   - `delete`: any education segment is junior college / associate degree, college-to-bachelor upgrade is present, or local rules mark school/company background as clearly disqualifying.
   - `check`: evidence is ambiguous, text extraction is weak, school/company background is uncertain, or the file needs human review.
   - `keep`: no disqualifying signal found and no unresolved ambiguity.
6. If the user explicitly asked to clean/delete the folder, run the script again with `--apply`.
   - Delete only files in the `delete` category.
   - Move `check` files into `<resume-folder>/check/`.
   - Keep all other files in place.
7. Return a concise summary with counts, report path, deleted filenames, check filenames, and any files that could not be read.

## Screening Policy

- Enforce the education rule strictly: if any education segment is junior college / associate degree, mark `delete`, even when the candidate later completed a bachelor's, master's, or PhD.
- Treat explicit college-to-bachelor upgrade signals as `delete`, including phrases such as "zhuan sheng ben", "junior college to bachelor", "associate to bachelor", and Chinese equivalents.
- Do not delete for vague education text unless a junior-college or upgrade signal is explicit. Move vague cases to `check`.
- Use local rules for school and company background. Public skill files must not contain private blacklists, client-specific school lists, or candidate data.
- Delete for school/company background only when the local rules clearly mark the evidence as disqualifying.
- Move to `check` when school/company quality is unclear, extraction is incomplete, file format is unsupported, or the judgment depends on context.
- Never recurse into an existing `check/` folder when scanning.

## File Handling Rules

- Operate only inside the user-provided resume folder.
- Create `check/` inside the resume folder when needed.
- Write audit files into `<resume-folder>/_resume_batch_cleaner_report/`.
- Preserve folder structure when moving ambiguous files to `check/` if files come from subdirectories.
- Do not delete directories.
- Do not modify resume file contents.
- If file deletion fails, record the failure in the report and leave the file untouched.

## Script Usage

Dry run:

```bash
python scripts/scan_resumes.py "path/to/resume-folder" --rules "path/to/screening-rules.local.md"
```

Apply actions:

```bash
python scripts/scan_resumes.py "path/to/resume-folder" --rules "path/to/screening-rules.local.md" --apply
```

The script supports `.txt`, `.md`, `.docx`, `.pdf`, and common image/document filenames. Text extraction is best-effort. Unsupported or unreadable files go to `check`.

## Reference Files

- `references/screening-rules.template.md`: Local rules template for school/company background and ambiguous cases.
- `references/decision-policy.md`: Decision policy for delete/check/keep classification.
- `scripts/scan_resumes.py`: Batch scanner and optional file-action script.
