---
name: elite-tech-resume-shortlist
description: "Batch-screen mixed resume folders into two auditable technical-or-product talent tiers: elite-school candidates and a conservative expanded public-university tier. Verify large-company employment, the requested role family, the complete education chain, and—only when explicitly requested—an age ceiling from stated age or birth-date evidence. Use for PDF/DOCX/DOC/image inventory, hash deduplication, extraction, manual review, strict education exclusions, and spreadsheet delivery."
---

# Elite Technical and Product Resume Shortlist

Build an auditable shortlist from resume folders. Treat every criterion as evidence-based: school names, company names, technical keywords, and age signals do not qualify a candidate unless their surrounding resume context proves the claim.

## Required references

Read both files before screening:

- [references/screening-policy.md](references/screening-policy.md) for hard decisions and false-positive controls.
- [references/output-schema.md](references/output-schema.md) before creating the deliverable.

## Workflow

### 1. Confirm the task-local policy

Record:

- Tier 1 domestic and overseas school definitions;
- the explicit Tier 2 public-university whitelist;
- the large-company scope;
- the allowed role families: technical, product, or both;
- whether technical internships count;
- whether the user explicitly requested an age ceiling and the as-of date;
- whether incomplete education chains are excluded or routed to review;
- output format and whether ranking is requested.

If the user gives a strict rule, it overrides defaults. Do not weaken “any education segment” into “highest degree only.”

### 2. Inventory without modifying sources

Run:

```powershell
python scripts/inventory_resumes.py `
  --input "D:\resumes\batch-1" `
  --input "D:\resumes\batch-2" `
  --output "work\elite-tech-resume-shortlist"
