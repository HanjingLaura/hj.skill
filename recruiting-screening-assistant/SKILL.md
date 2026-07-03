---
name: recruiting-screening-assistant
description: "Prepare recruiting screening calls, post-call candidate evaluations, and ranked candidate tracker updates. Use when the user provides a candidate resume, profile, job description, hiring persona, phone-screen notes, or candidate pipeline information and wants: a tailored screening call script, resume-based questions, required screening questions, candidate risk/recommendation analysis, next-step recommendation, ranked Markdown candidate table, or reusable recruiting process notes."
---

# Recruiting Screening Assistant

## Core Workflow

1. Identify the hiring context: role, seniority, location, work mode, timeline, required availability, process stage, and decision owner.
2. Read private local hiring context first when available: `local/company-context.local.md`. If it is missing, read `references/company-context.template.md` and ask for the missing role/process details.
3. Read `references/screening-workflow.md` before preparing a call script or process handoff.
4. Read `references/evaluation-rubric.md` before analyzing phone notes or recommending next steps.
5. Read `references/candidate-tracker.template.md` before creating or updating a candidate tracker.
6. If the user provides a resume or profile, extract only evidence-backed facts. Do not invent education, experience, dates, hometown, motivations, skills, availability, or AI tool usage.
7. Draft in the same language as the user's request unless they ask otherwise.
8. Keep the output operational: copy-ready call script, exact questions, note-taking fields, risks, recommendation points, candidate tracker update, and next action.
9. After the user shares post-call notes, convert them into structured evaluation, update the ranked candidate tracker, and suggest what should be saved into local context for future screens.

## Call Script Output

When preparing a screening call, produce:

- Candidate snapshot: role fit, notable resume facts, likely strengths, unknowns to verify.
- Call goal: what must be learned in this call.
- Full call script:
  - opening and consent to talk
  - company and role introduction adapted to the candidate
  - resume-based questions
  - required screening questions
  - motivation and stability questions
  - candidate Q&A handling notes
  - closing and next-step wording
- Note-taking checklist for the call.
- Risk watchlist: issues to probe without sounding accusatory.

## Post-Call Evaluation Output

When analyzing call notes, produce:

- One-paragraph candidate summary.
- Recommendation points with evidence.
- Risk points with evidence.
- Missing information or follow-up questions.
- Stage recommendation: `advance`, `leader check`, `hold`, `reject`, or `needs more info`.
- Recommendation rank among tracked candidates, with brief rationale.
- Candidate tracker row using the columns in `references/candidate-tracker.template.md`.
- Suggested internal handoff message.
- Suggested local-memory update if the user wants the skill to improve.

## Candidate Tracker Output

When the user asks for evaluation after a call, or when the task involves multiple candidates:

1. Read `local/candidate-tracker.local.md` if it exists. If missing, use `references/candidate-tracker.template.md` as the structure.
2. Add or update the current candidate row.
3. Preserve existing candidate rows unless the user asks to delete or archive them.
4. Sort the Markdown table by recommendation order, with the strongest candidate first.
5. Use only evidence from the resume, profile, or call notes. If a required field is unknown, write `unknown` rather than guessing.
6. Keep recommendation and risk cells concise; use semicolons for multiple points.
7. Provide either:
   - the full updated table when the user needs the document content, or
   - the exact row plus sorting instruction when direct file editing is not requested.

Required tracker fields:

- Recommendation order
- Name
- School
- Grade / year
- Hometown
- Whether they can accept a stable 6-month internship
- Earliest start date
- Whether they use overseas LLMs or overseas AI models
- Recommendation points
- Risk points

## Screening Principles

- Prioritize evidence over impressions. Tie every recommendation or risk to resume facts, call notes, or explicit candidate statements.
- Separate `fact`, `inference`, and `question to verify`.
- Tailor scripts to the candidate's background while preserving the user's required process.
- Keep the tone professional, warm, and efficient.
- Avoid over-selling. Explain opportunity fit clearly, but do not promise compensation, conversion, offer probability, or career outcomes unless the user provided approved wording.
- Flag potentially sensitive or legally risky questions when they appear. If a question touches family, health, protected traits, or private life, suggest a job-related alternative focused on availability, stability, commute, work authorization, or role motivation.

## Reference Files

- `local/company-context.local.md`: Private company, role, process, phone script, JD, candidate persona, and approved pitch. Read whenever preparing real calls or evaluations. This file should not be committed.
- `local/candidate-tracker.local.md`: Private ranked candidate tracker. Read and update after post-call evaluation when available. This file should not be committed.
- `references/company-context.template.md`: Public template for creating private company context.
- `references/screening-workflow.md`: Generic phone-screen preparation and follow-up workflow.
- `references/evaluation-rubric.md`: Structured evaluation dimensions for post-call candidate analysis.
- `references/call-notes.template.md`: Template for capturing call notes that can be evaluated later.
- `references/candidate-tracker.template.md`: Public template for a ranked Markdown candidate tracker.
