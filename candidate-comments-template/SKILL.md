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
9. When an exact client or role is supplied, include an evidence-backed recommendation strength and the main limitation in section 2. Do not turn a merely adjacent profile into a strong recommendation.
10. Render the completed comments as ordinary Markdown paragraphs with normal line wrapping. Bold only the eight numbered section headings, matching `**1. 候选人姓名**`; keep every answer paragraph in normal weight. Never place the comments inside a fenced code block, inline code, blockquote, or table; those formats create scroll boxes or make copying inconvenient.

## Resume Attachment Controls

When comments are delivered with a renamed or converted resume, use `$ttc-pdf-normalizer` and the same verified identity-block name. Before delivery, always check every rendered page for Boss-origin watermarks and remove any detected watermark conservatively (the user's standing preference is to clean such watermarks). If no supported watermark is detected, leave the page unchanged; still inspect the top-right corner for image-only marks. Render and inspect the final PDF to confirm the Chinese name is exact, a removed watermark is visually gone, and no legitimate header or body content was covered. Preserve the source file.

## Output Template

Use this exact eight-section structure:

**1. 候选人姓名**
（姓名）

**2. 建议客户、岗位**
（客户｜岗位：建议推进/可尝试/谨慎推进；用简历事实说明匹配依据，并明确尚未验证的关键能力或风险。没有具体岗位时写“待匹配｜目标方向”。）

**3. 看机会原因 / 当前状态（离职/在职）**
（状态及候选人明确说明的原因）

**4. 当前薪酬和期望薪酬**
（当前月base、薪数、奖金/股票及总包；期望薪资。缺失项写待补充。）

**5. 职级和绩效**
（当前/上一职级、晋升情况及绩效结果；缺失项写待补充。）

**6. 所在地和意向地**
（当前所在地、优先意向地及可接受范围；缺失项写待补充。）

**7. 到岗时间**
（明确时间或通知期；缺失项写待补充。）

**8. 其他在面流程或限制**
（Offer、面试阶段、已投/不可投公司、行业或地点限制、稳定性说明等；没有则写暂无。）

## Field Rules

- Name: Use the exact candidate name shown in the resume identity block. The filename may corroborate it but cannot establish it. If only an English name is visibly present, use it. If no reliable name is visible, write `候选人姓名待确认`.
- Suggested client and role: Name every supplied client-role pair that the candidate agreed to pursue. State `建议推进`, `可尝试`, or `谨慎推进` based on evidence. Summarize the highest-signal education, employer, years, domain, tools, ownership, delivery, and measurable outcomes that support the recommendation. State the most material unverified requirement or mismatch. Do not use `强推` unless the evidence clearly meets the role's core requirements.
- Opportunity reason: Separate employment status from motivation. Common motivations may include平台发展、业务方向、团队变化、薪酬提升、职业成长、地点/通勤、稳定性、离职后看新机会, but only include reasons supported by the chat record.
- Compensation: Preserve the user's wording and units. If the user provides base, salary months, annual bonus, stock, RSU, options, sign-on, or long-term incentive, normalize into `base*薪数+长期激励，总包`. Do not convert currencies unless the user asks.
- Level and performance: Keep concise. Use the candidate's company-specific level if provided, such as `P7`, `L5`, `M2`, or `高级工程师`. For performance, include rating and period if available.
- Location and availability: Keep current city, preferred cities, acceptable alternatives, notice period, and earliest start date distinct. Do not infer relocation willingness.
- Other processes and restrictions: Preserve specific active stages, existing offers, companies already contacted, role exclusions, location constraints, and stability explanations. Do not simplify an explicit restriction away.
- Unknowns: Prefer concise placeholders: `待补充`, `待确认`, `未提及`.

## Tone

Keep the comments factual, compact, and ready to forward. Include a concise recommendation and evidence-backed limitation in section 2, but do not add numeric fit scores or speculative concerns unless the user asks. Use plain Markdown with blank lines between numbered sections; bold the eight headings only and keep all body text unbolded.
