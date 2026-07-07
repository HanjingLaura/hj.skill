# Context Authoring Guide

Use this guide when converting a client document, job description, hiring brief, or recruiter notes into a reusable role context.

## Build the Context

1. Identify the private facts that should stay local: client identity, internal priorities, sensitive claims, compensation, funding, non-public relationships, and approved wording.
2. Put private facts only in `.hj-skill-local/candidate-fit-tracker/*.local.md`.
3. Convert the source document into screening instructions, not a narrative summary.
4. Preserve the client's own distinctions between roles, especially where common candidates are easy to misclassify.
5. Keep each role centered on one core evaluation question.
6. Define strong signals, weak signals, adjacent roles, scoring thresholds, human-review triggers, and output format.
7. Include "candidate communication notes" only when the source provides approved wording or constraints.
8. Define the role score columns that should appear in `candidate-screening-table.local.md`.
9. Assign a stable `Context ID` for this client or role group. Use lowercase letters, digits, and hyphens when possible.

## What to Extract

- Client background needed to explain the opportunity.
- Current hiring objective and target roles.
- For each role: one-line definition, core evaluation question, responsibilities, strong signals, preferred profile, weak signals, and confirmation questions.
- Role differentiation rules: how to tell role A from role B and from adjacent profiles.
- Scoring rubric and recommendation labels.
- Required output format or handoff format.
- Candidate table columns, especially the exact target role names and any adjacent role score column.
- Context ID for separating this role group from other local contexts.
- Human review triggers.
- Sensitive claims that should not be proactively disclosed.

## What to Avoid

- Do not paste a long source document unchanged when a compact role context will work.
- Do not include private context in public `references/`.
- Do not make a role look broader than the client intended.
- Do not turn weak or adjacent signals into target-role requirements.
- Do not invent scoring weights unless the source document provides them or the user asks for them.

## Quality Check

Before using a new context, confirm it answers:

- Which exact role context should trigger this file?
- What candidate evidence would produce a high score?
- What evidence is merely adjacent?
- What evidence should reduce confidence?
- What output should the recruiter send onward?
- What Markdown table row should be updated after each candidate?
- What situations require human review instead of a final call?

