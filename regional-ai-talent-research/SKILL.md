---
name: regional-ai-talent-research
description: Deeply research public AI, computer science, and robotics talent and public professional contact details across universities in a user-selected country or region, then deliver a source-backed, deduplicated, review-ready Excel workbook. Use when the user wants university/lab/faculty/PhD/postdoc/alumni discovery, verified public emails, Chinese-background evidence labels, paper-author expansion, school-by-school coverage, or the same sourcing workflow repeated with only the target region or school scope changed. Never use it to send outreach.
---

# Regional AI Talent Research

Build a public-evidence talent dataset and a review-ready Excel workbook. Treat only `target_region`, `school_scope`, `output_path`, and the run date as variable inputs. Keep the research depth, evidence rules, statuses, workbook structure, and completion gates fixed unless the user explicitly changes them.

## Start every run

1. Resolve:
   - `target_region`: required; infer it only when explicit in the request.
   - `school_scope`: optional explicit list or discovery rules. If omitted, discover eligible schools using the fixed protocol.
   - `output_path`: use the user's path; otherwise use `Desktop/<target_region>高校_AI人才及联系方式_<YYYY-MM-DD>.xlsx`.
   - `as_of_date`: current local date unless the user supplies another date.
2. Create a resumable working dataset matching [references/data-contract.md](references/data-contract.md).
3. Read and follow [references/research-protocol.md](references/research-protocol.md) completely before searching.
4. Load and follow the spreadsheet skill before producing or visually checking the `.xlsx`.

Ask only for a missing `target_region` when it cannot be inferred safely. An explicit school list narrows the initial queue but does not remove author-expansion or alumni-tracing requirements.

## Fixed operating rules

- Search public professional and academic sources only. Do not send email, message anyone, execute outreach, or access private data.
- Never construct or guess an email address from an institutional pattern.
- Keep faculty, researchers, fellows, postdocs, doctoral students, high-value master's students, engineers, alumni, former members, and departed researchers.
- Track a departed person's current institution, current public email, current homepage, and latest work while retaining the original school association.
- Do not score talent quality. Perform identity resolution, evidence capture, contact verification, and coverage tracking only.
- Use current web research for changing facts such as rankings, memberships, staff status, affiliations, and contact details. Prefer official sources and preserve public URLs.
- Do not infer nationality or ethnicity from a name, photograph, or appearance. Use only the five background labels in the protocol.
- Keep one canonical `person_id` globally. Render the same person in every associated school sheet without counting that person more than once globally.
- Do not claim a school or project complete until the protocol's stop conditions and QA gates pass. Mark inaccessible or ambiguous material explicitly.

## Execute the research

Work school by school with a persistent queue:

1. Select and justify schools.
2. Inspect relevant schools, departments, institutes, centres, labs, people directories, student pages, alumni pages, publications, projects, contact pages, and join pages.
3. Resolve every relevant person through official profiles, personal sites, CVs, scholarly identities, code profiles, papers, projects, and current institution pages.
4. Expand through recent high-value paper author networks.
5. Trace alumni and former members to their current destinations.
6. Run expansion rounds until two consecutive rounds add no new relevant people.
7. Record query/coverage state and blocked pages in the dataset as work proceeds.

Use the exact source priority, status vocabularies, confidence rules, deduplication logic, and completion gates in [references/research-protocol.md](references/research-protocol.md).

## Build and verify the workbook

Maintain the canonical JSON dataset throughout the run. Use the Node.js runtime and `node_modules` path returned by `load_workspace_dependencies`. In a writable run directory, create a `node_modules` junction to that exact dependency path, copy the single builder there, and run:

```powershell
Copy-Item <skill-dir>\scripts\build_workbook.mjs <run-dir>\build_workbook.mjs
<bundled-node> <run-dir>\build_workbook.mjs <dataset.json> --output <output.xlsx> --preview-dir <run-dir>\previews
```

Do not install dependencies or substitute another spreadsheet library. The builder rejects missing email provenance, invalid fixed statuses, unknown schools, duplicate IDs, missing minimum traceability, incomplete school gates marked as complete, and schema drift. It writes:

- `总览`
- `学校覆盖`
- `跨校去重`
- `待复查`
- one consistently structured sheet per included school

After building:

1. Review the builder's round-trip workbook inspection and formula-error scan.
2. Open and visually inspect every PNG in `preview-dir`. Check clipping, unreadable widths, broken URLs, blank required cells, and inconsistent headers.
3. Correct the dataset or builder inputs, rebuild, and repeat until all checks pass.
4. Save only the final workbook to the requested destination. Keep working JSON/checkpoints in the workspace unless the user asks for them.

## Report completion

State the output path, school count, global unique-person count, public-email count by confidence, missing-email count, review-queue count, and any schools or pages that remain explicitly blocked. Never describe partial coverage as complete.
