# 招聘初筛助手

[English](README.md) | [中文](README.zh-CN.md)

这是一个可复用的 Codex skill，用来准备候选人电话初筛话术、评估候选人作业、分析电话后的沟通记录，并维护一个按最终推荐顺序排序的 Markdown 候选人总表。

公开 skill 只保存通用招聘流程、作业评估标准、模板、评估框架和候选人表格结构。具体公司的流程、电话话术、岗位 JD、候选人画像、内部口径、电话记录、作业内容和真实候选人数据，都应该放在 `local/`，这个目录会被 Git 忽略。

## 能做什么

- 根据候选人简历或主页，生成一份针对 TA 的电话初筛话术。
- 把公司介绍和岗位亮点改写得更贴近候选人的背景和动机。
- 生成简历追问、必问题、风险追问和收尾话术。
- 给电话过程准备记录清单。
- 根据电话后的沟通内容，分析推荐点、风险点、缺失信息和下一步建议。
- 评估候选人的笔试作业、研究任务、case 任务或其他筛选作业。
- 生成给 leader 或招聘负责人的内部同步话术。
- 维护一个按最终推荐顺序排序的 Markdown 候选人总表。

## 候选人总表

电话后评估或作业评估完成后，这个 skill 可以新增或更新 `local/candidate-tracker.local.md` 里的候选人行。

候选人总表按最终推荐顺序排序，包含这些字段：

- 推荐顺序
- 姓名
- 学校
- 年级
- 籍贯
- 是否可接受 6 个月稳定实习
- 最早到岗时间
- AI/工具使用情况
- 软技能判断
- 作业情况
- 推荐点
- 风险点

如果某个字段没有证据，应该写 `unknown`，不要猜候选人信息或作业表现。

## 作业评估

收到候选人的笔试作业、研究任务、case 分析或筛选作业后，可以用这个 skill 做作业评估。

公开评估标准包括：

- 完成度与及时性
- 对任务的理解
- 信息搜集与资料质量
- 行业洞察与判断
- 结构化思维
- 执行细节
- 表达质量
- AI 工具使用（辅助信号）

作业结果会进入候选人总表的 `作业情况` 列，并可能影响最终推荐顺序。

## 目录结构

```text
recruiting-screening-assistant/
  SKILL.md
  README.md
  README.zh-CN.md
  agents/
    openai.yaml
  references/
    company-context.template.md
    screening-workflow.md
    evaluation-rubric.md
    assignment-rubric.md
    call-notes.template.md
    candidate-tracker.template.md
  local/
    company-context.local.md
    call-notes.local.md
    candidate-tracker.local.md
  scripts/
    reset-local-context.ps1
```

`references/` 放公开模板和通用方法，`local/` 放公司私有信息和候选人记录，不应该提交到 GitHub。

## 第一次使用

在你希望保存私人招聘资料的工作区里运行：

```powershell
powershell -ExecutionPolicy Bypass -File recruiting-screening-assistant\scripts\reset-local-context.ps1
```

默认会生成到 `.hj-skill-local/recruiting-screening-assistant/`。如果你想指定目录：

```powershell
powershell -ExecutionPolicy Bypass -File recruiting-screening-assistant\scripts\reset-local-context.ps1 -LocalRoot C:\path\to\private-recruiting-context
```

然后填写：

- `company-context.local.md`：公司介绍、招聘流程、岗位 JD、候选人画像、电话话术偏好、作业规则。
- `call-notes.local.md`：某一次电话后的沟通记录，可选。
- `candidate-tracker.local.md`：电话初筛和作业评估后的候选人总表。

如果这个 skill 不在 Codex 的 skills 目录里，请先把 `recruiting-screening-assistant/` 文件夹复制到 Codex skills 目录，例如 `~/.codex/skills/recruiting-screening-assistant`。

## 日常使用

你可以对 Codex 说：

```text
请使用 $recruiting-screening-assistant 根据这份候选人简历，生成一份 10 分钟电话初筛话术。
```

也可以说：

```text
请使用 $recruiting-screening-assistant 分析这份电话记录，输出推荐点、风险点、下一步建议，并更新候选人总表。
```

或：

```text
请使用 $recruiting-screening-assistant 评估这份候选人作业，并更新候选人总表里的作业情况和推荐顺序。
```

## 推荐工作流

1. 用户寻访并初筛候选人简历。
2. Codex 读取本地岗位背景和流程，生成候选人专属电话话术。
3. 用户修改话术并进行电话沟通。
4. 电话面通过的候选人进入后续沟通渠道。
5. 用户发送并收集候选人作业。
6. 用户把电话记录或作业内容发给 Codex。
7. Codex 输出推荐点、风险点、缺失信息、下一步建议、内部同步话术、作业情况和候选人总表更新。
8. 用户把更新后的表格保存到私人 `candidate-tracker.local.md`。

## 隐私说明

可以提交到 GitHub：

- `SKILL.md`
- `README.md`
- `README.zh-CN.md`
- `agents/openai.yaml`
- `references/*.md`
- `scripts/reset-local-context.ps1`

不要提交到 GitHub：

- `.hj-skill-local/`
- `local/`
- 候选人简历
- 候选人作业原文
- 带个人信息的电话记录
- 包含真实候选人的候选人总表
- 公司内部话术、JD、评分卡或流程细节
