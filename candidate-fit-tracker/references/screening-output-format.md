# Screening Output Format

Use this default when the selected local role context does not provide a stricter format.

## Candidate Evaluation

```text
结论：强推 / 可聊 / 备选 / 不建议
<目标岗位A>匹配度：xx/100
<目标岗位B>匹配度：xx/100
必要时补充：<相邻岗位>匹配度：xx/100
更适合岗位：xxx
为什么：
1. ...
2. ...
3. ...
主要风险：
1. ...
2. ...
建议动作：
强推：建议约面，主打 xxx
可聊：建议先电话确认 xxx
备选：暂存，等客户反馈后再推
不建议：不进入本岗位池
电话重点确认：
1. ...
2. ...
3. ...
```

## Handoff Summary

When the user asks for a compact handoff, use:

```text
候选人：xxx
简历来源 / 文件名：xxx
结论：强推 / 可聊 / 备选 / 不建议
<目标岗位A>：xx/100
<目标岗位B>：xx/100
<相邻岗位>：xx/100（如有）
更适合岗位：xxx
核心理由：
1.
2.
3.
主要风险：
1.
2.
建议动作：
是否建议电话聊：
电话重点确认：
```

## Running Markdown Table

When maintaining a candidate table, use this row shape. Rename `岗位1`, `岗位2`, and `岗位x` to the actual roles from the selected local context when useful.

```markdown
| 候选人 | 岗位Context | 简历来源 / 文件名 | 结论 | 岗位1 | 岗位2 | 岗位x（如果有补充） | 更适合岗位 | 核心理由 | 主要风险 | 建议动作 | 是否建议电话聊 | 电话重点确认 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xxx | context-id | xxx | 强推 / 可聊 / 备选 / 不建议 | xx/100 | xx/100 | xx/100 | xxx | 1. ...<br>2. ...<br>3. ... | 1. ...<br>2. ... | ... | 是 / 否 / 先补信息 | 1. ...<br>2. ...<br>3. ... |
```

Table update rules:

- Use one row per candidate per `岗位Context`.
- Update the existing row when follow-up candidate communication arrives.
- Keep score cells as `xx/100`; write `未评估` only when the role cannot be scored from available evidence.
- Keep reasons, risks, and confirmation points compact enough to scan.
- Preserve prior rows unless the user asks to reorder, archive, or delete.

## Writing Rules

- Put the conclusion first.
- Keep reasons short, direct, and evidence-based.
- Prefer exact project evidence over broad praise.
- Mention `证据不足` when a keyword appears without supporting detail.
- Do not write long client background unless the user asks.
- Do not hard-push a candidate into target roles when the evidence points to an adjacent role.
