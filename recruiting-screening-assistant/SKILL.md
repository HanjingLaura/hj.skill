---
name: recruiting-screening-assistant
description: "Prepare recruiting screening calls and post-call candidate evaluations. Use when the user provides a candidate resume, profile, job description, hiring persona, or phone-screen notes and wants: a tailored screening call script, resume-based questions, required screening questions, candidate risk/recommendation analysis, next-step recommendation, or reusable recruiting process notes."
---

# Recruiting Screening Assistant

## Core Workflow

1. Identify the hiring context: role, seniority, location, work mode, timeline, required availability, process stage, and decision owner.
2. Read private local hiring context first when available: `local/company-context.local.md`. If it is missing, read `references/company-context.template.md` and ask for the missing role/process details.
3. Read `references/screening-workflow.md` before preparing a call script or process handoff.
4. Read `references/evaluation-rubric.md` before analyzing phone notes or recommending next steps.
5. If the user provides a resume or profile, extract only evidence-backed facts. Do not invent education, experience, dates, motivations, skills, or availability.
6. Draft in the same language as the user's request unless they ask otherwise.
7. Keep the output operational: copy-ready call script, exact questions, note-taking fields, risks, recommendation points, and next action.
8. After the user shares post-call notes, convert them into structured evaluation and suggest what should be saved into local context for future screens.

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
- Suggested internal handoff message.
- Suggested local-memory update if the user wants the skill to improve.

## Screening Principles

- Prioritize evidence over impressions. Tie every recommendation or risk to resume facts, call notes, or explicit candidate statements.
- Separate `fact`, `inference`, and `question to verify`.
- Tailor scripts to the candidate's background while preserving the user's required process.
- Keep the tone professional, warm, and efficient.
- Avoid over-selling. Explain opportunity fit clearly, but do not promise compensation, conversion, offer probability, or career outcomes unless the user provided approved wording.
- Flag potentially sensitive or legally risky questions when they appear. If a question touches family, health, protected traits, or private life, suggest a job-related alternative focused on availability, stability, commute, work authorization, or role motivation.

## Reference Files

- `local/company-context.local.md`: Private company, role, process, phone script, JD, candidate persona, and approved pitch. Read whenever preparing real calls or evaluations. This file should not be committed.
- `references/company-context.template.md`: Public template for creating private company context.
- `references/screening-workflow.md`: Generic phone-screen preparation and follow-up workflow.
- `references/evaluation-rubric.md`: Structured evaluation dimensions for post-call candidate analysis.
- `references/call-notes.template.md`: Template for capturing call notes that can be evaluated later.
