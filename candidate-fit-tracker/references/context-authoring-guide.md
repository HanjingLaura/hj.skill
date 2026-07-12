# Context Authoring Guide

Use this guide when converting a client document, job description, hiring brief, or recruiter notes into a reusable role context.

## Build the Context

1. Identify the private facts that should stay local: client identity, internal priorities, sensitive claims, compensation, funding, non-public relationships, and approved wording.
2. Put private facts only in `.hj-skill-local/candidate-fit-tracker/<role-case>/*.local.md`.
3. Convert the source document into screening instructions, not a narrative summary.
4. Preserve the client's own distinctions between roles, especially where common candidates are easy to misclassify.
5. Keep each role centered on one core evaluation question.
6. Define strong signals, weak signals, adjacent roles, scoring thresholds, human-review triggers, and output format.
7. Include "candidate communication notes" only when the source provides approved wording or constraints.
8. Define the role score columns that should appear in `candidate-screening-table.local.md`.
9. Assign a stable `Context ID` for this client or role group. Use lowercase letters, digits, and hyphens when possible.
10. Include a feedback calibration section so interview outcomes, offer outcomes, rejection reasons, and client feedback can improve the scoring standard over time.

## What to Extract

- Client background needed to explain the opportunity.
- Current hiring objective and target roles.
- For each role: one-line definition, core evaluation question, responsibilities, strong signals, preferred profile, weak signals, and confirmation questions.
- Role differentiation rules: how to tell role A from role B and from adjacent profiles.
- Scoring rubric and recommendation labels.
- Required output format or handoff format.
- Candidate table columns, especially the exact target role names and any adjacent role score column.
- Context ID for separating this role group from other local contexts.
- Feedback signals that should update scoring over time, such as repeated rejection reasons, successful interview patterns, offer patterns, or newly discovered client preferences.
- Human review triggers.
- Sensitive claims that should not be proactively disclosed.

## What to Avoid

- Do not paste a long source document unchanged when a compact role context will work.
- Do not include private context in public `references/`.
- Do not make a role look broader than the client intended.
- Do not turn weak or adjacent signals into target-role requirements.
- Do not invent scoring weights unless the source document provides them or the user asks for them.
- Do not rewrite the scoring standard from one noisy outcome. Record it in the feedback calibration log first, then update the role context when it becomes clearly generalizable.

## Quality Check

Before using a new context, confirm it answers:

- Which exact role context should trigger this file?
- What candidate evidence would produce a high score?
- What evidence is merely adjacent?
- What evidence should reduce confidence?
- What output should the recruiter send onward?
- What Markdown table row should be updated after each candidate?
- Where should interview, offer, rejection, and client feedback be recorded?
- What feedback would justify changing the scoring standard?
- What situations require human review instead of a final call?

