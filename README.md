# hj.skill

[English](README.md) | [中文](README.zh-CN.md)

`hj.skill` is a personal Codex skill workspace for collecting small reusable skills.

This repository is for distilling small reusable skills from real personal workflows: repeated application forms, portfolio drafting, project summaries, interview preparation, research workflows, or any other task that becomes easier when the agent can follow a stable method without loading a huge conversation history.

The public repository should contain reusable workflows, templates, and examples. Private personal context stays local and ignored by Git.

## Included Skills

| Skill | What it does | Status |
| --- | --- | --- |
| [`hackathon-application-answerer`](hackathon-application-answerer/README.md) | Drafts, adapts, and improves answers for hackathon, builder program, fellowship, and startup competition applications. | Ready |

More skills can be added as new repeated needs appear.

## Common Usage Pattern

Most skills in this repository follow the same workflow:

1. Choose the skill that matches the task.
2. Copy public template files, such as `profile.template.md`, into private local files, such as `profile.local.md`.
3. Fill the local files with your real background, preferences, prior answers, examples, and constraints.
4. Ask Codex to use the skill, for example: `Use $hackathon-application-answerer to answer this form`.
5. Review and edit the generated answer before submitting it.
6. Save useful final answers, user edits, and lessons learned back into local files so the next answer becomes more accurate.

This makes each skill reusable by others while still allowing deep personalization on one machine.

## Skill Structure

A typical skill folder looks like this:

```text
skill-name/
  SKILL.md
  README.md
  README.zh-CN.md
  agents/
    openai.yaml
  references/
    profile.template.md
  local/
    profile.local.md
```

`references/` stores public templates and reusable guidance. `local/` stores private memory and should not be committed.

## Privacy Convention

Commit public skill files:

- `SKILL.md`
- `README.md`
- `README.zh-CN.md`
- `agents/openai.yaml`
- `references/*.template.md`
- general reference files without personal facts

Keep private or generated files ignored:

- `local/`
- `*.local.md`
- `*.private.md`
- `private/`
- `tmp/`
- `output/`
- generated portfolios, resumes, screenshots, logs, and one-off scripts

## Adding More Skills

When adding a new skill, follow the same split:

1. Put reusable instructions in `SKILL.md`.
2. Put non-personal examples in `*.template.md`.
3. Put real private context in `local/*.local.md`.
4. Add local/generated artifacts to `.gitignore`.
5. Validate the skill before publishing.

The goal is to make this repo useful to other people while still supporting deeply personalized local workflows.
