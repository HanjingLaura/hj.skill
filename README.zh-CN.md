# hj.skill

[English](README.md) | [中文](README.zh-CN.md)

`hj.skill` 是一个个人 Codex skill 工作区，用来收集小而可复用的 skill。

这个仓库用来把真实生活和工作中反复出现的问题，沉淀成一个个小而稳定的 skill。比如活动报名问答、作品集整理、项目经历改写、面试准备、调研分析，或者任何不想每次都从长对话里重新解释一遍的任务。

公开仓库里只放可复用的流程、模板和示例；真正的个人资料、过往答案、简历、生成文件和本地实验内容都保留在本地，并通过 `.gitignore` 排除。

## 已包含的能力

| 名称 | 用途 | 状态 |
| --- | --- | --- |
| [`hackathon-application-answerer`](hackathon-application-answerer/README.zh-CN.md) | 起草、改写和迭代黑客松、创新营、创业比赛等活动报名表答案。 | 可用 |

之后如果出现新的高频需求，可以继续在这个仓库里增加新的 skill。

## 通用使用方式

这个仓库里的 skill 基本遵循同一套用法：

1. 选择和当前任务匹配的 skill。
2. 把公开模板文件复制成本地私人文件，例如从 `profile.template.md` 复制出 `profile.local.md`。
3. 在本地文件里填写真实背景、偏好、过往答案、项目案例和限制条件。
4. 让 Codex 调用对应 skill，例如：`请使用 $hackathon-application-answerer 帮我回答这份报名表`。
5. 检查、修改并提交 AI 生成的答案。
6. 把最终提交版本、你的修改习惯和新的补充信息沉淀回本地文件，让下一次回答更贴近你。

这样别人可以复用公开方法，而你自己的本地版本也能持续变得更懂你。

## 目录结构约定

一个典型 skill 目录大概长这样：

```text
skill-name/
  SKILL.md
  README.md
  README.zh-CN.md
  agents/
    openai.yaml
  references/
    profile.template.md
  local/
    profile.local.md
```

`references/` 放公开模板和通用资料，`local/` 放私人记忆。`local/` 不应该提交到 Git。

## 隐私约定

可以提交的公开文件：

- `SKILL.md`
- `README.md`
- `README.zh-CN.md`
- `agents/openai.yaml`
- `references/*.template.md`
- 不包含个人事实的通用参考文件

保持私有或忽略的文件：

- `local/`
- `*.local.md`
- `*.private.md`
- `private/`
- `tmp/`
- `output/`
- 生成的作品集、简历、截图、日志和一次性脚本

## 添加更多能力

新增 skill 时，建议沿用同样的分层：

1. 将可复用指令放入 `SKILL.md`。
2. 将非个人示例放入 `*.template.md`。
3. 将真实私人上下文放入 `local/*.local.md`。
4. 将本地或生成产物加入 `.gitignore`。
5. 发布前验证 skill。

目标是让这个仓库既能被其他人拿去改造成自己的工具箱，也能支持每个人在本地保留真正适合自己的私人版本。
