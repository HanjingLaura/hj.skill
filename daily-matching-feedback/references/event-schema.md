# Daily Feedback Event Schema

每行必须是一个 UTF-8 JSON 对象。一个对象表示一次可独立判断的反馈事件。

## 字段

| 字段 | 必填 | 内容 |
| --- | --- | --- |
| `date` | 是 | `YYYY-MM-DD` |
| `company` | 至少与 role 有一个 | 公司或客户名称 |
| `role` | 至少与 company 有一个 | 岗位名称或稳定 Context ID |
| `candidate` | 否 | 候选人；岗位级反馈留空 |
| `original_recommendation` | 否 | 原始结论，如 `强推`、`可聊`、`不建议` |
| `original_score` | 否 | 原始分数或区间，保留原口径 |
| `match_basis` | 否 | 当时推荐或不推荐的关键依据 |
| `feedback` | 否 | 客户、面试官、招聘方或候选人的明确反馈 |
| `feedback_source` | 否 | 来源角色，不保存不必要的私人联系方式 |
| `outcome` | 否 | 阶段或结果，如 `约面`、`通过`、`拒绝`、`offer` |
| `role_supplement` | 否 | 反馈揭示的公司/岗位新增信息 |
| `mechanism_judgment` | 是 | `hit`、`partial`、`miss`、`pending` |
| `issue_type` | 是 | 见下方受控值 |
| `mechanism_note` | 否 | 判断依据；指出原机制答对或错在哪里 |
| `generalizability` | 是 | `candidate-specific`、`company-role-specific`、`mechanism-general` |
| `generalizable_lesson` | 否 | 可复用的筛选/匹配结论；不能泛化时留空 |
| `confidence` | 是 | `high`、`medium`、`low` |
| `rule_action` | 是 | `apply`、`observe`、`no_change` |
| `next_action` | 否 | 补信息、改岗位画像、调权重、复查历史人选等 |
| `evidence_source` | 否 | 文件名、聊天时间或其他可定位来源 |

## `issue_type` 受控值

- `none`：没有明显误差。
- `false-positive`：推荐过高，实际明确不匹配。
- `false-negative`：推荐过低或漏推，实际明确匹配。
- `role-understanding`：岗位画像或岗位边界理解错误。
- `depth-or-level`：方向对，但能力深度、职级或 ownership 判断偏差。
- `hard-constraint`：地点、薪资、学历、行业、时间等明确硬条件遗漏。
- `evidence-gap`：原判断依据不足或关键词替代了项目证据。
- `preference-mismatch`：公司偏好、团队风格或候选人方向不一致。
- `timing-or-process`：流程、到岗、竞争 offer 等非能力因素。
- `data-quality`：输入缺失、过期、冲突或关联到错误岗位/人选。
- `external-factor`：岗位取消、HC 变化等机制外因素。
- `pending`：当前无法归因。

## 判断约束

1. 没有明确反馈时使用 `pending`，不要从沉默推断拒绝。
2. 面试通过不一定是完全命中；若反馈明确指出级别或方向偏差，可使用 `partial`。
3. 面试失败不一定是失配；若原机制已标注同一风险，可使用 `hit` 或 `partial`。
4. 候选人拒绝机会、薪资临时变化或岗位取消通常归为 `external-factor` 或 `timing-or-process`，不要直接修改能力匹配权重。
5. 单条候选人反馈默认 `candidate-specific`。只有反馈直接定义岗位偏好或硬条件时，才升级为 `company-role-specific`。
6. `mechanism-general` 需要跨人选、跨岗位重复证据，或用户明确确认其为通用规则。

## 示例

```json
{"date":"2026-07-24","company":"示例科技","role":"Agent 算法工程师","candidate":"张三","original_recommendation":"强推","original_score":"88/100","match_basis":"有 Agent 评测与强化学习项目","feedback":"技术方向认可，但项目 ownership 不够，按中级而非资深评估","feedback_source":"客户面试官","outcome":"一面未通过","role_supplement":"资深档必须证明端到端 owner 经验","mechanism_judgment":"partial","issue_type":"depth-or-level","mechanism_note":"方向命中，但职级深度判断偏高","generalizability":"company-role-specific","generalizable_lesson":"该岗位资深档提高端到端 ownership 权重","confidence":"high","rule_action":"apply","next_action":"更新该岗位资深档评分说明并复查 80 分以上人选","evidence_source":"用户当日反馈"}
```
