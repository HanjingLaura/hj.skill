---
name: candidate-comments-template
description: "Generate a copy-ready candidate comments template from a resume, LinkedIn/profile text, recruiter notes, or chat records. Use when the user asks for a comments 模板, 候选人 comments, 背景概述, 看机会原因, 薪酬/级别/绩效整理, or wants resume and conversation evidence summarized into a concise Chinese candidate handoff note."
---

# Candidate Comments Template

## Core Workflow

1. Read all user-provided resume, profile, chat record, recruiter note, and compensation context.
2. Verify the candidate name from the visible identity block on the rendered first resume page. Do not use the attachment filename, chat nickname, email prefix, recruiter name, OCR output, company, school, title, or document label as primary name evidence. For Chinese names, copy the exact visible 2–4 characters; do not guess a missing or ambiguous character. If extraction/OCR conflicts with the rendered page, the rendered identity block wins. Ask the user only when that identity block is unclear or absent.
3. Check the current task history and existing TTC filenames for the verified name. If the candidate was already handled, tell the user immediately and reuse the prior PDF/number unless the source resume is a genuinely new version.
4. Extract only evidence-backed facts. Do not invent company names, titles, dates, compensation, stock value, current status, level, performance, motivation, or notice period.
5. If a required field is missing, write `待补充` or `待确认` in that field instead of guessing.
6. If sources conflict, prefer the user's latest chat record over the resume for current status, compensation, motivation, and availability. Mark unresolved conflicts as `待确认`.
7. Draft in Chinese unless the user asks otherwise.
8. Return only the completed comments template unless the user asks for analysis, questions, or a resume attachment.

## Resume Attachment Controls

When comments are delivered with a renamed or converted resume, use `$ttc-pdf-normalizer` and the same verified identity-block name. The normalizer should conservatively remove a detected Boss-origin top-right numeric watermark; if no supported watermark is detected, it must leave the page unchanged. Render and inspect the final PDF to confirm the Chinese name is exact, a removed watermark is visually gone, and no legitimate header or body content was covered. Preserve the source file.

## Output Template

Use this exact structure:

```text
（姓名）
1.背景概述
（70-100字，客观概述候选人的教育/公司/岗位/核心经历/方向，不额外渲染，不写过度评价）

2.看机会的原因
在职/离职：（在职/离职/待确认）
原因：（基于聊天记录整理候选人明确提到的看机会原因；没有则写待补充）

3.薪酬：
base：（金额）*（薪数）薪发放
长期激励：（金额/形式/周期；没有则写待补充）
总包：（金额；没有则写待补充）

4.级别：
（当前级别/目标级别/职级体系；没有则写待补充）
绩效：（绩效结果/评级/周期；没有则写待补充）
```

## Field Rules

- Name: Use the exact candidate name shown in the resume identity block. The filename may corroborate it but cannot establish it. If only an English name is visibly present, use it. If no reliable name is visible, write `候选人姓名待确认`.
- Background summary: Keep it between 70 and 100 Chinese characters when possible. Include high-signal facts such as school, degree, current/recent employer, role, years of experience, domain, and notable responsibilities. Avoid subjective praise like `优秀`, `非常强`, `顶尖`, unless directly quoted from a formal evaluation.
- Opportunity reason: Separate employment status from motivation. Common motivations may include平台发展、业务方向、团队变化、薪酬提升、职业成长、地点/通勤、稳定性、离职后看新机会, but only include reasons supported by the chat record.
- Compensation: Preserve the user's wording and units. If the user provides base, salary months, annual bonus, stock, RSU, options, sign-on, or long-term incentive, normalize into `base*薪数+长期激励，总包`. Do not convert currencies unless the user asks.
- Level and performance: Keep concise. Use the candidate's company-specific level if provided, such as `P7`, `L5`, `M2`, or `高级工程师`. For performance, include rating and period if available.
- Unknowns: Prefer concise placeholders: `待补充`, `待确认`, `未提及`.

## Tone

Keep the comments factual, compact, and ready to forward. Do not add interview recommendations, risk analysis, fit scoring, or follow-up questions unless the user explicitly asks.
