# 招聘初筛助手

[English](README.md) | [中文](README.zh-CN.md)

这是一个可复用的 Codex skill，用来准备候选人电话初筛话术、分析电话后的沟通记录，并维护一个按推荐顺序排序的 Markdown 候选人总表。

公开 skill 只保存通用招聘流程、模板、评估框架和候选人表格结构。具体公司的流程、电话话术、岗位 JD、候选人画像、内部口径、电话记录和真实候选人数据，都应该放在 `local/`，这个目录会被 Git 忽略。

## 能做什么

- 根据候选人简历或主页，生成一份针对 TA 的电话初筛话术。
- 把公司介绍和岗位亮点改写得更贴近候选人的背景和动机。
- 生成简历追问、必问题、风险追问和收尾话术。
- 给电话过程准备记录清单。
- 根据电话后的沟通内容，分析推荐点、风险点、缺失信息和下一步建议。
- 生成给 leader 或招聘负责人的内部同步话术。
- 维护一个按推荐顺序排序的 Markdown 候选人总表。

## 候选人总表

电话后评估完成后，这个 skill 可以新增或更新 `local/candidate-tracker.local.md` 里的候选人行。

候选人总表按推荐顺序排序，包含这些字段：

- 推荐顺序
- 姓名
- 学校
- 年级
- 籍贯
- 是否可接受 6 个月稳定实习
- 最早到岗时间
- 是否使用国外大模型
- 推荐点
- 风险点

如果某个字段没有证据，应该写 `unknown`，不要猜候选人信息。

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

在仓库根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File recruiting-screening-assistant\scripts\reset-local-context.ps1
```

然后填写：

- `local/company-context.local.md`：公司介绍、招聘流程、岗位 JD、候选人画像、电话话术偏好。
- `local/call-notes.local.md`：某一次电话后的沟通记录，可选。
- `local/candidate-tracker.local.md`：电话初筛后的候选人总表。

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
请使用 $recruiting-screening-assistant 根据这次电话沟通更新候选人总表，缺失字段写 unknown。
```

## 推荐工作流

1. 用户提供候选人简历、投递岗位和来源。
2. Codex 读取本地岗位背景和流程，生成候选人专属电话话术。
3. 用户修改话术并进行电话沟通。
4. 用户把电话记录发给 Codex。
5. Codex 输出推荐点、风险点、缺失信息、下一步建议、内部同步话术和候选人总表更新。
6. 用户把更新后的表格保存到 `local/candidate-tracker.local.md`。

## 隐私说明

可以提交到 GitHub：

- `SKILL.md`
- `README.md`
- `README.zh-CN.md`
- `agents/openai.yaml`
- `references/*.md`
- `scripts/reset-local-context.ps1`

不要提交到 GitHub：

- `local/`
- 候选人简历
- 带个人信息的电话记录
- 包含真实候选人的候选人总表
- 公司内部话术、JD、评分卡或流程细节
