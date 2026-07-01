# 招聘初筛助手

[English](README.md) | [中文](README.zh-CN.md)

这是一个可复用的 Codex skill，用来准备候选人电话初筛话术，并把电话后的沟通记录整理成结构化评估。

公开 skill 只保存通用招聘流程、模板和评估框架。具体公司的流程、电话话术、岗位 JD、候选人画像和内部口径，应该放在 `local/company-context.local.md`，这个目录会被 Git 忽略。

## 能做什么

- 根据候选人简历或主页，生成一份针对 TA 的电话初筛话术。
- 把公司介绍和岗位亮点改写得更贴近候选人的背景和动机。
- 生成简历追问、必问题、风险追问和收尾话术。
- 给电话过程准备记录清单。
- 根据电话后的沟通内容，分析推荐点、风险点、缺失信息和下一步建议。
- 生成给 leader 或招聘负责人的内部同步话术。

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
  local/
    company-context.local.md
    call-notes.local.md
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

如果这个 skill 不在 Codex 的 skills 目录里，请先把 `recruiting-screening-assistant/` 文件夹复制到 Codex skills 目录，例如 `~/.codex/skills/recruiting-screening-assistant`。

## 日常使用

你可以对 Codex 说：

```text
请使用 $recruiting-screening-assistant 根据这份候选人简历，生成一份 10 分钟电话初筛话术。
```

也可以说：

```text
请使用 $recruiting-screening-assistant 分析这份电话记录，输出推荐点、风险点和下一步建议。
```

或：

```text
请使用 $recruiting-screening-assistant 把这份电话话术改得更自然、更像真人沟通。
```

## 推荐工作流

1. 用户提供候选人简历、投递岗位和来源。
2. Codex 读取本地岗位背景和流程，生成候选人专属电话话术。
3. 用户修改话术并进行电话沟通。
4. 用户把电话记录发给 Codex。
5. Codex 输出推荐点、风险点、缺失信息、下一步建议和内部同步话术。
6. 如果有新的有效问题或判断标准，再沉淀回本地公司上下文。

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
- 公司内部话术、JD、评分卡或流程细节
