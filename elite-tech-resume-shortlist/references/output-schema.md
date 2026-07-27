# Output schema

## Summary

Include:

- files scanned;
- unique resumes;
- exact duplicates;
- extraction failures and manual-review files;
- Tier 1 formal or formal-plus-internship candidates;
- Tier 1 internship-only candidates;
- Tier 2 formal or formal-plus-internship candidates;
- Tier 2 internship-only candidates;
- age-unverifiable or boundary-unverifiable candidates;
- exclusions by hard reason.

## Table 1 - Elite

Contains only candidates whose qualifying school is 985/211 or task-defined overseas elite.

## Table 2 - Expanded

Contains only candidates who are not in Table 1 and whose qualifying school is on the disclosed Double First-Class non-985/211 or reputable-public-first-tier whitelist.

The two selected tables use the same required columns:

| Column | Meaning |
| --- | --- |
| Candidate | Resume-internal name |
| Resume alias | Filename nickname when different |
| Technical category | Backend, algorithm, data, test development, SoC, etc. |
| Original role | Role inferred from source filename or body |
| Relevant years | Resume-supported relevant experience |
| Age evidence | Stated age or stated birth date or year |
| Age on as-of date | Verified age below the ceiling |
| School qualification | Canonical school tier and degree chain |
| Education-chain check | Explicit clean-chain result |
| Large-company experience | Only context-verified employers |
| Experience type | Formal, formal plus internship, or internship only |
| Technical evidence | Short hands-on evidence summary |
| Source batch | Input folder or batch |
| Source filename | Original filename without contact data |
| Evidence status | Verified or conservative |

Never include phone, email, address, ID number, photograph, compensation, or unrelated sensitive data unless explicitly required.

## Pending or Excluded

Include near matches and all manually reviewed exception files:

| Column | Meaning |
| --- | --- |
| Candidate or alias | Best available identity |
| Original role | Source role |
| Disposition | Pending verification or excluded |
| Reason | One decisive, evidence-based reason |
| Triggered false hit | School, company, role, or age signal when relevant |
| Source batch | Input batch |
| Source filename | Original filename |

Useful reason labels:

- education-junior-college
- education-upgrade-path
- education-private-bachelor
- education-chain-unverifiable
- age-unverifiable
- age-boundary-unverifiable
- age-not-under-ceiling
- age-conflict-review
- school-tier-not-met
- school-tier-unverifiable
- company-not-employment
- company-role-nontechnical
- role-nontechnical
- duplicate

## Methodology

Record:

- task-local school and company definitions;
- the complete Tier 2 school whitelist;
- age ceiling, as-of date, and accepted age-evidence types;
- internship policy;
- strict education rule;
- authoritative source URLs and access date;
- supported file types and extraction limitations;
- duplicate method;
- manual-review method;
- statement that resume claims were screened, not independently background-checked.

## Workbook presentation

- Freeze headers and enable filters.
- Use wrapped text and readable widths.
- Highlight internship-only rows.
- Label Tier 1 and Tier 2 clearly and prevent overlap.
- Keep unknown-age candidates only in `Pending or Excluded`.
- Keep source filenames available for retrieval.
- Use formulas for summary counts where supported.
- Render every sheet and inspect spreadsheet errors before export.
