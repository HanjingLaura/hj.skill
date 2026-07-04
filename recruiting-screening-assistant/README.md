# Recruiting Screening Assistant

[English](README.md) | [中文](README.zh-CN.md)

A reusable Codex skill for preparing recruiting phone screens, evaluating written assignments, analyzing post-call notes, and maintaining a ranked Markdown candidate tracker.

The public skill contains generic recruiting workflows, assignment rubrics, templates, evaluation rubrics, and tracker structure. Company-specific process, phone scripts, job descriptions, candidate persona, approved pitch, call notes, assignments, and real candidate data should live in `local/`, which is ignored by Git.

## Features

- Draft a tailored phone-screen script from a candidate resume or profile.
- Adapt company and role pitch to the candidate's likely motivation.
- Generate resume-based probing questions and required screening questions.
- Create a note-taking checklist for the call.
- Analyze post-call notes into recommendation points, risk points, missing information, and next-step suggestions.
- Evaluate written assignments, research tasks, case tasks, or homework submissions.
- Produce internal handoff messages for leader or hiring manager review.
- Maintain a ranked Markdown candidate tracker sorted by final recommendation order.

## Candidate Tracker

After post-call or assignment evaluation, the skill can add or update a row in `local/candidate-tracker.local.md`.

The tracker keeps candidates in ranked recommendation order with these fields:

- Recommendation order
- Name
- School
- Grade / year
- Hometown
- Whether the candidate can accept a stable 6-month internship
- Earliest start date
- Whether the candidate uses overseas LLMs or overseas AI models
- Assignment status
- Recommendation points
- Risk points

Unknown fields should be written as `unknown`; the skill should not guess candidate facts or assignment performance.

## Assignment Evaluation

Use the assignment evaluation flow after receiving a candidate's written task, research task, case analysis, or screening homework.

The public rubric evaluates:

- Completion and timeliness
- Understanding of the task
- Research and information quality
- Industry insight and judgment
- Structured thinking
- Execution detail
- Communication quality
- AI tool use

Assignment results should update the candidate tracker's `Assignment status` column and may change the final recommendation order.

## Folder Structure

```text
recruiting-screening-assistant/
  SKILL.md
  README.md
  README.zh-CN.md
  agents/
    openai.yaml
  references/
    company-context.template.md
    screening-workflow.md
    evaluation-rubric.md
    assignment-rubric.md
    call-notes.template.md
    candidate-tracker.template.md
  local/
    company-context.local.md
    call-notes.local.md
    candidate-tracker.local.md
  scripts/
    reset-local-context.ps1
```

`references/` contains public templates and general guidance. `local/` contains private company and candidate context and should not be committed.

## First-Time Setup

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File recruiting-screening-assistant\scripts\reset-local-context.ps1
```

Then fill in:

- `local/company-context.local.md`: company pitch, hiring process, role JD, candidate persona, phone script preferences, assignment rules.
- `local/call-notes.local.md`: optional working notes from a specific call.
- `local/candidate-tracker.local.md`: ranked candidate table maintained after screening calls and assignments.

If you keep the skill outside Codex's skills directory, copy the `recruiting-screening-assistant/` folder into your Codex skills directory first, for example `~/.codex/skills/recruiting-screening-assistant`.

## Example Requests

```text
Use $recruiting-screening-assistant to prepare a 10-minute phone-screen script for this candidate resume.
```

```text
Use $recruiting-screening-assistant to analyze these phone notes, give recommendation points and risk points, and update my candidate tracker.
```

```text
Use $recruiting-screening-assistant to evaluate this candidate assignment and update the assignment status in my ranked tracker.
```

```text
Use $recruiting-screening-assistant to update the ranked candidate tracker after this call and assignment. Keep unknown fields as unknown.
```

## Recommended Workflow

1. Source and screen the candidate resume.
2. Let Codex draft the phone-screen script.
3. Complete the phone screen and add qualified candidates to the follow-up channel.
4. Send and collect the written assignment, if required.
5. Send call notes or assignment content back to Codex.
6. Let Codex produce evaluation, risks, next step, internal handoff, assignment status, and a candidate tracker update.
7. Save the updated table in `local/candidate-tracker.local.md`.

## Privacy

Commit:

- `SKILL.md`
- `README.md`
- `README.zh-CN.md`
- `agents/openai.yaml`
- `references/*.md`
- `scripts/reset-local-context.ps1`

Do not commit:

- `local/`
- candidate resumes
- assignment submissions
- phone notes with personal details
- candidate tracker files with real people
- company-private scripts, JDs, scorecards, or internal process notes
