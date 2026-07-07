# Role Context Template

Copy this file to `.hj-skill-local/candidate-fit-tracker/<client-or-role>.local.md` and fill it with private client details. Do not commit filled local files.

## Context Name

- Context ID:
- Client / project:
- Context owner:
- Last updated:
- Use when:

## Client Background

- What the client does:
- Current hiring objective:
- What to emphasize to candidates:
- What not to overstate or proactively disclose:
- Location, work mode, seniority, language, or process constraints:

## Target Roles

### Role 1: <Role Name>

One-line role definition:

Core evaluation question:

Primary responsibilities:

- 

Strong signals:

- 

Preferred candidate profile:

- 

Weak or misleading signals:

- 

Phone confirmation points:

- 

### Role 2: <Role Name>

One-line role definition:

Core evaluation question:

Primary responsibilities:

- 

Strong signals:

- 

Preferred candidate profile:

- 

Weak or misleading signals:

- 

Phone confirmation points:

- 

## Adjacent Roles

List profiles that may be valuable but should not be forced into the target roles.

- Adjacent role:
- How to recognize it:
- How to report it:

## Role Differentiation

- If the resume emphasizes <signal>, classify as <role>.
- If the resume emphasizes <signal>, classify as <role>.
- Common false positive:

## Scoring Rubric

- `85-100`: strong recommend; directly matches core demand
- `70-84`: worth a call; relevant but needs confirmation
- `55-69`: backup; adjacent but not centered
- `40-54`: weak match; likely client concern
- `0-39`: not recommended for the target roles

## Output Format

Use this format unless the user asks for a different one:

```text
结论：强推 / 可聊 / 备选 / 不建议
<Role 1>匹配度：xx/100
<Role 2>匹配度：xx/100
必要时补充：<Adjacent role>匹配度：xx/100
更适合岗位：xxx
为什么：
1. ...
2. ...
3. ...
主要风险：
1. ...
2. ...
建议动作：...
电话重点确认：
1. ...
2. ...
3. ...
```

## Candidate Screening Table

Default table file:

`.hj-skill-local/candidate-fit-tracker/candidate-screening-table.<context-id>.local.md`

Role context column value:

- <context-id>

Use these role score columns:

- 岗位1:
- 岗位2:
- 岗位x（如果有补充）:

When the user provides a candidate resume or follow-up communication, update the table row with:

- 候选人
- 岗位Context
- 简历来源 / 文件名
- 结论
- role score columns
- 更适合岗位
- 核心理由
- 主要风险
- 建议动作
- 是否建议电话聊
- 电话重点确认

## Human Review Triggers

- 

## Candidate Communication Notes

Approved opening pitch:

Role-specific pitch:

How to answer "what does the company do?":

How to answer "why did you contact me?":

Sensitive wording to avoid:

-

