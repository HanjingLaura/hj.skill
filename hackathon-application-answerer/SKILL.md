---
name: hackathon-application-answerer
description: Draft, adapt, and improve personalized hackathon application answers. Use when the user needs to answer repeated hackathon, fellowship, accelerator, builder program, demo day, startup competition, or innovation challenge application questions; wants reusable answer variants; wants to map similar questions to prior answers; or wants to turn personal/project background into concise, persuasive registration responses.
---

# Hackathon Application Answerer

## Core Workflow

1. Identify the application context: hackathon name, theme, judging criteria, target track, answer language, word/character limits, deadline, and whether the response is individual or team-based.
2. Resolve the private local memory directory. Prefer a user-provided directory. Otherwise use the current workspace path `.hj-skill-local/hackathon-application-answerer/`. For backward compatibility only, use `local/` inside the skill folder if it already exists.
3. Read the user's local profile first when available: `<local memory directory>/profile.local.md`. If it does not exist, read `references/profile.template.md` and ask the user for the missing facts needed to answer.
4. Read the user's local reusable answer bank first when available: `<local memory directory>/answer-bank.local.md`. If it does not exist, read `references/answer-bank.template.md` for the expected structure.
5. Read `references/question-patterns.md` when classifying questions or deciding the best answer structure.
6. Draft answers in the same language as the application question unless the user asks otherwise.
7. Preserve truthfulness. Do not invent personal facts, awards, project metrics, teammates, affiliations, or availability. If a key fact is missing, either ask a concise question or mark `[needs user info: ...]` inside a draft.
8. Prefer concrete evidence over generic passion: project names, shipped artifacts, tools used, users helped, obstacles overcome, metrics, and the user's distinctive motivation.
9. After drafting, suggest reusable snippets that should be added to `<local memory directory>/answer-bank.local.md` when the user is likely to face similar questions again.

## Answer Strategy

For each question:

- Classify the underlying question type, not just the surface wording.
- Reuse prior content only after adapting it to the specific program, theme, and limit.
- Lead with the strongest direct answer in the first sentence.
- Use one compact story or proof point when space allows.
- End with fit: why this hackathon/program is the right place for this project or person.
- Keep answers specific, humble, and outcome-oriented.

When there is a word or character limit, draft within the limit. If no limit is given, default to:

- Short form: 80-120 words for ordinary text boxes.
- Medium form: 150-220 words for motivation, project, or team-fit prompts.
- Bullet form: 3-5 concise bullets for lists.

## Common Deliverables

Produce the format that best matches the request:

- A table mapping each application question to intent, reused source, and final answer.
- Multiple answer variants: concise, warm, technical, founder-like, or more personal.
- A reusable answer bank entry when the user wants to save a polished response.
- A gap list of missing facts needed to strengthen weak answers.
- A final copy-ready application response set.

## Voice

Default to a voice that is:

- Clear, direct, and human.
- Ambitious without sounding exaggerated.
- Specific about builder energy, learning speed, collaboration, and shipped work.
- Comfortable in either English or Chinese, matching the application language.

Avoid:

- Overclaiming impact.
- Cliches such as "I have always been passionate about technology" unless backed by a concrete story.
- Generic praise of the hackathon that could apply to any event.
- Repeating the same personal anecdote across many answers unless the user asks for consistency.

## Reference Files

- `<local memory directory>/profile.local.md`: Private user profile, projects, achievements, preferences, constraints, and reusable personal facts. Read whenever answers require personal or project specifics. This file should not be committed.
- `references/profile.template.md`: Public template for creating a private profile. Read when `profile.local.md` is missing or when helping a user set up the skill.
- `<local memory directory>/answer-bank.local.md`: Private prior answers and polished snippets. Read whenever a new question resembles previous application questions. This file should not be committed.
- `references/answer-bank.template.md`: Public template for creating a private answer bank. Read when `answer-bank.local.md` is missing or when helping a user set up reusable answer storage.
- `references/question-patterns.md`: Common hackathon application question types and response structures. Read when deciding how to frame a response.
