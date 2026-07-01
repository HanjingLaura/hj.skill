# Recruiting Screening Assistant

[English](README.md) | [中文](README.zh-CN.md)

A reusable Codex skill for preparing recruiting phone screens and turning post-call notes into structured candidate evaluations.

The public skill contains generic recruiting workflows, templates, and evaluation rubrics. Company-specific process, phone scripts, job descriptions, candidate persona, and approved pitch should live in `local/company-context.local.md`, which is ignored by Git.

## Features

- Draft a tailored phone-screen script from a candidate resume or profile.
- Adapt company and role pitch to the candidate's likely motivation.
- Generate resume-based probing questions and required screening questions.
- Create a note-taking checklist for the call.
- Analyze post-call notes into recommendation points, risk points, missing information, and next-step suggestions.
- Produce internal handoff messages for leader or hiring manager review.

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
    call-notes.template.md
  local/
    company-context.local.md
    call-notes.local.md
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

- `local/company-context.local.md`: company pitch, hiring process, role JD, candidate persona, phone script preferences.
- `local/call-notes.local.md`: optional working notes from a specific call.

If you keep the skill outside Codex's skills directory, copy the `recruiting-screening-assistant/` folder into your Codex skills directory first, for example `~/.codex/skills/recruiting-screening-assistant`.

## Example Requests

```text
Use $recruiting-screening-assistant to prepare a 10-minute phone-screen script for this candidate resume.
```

```text
Use $recruiting-screening-assistant to analyze these phone notes and give recommendation points, risk points, and next step.
```

```text
Use $recruiting-screening-assistant to rewrite this phone script so it sounds warmer and more natural.
```

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
- phone notes with personal details
- company-private scripts, JDs, scorecards, or internal process notes
