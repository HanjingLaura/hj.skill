# hj.skill

[English](README.md) | [中文](README.zh-CN.md)

`hj.skill` is a small collection of reusable Codex skills distilled from real workflows.

The goal is simple: keep repeatable methods public, keep personal or company-specific context local, and let each user build their own private memory without copying long background prompts into every conversation.

## Quick Start

1. Clone this repository.
2. Choose a skill folder from the list below.
3. Copy that folder into your Codex skills directory.
4. If the skill needs private local files (see the Setup column below), run its setup script from the workspace where you want private data stored. By default, it creates `.hj-skill-local/<skill-name>/`.
5. Fill the generated `*.local.md` files with your own context.
6. Invoke the skill in Codex with its `$skill-name`.

Example skills directory paths:

```text
macOS / Linux: ~/.codex/skills/
Windows: C:\Users\<you>\.codex\skills\
```

Example copy target:

```text
~/.codex/skills/hackathon-application-answerer
~/.codex/skills/recruiting-screening-assistant
```

You can also keep this repo as a development workspace and copy individual skill folders into Codex only when they are ready.

## Included Skills

| Skill | Use it for | Setup |
| --- | --- | --- |
| [`hackathon-application-answerer`](hackathon-application-answerer/README.md) | Drafting and improving hackathon, builder program, fellowship, and startup competition application answers. | `powershell -ExecutionPolicy Bypass -File hackathon-application-answerer\scripts\reset-local-memory.ps1` |
| [`recruiting-screening-assistant`](recruiting-screening-assistant/README.md) | Preparing recruiting phone-screen scripts, evaluating assignments and post-call notes, and maintaining a ranked candidate tracker. | `powershell -ExecutionPolicy Bypass -File recruiting-screening-assistant\scripts\reset-local-context.ps1` |
| [`candidate-fit-tracker`](candidate-fit-tracker/SKILL.md) | Evaluating candidates against real client role contexts with evidence-backed fit scoring, risks, next actions, and maintained screening notes. | `powershell -ExecutionPolicy Bypass -File candidate-fit-tracker\scripts\reset-local-context.ps1` |
| [`candidate-comments-template`](candidate-comments-template/SKILL.md) | Turning a candidate resume and chat record into a concise, copy-ready comments template with background, motivation, compensation, level, and performance. | No setup required |
| [`ai-news-gossip-comic`](ai-news-gossip-comic/SKILL.md) | Fetching and verifying recent AI news, rewriting it in a playful gossip style, and producing sourced news cards, storyboards, and multi-panel comic prompts. | No setup required |

Read each skill's README or SKILL.md for its exact workflow and examples.

## Common Usage Pattern

Most skills in this repo follow the same loop:

1. Initialize private local files from public templates.
2. Add your own background, examples, preferences, role context, or process details into `.hj-skill-local/<skill-name>/*.local.md`, or into another directory passed with `-LocalRoot`.
3. Ask Codex to use the skill, such as `Use $hackathon-application-answerer to answer this form`.
4. Review and edit the output before using it.
5. Save useful final versions and lessons back into local files.

Over time, the public skill stays clean while your local version becomes more personalized.

## Skill Structure

```text
skill-name/
  SKILL.md                  # required: the reusable skill instructions
  README.md                 # optional: English docs
  README.zh-CN.md           # optional: Chinese docs
  agents/
    openai.yaml             # Codex agent config
  references/               # optional: public templates and guidance
    public-template-or-guidance.md
  scripts/                  # optional: local-file setup/reset script
    setup-or-reset-script.ps1
```

Only `SKILL.md` is required; add `references/` and `scripts/` as the skill needs them. `references/` contains public templates and reusable guidance. Private memory should live outside the installed skill folder, usually in `.hj-skill-local/<skill-name>/` in your working directory.

## Privacy Rules

Commit:

- `SKILL.md`
- `README.md`
- `README.zh-CN.md`
- `agents/openai.yaml`
- `references/*.md` when they contain only public templates or generic guidance
- reusable scripts that do not contain private data

Do not commit:

- `local/`
- `.hj-skill-local/`
- `*.local.md`
- `*.private.md`
- resumes, candidate notes, portfolios, screenshots, logs, generated files, or company-private process details

The root `.gitignore` is configured to ignore local private files.

## Add A New Skill

When adding a new skill:

1. Put reusable instructions in `SKILL.md`.
2. Put public templates and generic guidance in `references/`.
3. Put real personal or company-specific context in `local/*.local.md`.
4. Add a small setup/reset script if local templates need to be created.
5. Validate the skill before publishing.

This keeps the repo useful to others while still supporting deeply personalized local workflows.
