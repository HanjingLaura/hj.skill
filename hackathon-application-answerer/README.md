# Hackathon Application Answerer

[English](README.md) | [中文](README.zh-CN.md)

A reusable Codex skill for answering repetitive hackathon, accelerator, fellowship, builder program, startup competition, and innovation challenge application questions without loading the same personal background into every conversation.

The skill separates public reusable workflow from private personal memory:

- Public files define answer strategy, question patterns, and templates.
- Local files store personal facts, prior answers, preferences, and iteration notes.
- Local files are ignored by Git so the skill can be used personally without publishing sensitive information.

## Features

- Draft copy-ready application answers in Chinese or English.
- Map similar questions to prior answers and reusable angles.
- Keep personal context in a structured local profile.
- Build an answer bank while completing real applications.
- Adapt answers to word limits, tone, tracks, themes, and event context.
- Suggest what should be saved after each answer so the skill improves over time.

## Good Fits

- Self-introduction questions.
- Motivation and event-fit questions.
- Project ideas and track selection.
- Technical, product, design, or collaboration strengths.
- Past project and portfolio descriptions.
- Team conflict, values, vision, and reflective questions.
- Social-impact, industry, community, or user-insight prompts.

## Folder Structure

```text
hackathon-application-answerer/
  SKILL.md
  README.md
  README.zh-CN.md
  agents/
    openai.yaml
  references/
    profile.template.md
    answer-bank.template.md
    question-patterns.md
  local/
    profile.local.md
    answer-bank.local.md
  scripts/
    reset-local-memory.ps1
```

`references/` contains public templates and reusable guidance. `local/` contains private memory and should not be committed.

## First-Time Setup

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File hackathon-application-answerer\scripts\reset-local-memory.ps1
```

Then fill in:

- `local/profile.local.md`: real background, projects, skills, preferences, and constraints.
- `local/answer-bank.local.md`: strong submitted answers, reusable snippets, and editing notes.

## Daily Use

Example requests:

```text
Use $hackathon-application-answerer to answer this hackathon application in Chinese. Keep each answer under 200 Chinese characters.
```

```text
Use $hackathon-application-answerer to improve this answer and suggest what should be saved into my answer bank.
```

```text
Use $hackathon-application-answerer to generate three variants: concise, sincere, and product-oriented.
```

If you keep the skill outside Codex's skills directory, copy the `hackathon-application-answerer/` folder into your Codex skills directory first, for example `~/.codex/skills/hackathon-application-answerer`.

## Local Memory Iteration

After completing a real application:

1. Save strong final answers to `local/answer-bank.local.md`.
2. Add new project facts, preferences, or constraints to `local/profile.local.md`.
3. Remove stale details that no longer represent the user.

This keeps the skill personalized without requiring a huge repeated prompt.

## Reset Local Memory

To clear previous personal content and rebuild local files from templates:

```powershell
powershell -ExecutionPolicy Bypass -File hackathon-application-answerer\scripts\reset-local-memory.ps1
```

This recreates:

- `local/profile.local.md`
- `local/answer-bank.local.md`

To delete local memory files without recreating templates:

```powershell
powershell -ExecutionPolicy Bypass -File hackathon-application-answerer\scripts\reset-local-memory.ps1 -DeleteOnly
```

## Privacy Model

Commit:

- `SKILL.md`
- `README.md`
- `README.zh-CN.md`
- `agents/openai.yaml`
- `references/*.template.md`
- `references/question-patterns.md`
- `scripts/reset-local-memory.ps1`

Do not commit:

- `local/`
- `*.local.md`
- resumes, portfolios, screenshots, generated PDFs
- files containing private contact details, personal stories, or unpublished project information

The root `.gitignore` is configured to ignore these private files.
