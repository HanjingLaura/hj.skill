# 黑客松报名问答助手

[English](README.md) | [中文](README.zh-CN.md)

这是一个可复用的 Codex skill，用来回答黑客松、创新营、创业比赛、加速器、奖学金项目、开发者活动等报名表中反复出现的问题。

它的核心思路是：公开文件只保存通用方法，私人文件保存你的真实背景和过往答案。这样既能避免每次都重新解释自己，也不会把个人信息提交到 GitHub。

## 能做什么

- 根据报名表问题，生成可直接复制的中文或英文答案。
- 识别“表面不同但本质相似”的问题，并复用过往答案。
- 把你的个人背景、项目经历、技能、偏好和表达风格整理成结构化资料。
- 在真实报名过程中不断积累可复用答案库。
- 根据字数限制生成短版、中版或更完整的版本。
- 在回答后提示哪些内容值得保存，方便下一次继续迭代。

## 适合的问题

- 自我介绍
- 为什么参加这个活动
- 你想做什么项目
- 你能为团队带来什么
- 技术能力、产品能力或设计能力说明
- 过往项目经历
- 团队协作、冲突处理、价值观问题
- 对某个赛道、行业、人群或社会议题的理解

## 目录结构

```text
hackathon-application-answerer/
  SKILL.md
  README.md
  README.zh-CN.md
  agents/
    openai.yaml
  references/
    profile.template.md
    answer-bank.template.md
    question-patterns.md
  local/
    profile.local.md
    answer-bank.local.md
  scripts/
    reset-local-memory.ps1
```

`references/` 放公开模板和通用题型策略。`local/` 放你的私人资料和过往答案，不应该提交到 GitHub。

## 第一次使用

在仓库根目录运行：

```powershell
Copy-Item hackathon-application-answerer\references\profile.template.md hackathon-application-answerer\local\profile.local.md
Copy-Item hackathon-application-answerer\references\answer-bank.template.md hackathon-application-answerer\local\answer-bank.local.md
```

然后填写：

- `local/profile.local.md`：你的真实背景、项目、技能、偏好、限制条件。
- `local/answer-bank.local.md`：你提交过的好答案、可复用片段、修改习惯。

## 日常使用

你可以直接对 Codex 说：

```text
请使用 $hackathon-application-answerer 帮我回答这份黑客松报名表，答案用中文，每题控制在 200 字以内。
```

也可以说：

```text
请使用 $hackathon-application-answerer 优化这段答案，并告诉我哪些内容值得保存到答案库。
```

或：

```text
请使用 $hackathon-application-answerer 根据我的个人资料，给这个问题生成三个版本：简短版、真诚版、偏产品视角版。
```

## 本地记忆怎么迭代

每完成一次真实报名，都建议做三件事：

1. 把最终提交的好答案保存到 `local/answer-bank.local.md`。
2. 把新补充的项目事实、经历、偏好保存到 `local/profile.local.md`。
3. 删除明显过时、已经不代表你的内容。

这样这个 skill 会越来越像“懂你的人”，而不是每次从零开始的通用问答工具。

## 清空或重建本地记忆

如果你想完全删掉之前的个人内容，重新开始蒸馏自己，可以运行：

```powershell
powershell -ExecutionPolicy Bypass -File hackathon-application-answerer\scripts\reset-local-memory.ps1
```

这个命令会用公开模板重建：

- `local/profile.local.md`
- `local/answer-bank.local.md`

如果你只想删除本地记忆文件，不自动重建模板，可以运行：

```powershell
powershell -ExecutionPolicy Bypass -File hackathon-application-answerer\scripts\reset-local-memory.ps1 -DeleteOnly
```

## 隐私说明

可以提交到 GitHub：

- `SKILL.md`
- `README.md`
- `README.zh-CN.md`
- `agents/openai.yaml`
- `references/*.template.md`
- `references/question-patterns.md`
- `scripts/reset-local-memory.ps1`

不要提交到 GitHub：

- `local/`
- `*.local.md`
- 简历、作品集、截图、生成的 PDF
- 任何包含真实联系方式、私人经历、未公开项目细节的文件

根目录 `.gitignore` 已经默认忽略这些私人文件。

## 推荐工作流

1. 用户提供简历、个人主页、过往报名内容或项目描述。
2. Codex 帮用户整理进 `local/profile.local.md` 和 `local/answer-bank.local.md`。
3. 用户提供新的报名表问题。
4. Codex 根据本地资料生成答案。
5. 用户修改并提交最终版本。
6. Codex 再把最终版本沉淀回本地答案库。

这个循环越多，回答会越贴近用户本人。