```

The script hashes files, removes exact duplicates from analysis, extracts PDF/DOCX text when possible, and flags legacy DOC/images/low-text files for manual review. Keep generated text and audit data under `work/` or another private ignored directory. Never commit resumes, extracted text, contact details, or candidate outputs to a skill repository.

### 3. Establish authoritative school evidence

Browse current primary sources because institution status and rankings change:

- use the Ministry of Education or relevant national authority for Chinese institution names, levels, and private/public status;
- use the official historical 211 list;
- use the current Double First-Class list for that classification;
- use the ranking publisher's current official table when overseas elite is ranking-based.

Store thresholds, the complete Tier 2 whitelist, and source URLs in Methodology. Match longest normalized institution names first. Never let a substring qualify another school: `杭州电子科技大学` is not `电子科技大学`.

### 4. Apply education-chain hard screening

Inspect the complete visible education timeline, not only the highest degree. Exclude when any segment shows:

- junior college, higher vocational, associate degree, or equivalent;
- college-to-bachelor upgrading, including 专升本、专接本、专插本、高起本 or equivalent;
- a private Chinese bachelor's institution or historical independent college under the user's policy;
- an education chain too incomplete to verify under strict mode.

A later 985/211/master/doctorate never cancels an earlier disqualifying segment. Exchange study, certificates, bootcamps, and short courses are not degrees; label them separately.

### 5. Apply the age rule only from explicit evidence

When the user explicitly requests an age ceiling, record an as-of date and require:

- a stated age in the resume; or
- a stated date, month, or year of birth.

Calculate age on the as-of date. “Under 40” means the candidate has not reached the 40th birthday. Do not infer age from graduation year, work history, appearance, seniority, or name. Route candidates without explicit age evidence to `age-unverifiable`; do not mix them into either selected table. Age can be a protected characteristic, so disclose the user-requested rule and avoid collecting more personal data than needed.

### 6. Assign the school tier without overlap

- `tier-1-elite`: at least one verified 985/211 degree or a task-defined overseas-elite degree.
- `tier-2-expanded`: not Tier 1, but at least one degree from the explicit task-local whitelist of current Double First-Class non-985/211 institutions or reputable public first-tier universities.

Tier 2 is a conservative whitelist, not every public undergraduate institution. Record the exact whitelist in Methodology. Both tiers must pass the same age, education-chain, company-context, and technical-role rules.

### 7. Verify large-company experience in context

Count a company only when the work or internship section proves actual employment in an allowed role family. Capture:

- company and employing entity;
- formal employment versus internship;
- dates and role;
- a short responsibility excerpt proving the role family.

Do not count a company mentioned only as a cloud provider, tool, client, customer, competitor, certification, contest, research partner, model source, API, email domain, or project environment.

Default: include internship-only candidates in a separate clearly labeled tier. Do not mix them silently with formal employees.

### 8. Verify the requested role family

Classify every selected candidate as `technical` or `product`; do not infer the family from a keyword alone.

For `technical`, include engineering, algorithm, research, data engineering/science, technical testing/quality, hardware/SoC, infrastructure, security engineering, and technical architecture when the resume proves hands-on implementation.

For `product`, require a product-manager, product-owner, or product-lead mainline with concrete ownership of product definition and outcomes—for example roadmaps, requirements, user or market discovery, product design, launches, experimentation, metrics, iteration, or platform/application ownership.

Exclude strategy, operations, marketing, investment, sales/BD, legal, finance, pure design, PMO/project management, delivery coordination, and presales/business-expansion mainlines unless the task explicitly requests them. A title containing “product” does not qualify if the work is actually product operations, sales enablement, project delivery, or marketing. For mixed titles:

- require code, systems, models, experiments, test automation, hardware, or other concrete technical artifacts;
- distinguish data science/engineering from business analysis;
- distinguish test development and platform engineering from manual QA;
- distinguish a hands-on technical lead from a people/process-only manager.
- distinguish product ownership from project management, operations, and business analysis;
- record only the large-company role that actually belongs to an allowed family.

### 9. Resolve every exception manually

Visually inspect all image resumes, scanned PDFs, legacy DOC files, garbled extraction, suspicious filename/body mismatches, and ambiguous schools. Use WPS/Word extraction or rendering when available.

Every unique resume must end as one of:

- `tier-1-selected-formal`
- `tier-1-selected-internship-only`
- `tier-2-selected-formal`
- `tier-2-selected-internship-only`
- `age-unverifiable`
- `role-family-unverifiable`
- `excluded`
- `duplicate`

Do not leave unresolved generic `review` rows in the final output.

### 10. Canonicalize and audit

- Prefer the name inside the resume; retain the filename alias separately.
- Keep the most complete readable copy of a duplicate.
- Replace automated school/company hits with manually verified canonical labels.
- Record a concise reason for every near-match exclusion.
- Do not expose phone numbers, email addresses, ID numbers, photographs, or other unnecessary personal data in the shortlist.

### 11. Produce the deliverable

For Excel output, use the installed spreadsheet skill and create:

1. `Summary`
2. `Table 1 - Elite`
3. `Table 2 - Expanded`
4. `Pending or Excluded`
5. `Methodology`

Keep the two selected tiers mutually exclusive. Include a role-family column and report technical/product counts separately. Separate internship-only candidates visually. Include source batch and source filename so the recruiter can find the original resume. Do not embed extracted resume text.

### 12. Validate before handoff

Check:

- each tier's count equals its table rows;
- no candidate appears in both selected tables;
- selected rows have unique source hashes or files;
- every selected row has age, school, education-chain, company-context, and allowed-role evidence;
- every selected candidate is below the requested age ceiling on the recorded as-of date;
- no selected row contains a hard education disqualifier;
- no famous company, school, or role family is supported only by a keyword hit;
- all exception files were manually resolved;
- workbook formulas contain no spreadsheet errors;
- rendered previews are readable.

Report total files, unique resumes, duplicates, Tier 1 selections, Tier 2 selections, technical/product counts within each tier, age-unverifiable cases, internship-only selections, and important conservative exclusions.
