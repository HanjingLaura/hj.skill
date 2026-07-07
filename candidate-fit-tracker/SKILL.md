---
name: candidate-fit-tracker
description: "Evaluate candidates against a real client role context with evidence-backed fit scoring, role differentiation, risks, next actions, and a maintained Markdown screening table. Use when the user provides company context, key roles, role differentiation, talent profiles, a resume, profile, candidate communication notes, job description, hiring persona, or local role context and wants stable screening judgments for real roles rather than generic recruiting advice."
---

# Candidate Fit Tracker

## Core Workflow

1. Resolve the local context directory.
   - Prefer a directory named by the user.
   - Otherwise use `.hj-skill-local/candidate-fit-tracker/` under the current workspace.
2. Resolve the role context before judging any candidate.
   - Prefer a role context file named by the user.
   - Otherwise search the local context directory for role context files ending in `.local.md`, excluding candidate table files.
   - If exactly one local context matches the user's client or role wording, read it.
   - If no local context exists, read `references/role-context.template.md` and ask the user for the missing client and role details.
   - If several contexts could apply, ask the user which one to use before scoring.
3. Read the selected local role context completely. Treat it as the source of truth for client background, role priorities, scoring thresholds, approved wording, and handoff format.
   - Use its `Context ID` as the stable role-pool identifier.
   - If no `Context ID` exists, derive one from the context filename and add it when updating the context.
4. Read `references/screening-output-format.md` before producing an evaluation unless the local context defines a stricter output format.
5. Read `references/candidate-screening-table.template.md` before creating or updating a candidate table.
6. Extract candidate evidence from the resume, profile, OCR text, interview notes, or assignment notes. Use only evidence present in the candidate material.
7. Score each target role independently. Do not average roles together and do not let a strong adjacent profile inflate the main-role score.
8. Separate four buckets in the reasoning:
   - target role fit
   - adjacent role fit
   - weak or misleading keyword match
   - evidence gaps to verify by phone or hiring-manager review
9. Output in the user's language unless they ask otherwise. Keep the answer operational and concise enough to forward.

## Candidate Table Workflow

Use a Markdown table as the running record for candidate screening.

1. Store the table in the local context directory as `candidate-screening-table.<context-id>.local.md` when a `Context ID` is available. Fall back to `candidate-screening-table.local.md` only for legacy or single-context use.
2. If the table does not exist, create it from `references/candidate-screening-table.template.md`, set the `role context` column, and adapt the role score columns to the selected role context.
3. Before evaluating a new candidate, read the existing table so recommendations stay consistent with prior candidates.
4. If the candidate is new, append one row. If the candidate already exists, update that row instead of duplicating it.
5. Treat candidates with the same name but different `role context` values as separate screening records unless the user asks to merge them.
6. Include resume evidence and communication notes in the same row when the user provides follow-up messages, phone notes, preferences, availability, concerns, or clarifications.
7. Keep table cells compact. Use `<br>` inside cells for numbered reasons, risks, and phone confirmation points.
8. Preserve existing rows and ordering unless the user asks to reorder. If ranking is requested, sort strongest candidates first within the same `role context`.
9. After updating the file, summarize what changed and show the updated row or the compact table excerpt relevant to the current candidate.

Default table fields:

- candidate
- role context
- resume source / file name
- recommendation
- role 1 score
- role 2 score
- extra role score, when useful
- best-fit role
- core reasons
- main risks
- suggested action
- whether to schedule a call
- phone confirmation points

## Evidence Rules

- Tie every positive judgment, risk, and score to concrete evidence from the candidate material.
- Do not infer hidden depth from titles such as AI engineer, agent engineer, researcher, backend engineer, platform engineer, SRE, or architect.
- Prefer project substance over keywords: what the candidate built, researched, evaluated, deployed, scaled, operated, or owned.
- Write `insufficient evidence` when the resume names a keyword but gives no project detail. Use the user's language in final output.
- Do not invent education, dates, employers, publications, open-source impact, compensation, location intent, availability, or motivation.
- If the candidate appears strong but the role fit is unclear, keep the score conservative and add phone-confirmation questions.

## Scoring

Use the local context's scoring rubric. If it does not define one, use this default:

- `85-100`: strong recommend; clearly matches the role's core requirements
- `70-84`: worth a call; relevant evidence exists but depth, ownership, or direction needs confirmation
- `55-69`: backup; adjacent experience exists but the candidate is not centered on this role
- `40-54`: weak match; likely to be challenged by the client
- `0-39`: not recommended for this role

Score target roles separately. Add an adjacent-role score only when it helps avoid forcing the candidate into the wrong role.

## Manual Review Triggers

Flag for human review when any of these apply:

- More than one target role scores `75+`.
- The candidate looks unusually strong but the recommendation is negative.
- The candidate has many high-signal keywords but project descriptions are vague.
- The candidate has top-tier research, core platform ownership, notable open-source work, or unusually relevant domain experience.
- Compensation, location, stability, availability, or direction appears risky or unclear.
- The local context explicitly names additional review triggers.

## Role Context Creation

When the user asks to turn a client document, job description, or hiring notes into a reusable context:

1. Read `references/context-authoring-guide.md`.
2. Use `references/role-context.template.md` as the structure.
3. Keep client-specific or private facts in `.hj-skill-local/candidate-fit-tracker/*.local.md`, not in the public skill folder.
4. Preserve approved client wording, sensitive claims, and "do not say" constraints exactly.
5. Condense long source material into screening-useful sections: client background, roles, strong signals, weak signals, role differentiation, scoring, review triggers, output format, and candidate communication notes.
6. If the user provides the company situation, key roles, role differentiation, and talent profiles first, create or update the local role context before evaluating candidates.
7. Give each role context a stable `Context ID` so multiple clients or job groups can coexist in the same local directory.
8. If the user then provides resumes or candidate communications, update the candidate table for that `Context ID` directly.

## Reference Files

- `references/role-context.template.md`: Template for a private client and role context.
- `references/screening-output-format.md`: Default concise evaluation and handoff format.
- `references/candidate-screening-table.template.md`: Default Markdown table for ongoing candidate screening.
- `references/context-authoring-guide.md`: Instructions for converting client hiring documents into reusable local contexts.
- `.hj-skill-local/candidate-fit-tracker/*.local.md`: Private client and role contexts plus the running candidate table. Read the relevant role context and candidate table before evaluating candidates.


