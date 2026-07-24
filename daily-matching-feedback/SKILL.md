---
name: daily-matching-feedback
description: "Capture and consolidate daily recruiting match and recommendation feedback across companies, roles, and candidates; produce an evening company-role supplement document plus a matching-mechanism feedback table and calibration suggestions. Use when the user sends job descriptions, company or role updates, candidate recommendations, client or interviewer feedback, hiring outcomes, rejection reasons, or asks to 梳理每日匹配反馈、晚间复盘、补充岗位画像、拉反馈表、判断推荐机制命中与失配、校准匹配规则."
---

# Daily Matching Feedback

把白天零散出现的公司、岗位、人选、推荐和反馈沉淀为可追溯的日记录，并在晚间生成：

1. 按公司和岗位组织的复盘文档；
2. 逐条判断匹配机制表现的 Markdown/CSV 表；
3. 可执行但不过拟合的规则校准建议。

## 工作目录

1. 优先使用用户指定的目录。
2. 否则使用当前工作区下的 `.hj-skill-local/daily-matching-feedback/<YYYY-MM-DD>/`。
3. 将当天的规范化事件保存在 `records.<YYYY-MM-DD>.local.jsonl`。
4. 将生成结果保存在同一日期目录：
   - `daily-matching-review.<YYYY-MM-DD>.md`
   - `matching-feedback-table.<YYYY-MM-DD>.md`
   - `matching-feedback-table.<YYYY-MM-DD>.csv`
5. 不要把包含真实公司、人选和反馈的 `.local.jsonl` 提交到公共 skill 目录。

## 白天采集

收到公司、岗位、人选、推荐或反馈时：

1. 读取当天已有的 `records.<date>.local.jsonl`，避免重复记录。
2. 读取 `references/event-schema.md`，将新信息规范化为一条或多条 JSONL 事件。
3. 一个“公司 × 岗位 × 人选 × 一次反馈”写一条事件。岗位级反馈没有具体人选时，将 `candidate` 留空。
4. 保留用户给出的原始推荐结论、分数、关键依据、反馈来源、实际结果和补充信息；缺失字段使用空字符串，不猜测。
5. 将同一事件的后续澄清更新到原记录，而不是新增近似重复行。
6. 只保存本任务需要的招聘信息。不要记录私人联系方式、身份证号、完整住址或无关敏感信息。
7. 若用户只是白天持续“丢材料”，简短确认已归档的公司、岗位、人选和反馈，不提前强行给出最终校准结论。

## 判断匹配机制

对每条有实际反馈的事件填写 `mechanism_judgment`：

- `hit`：原推荐方向和实际反馈一致，且关键理由被验证。
- `partial`：方向基本正确，但级别、深度、硬约束、岗位边界或核心依据存在明显偏差。
- `miss`：明确反馈与原推荐相反，或原机制漏掉了决定性信息。
- `pending`：没有足够的下游反馈，不能评价机制。

填写 `issue_type` 时只选一个主因；需要时把次要原因写入 `mechanism_note`。使用 `references/event-schema.md` 中的受控值。

区分三类结论：

- `candidate-specific`：只解释这个人选，不改通用规则。
- `company-role-specific`：更新该公司/岗位画像或筛选规则。
- `mechanism-general`：可能适用于多个公司/岗位的通用机制。

不要因为一个模糊拒绝、流程偶然结果或单一候选人就修改全局机制。只有反馈明确、重复出现或直接揭示岗位硬条件时，才将规则标为 `apply`；其余标为 `observe` 或 `no_change`。

## 晚间复盘

用户说“晚上梳理”“今天复盘”“拉表”“把反馈给匹配机制”或同义表达时：

1. 汇总本轮材料与当天已有记录。
2. 对每条记录补齐机制判断、误差类型、泛化范围、置信度和建议动作。
3. 检查：
   - 公司和岗位是否可定位；
   - 原推荐与实际反馈是否来自明确证据；
   - 岗位补充信息是否为已确认事实；
   - 候选人个案是否被误写成通用规则；
   - 同一事件是否重复。
4. 将 `<skill-root>` 解析为本 `SKILL.md` 所在目录，再运行：

```powershell
python "<skill-root>\scripts\render_daily_review.py" `
  --input "<date-dir>\records.<YYYY-MM-DD>.local.jsonl" `
  --date "<YYYY-MM-DD>" `
  --output-dir "<date-dir>" `
  --force
```

仅当目标文件是本脚本此前生成的结果时使用 `--force`。若用户手工编辑过目标文件，先保留副本或改用新输出目录。

5. 完整阅读生成的文档和表格，修正任何错分、重复、乱码或不清晰的机制建议。
6. 在回复中给出：
   - 当日有效反馈数；
   - `命中 / 部分命中 / 失配 / 待判断` 数量；
   - 最重要的 1–3 条岗位补充或机制观察；
   - 可点击的复盘文档和 CSV 表路径。
7. 若有效反馈少于 5 条，明确说明样本很小，只做方向性观察，不把比例当稳定指标。

## 输出规则

- 使用用户的语言，默认输出简洁中文。
- 将事实、机制判断和规则建议分开写。
- 用 `待确认` 表示确实需要补充的信息，不自行补全。
- 严格命中率只计算 `hit / (hit + partial + miss)`。
- 方向有效率只计算 `(hit + partial) / (hit + partial + miss)`。
- 不把 `pending` 放入分母。
- 不把面试未通过自动判定为机制失配；先看失败原因是否与推荐依据相关。
- 不把候选人主动放弃、薪资变化、流程取消等外部结果直接当作匹配错误。
- 对公司/岗位画像的新增内容注明反馈来源和置信度。
- CSV 使用 UTF-8 with BOM，确保中文可直接在 Excel 中打开。
- 用户明确需要 `.xlsx` 时，先生成并核对 CSV，再使用 `$spreadsheets` 转为工作簿。

## 与其他招聘 Skill 的边界

- 需要首次评估候选人与岗位适配度时，使用 `$candidate-fit-tracker`；本 skill 负责沉淀后续反馈和每日机制复盘。
- 需要生成单个候选人的客户提报时，使用 `$candidate-client-handoff`。
- 同一条客户反馈可以同步更新候选人筛选表，但不要在两个 skill 的本地文件中写出相互冲突的结论。

## 参考文件

- `references/event-schema.md`：JSONL 字段、受控值和事件示例。
- `references/output-spec.md`：晚间文档和机制反馈表的内容标准。
- `scripts/render_daily_review.py`：从当天 JSONL 生成复盘文档、Markdown 表和 CSV 表。
