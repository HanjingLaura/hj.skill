# hj.skill

[English](README.md) | [中文](README.zh-CN.md)

`hj.skill` 是一组可复用的 Codex skills，用来把真实工作流沉淀成稳定的小工具。

这个仓库的核心思路是：公开部分只放可复用方法，私人资料和公司内部信息都放在本地。这样别人可以直接复用 skill 的方法，每个人也可以在自己的电脑里维护一份不会提交到 GitHub 的私人记忆。

## 快速开始

1. 克隆这个仓库。
2. 从下面的列表里选择一个想用的 skill 文件夹。
3. 把这个 skill 文件夹复制到 Codex 的 skills 目录。
4. 如果这个 skill 需要本地私人文件（见下表的初始化命令），在你希望保存私人资料的工作区里运行它的初始化脚本。默认会生成 `.hj-skill-local/<skill-name>/`。
5. 在生成的 `*.local.md` 文件里填写你自己的背景、岗位、流程或偏好。
6. 在 Codex 里用 `$skill-name` 调用对应 skill。

常见 Codex skills 目录：

```text
macOS / Linux: ~/.codex/skills/
Windows: C:\Users\<你的用户名>\.codex\skills\
```

复制后的目标路径示例：

```text
~/.codex/skills/hackathon-application-answerer
~/.codex/skills/recruiting-screening-assistant
```

你也可以把这个仓库当成开发工作区：先在这里修改和迭代 skill，准备好之后再把单个 skill 文件夹复制到 Codex 的 skills 目录。

## 已包含的 Skills

| Skill | 用途 | 初始化命令 |
| --- | --- | --- |
| [`hackathon-application-answerer`](hackathon-application-answerer/README.zh-CN.md) | 起草、改写和迭代黑客松、创新营、创业比赛等活动报名表答案。 | `powershell -ExecutionPolicy Bypass -File hackathon-application-answerer\scripts\reset-local-memory.ps1` |
| [`recruiting-screening-assistant`](recruiting-screening-assistant/README.zh-CN.md) | 生成招聘电话初筛话术、评估候选人作业、分析电话记录，并维护按推荐顺序排序的候选人总表。 | `powershell -ExecutionPolicy Bypass -File recruiting-screening-assistant\scripts\reset-local-context.ps1` |
| [`candidate-fit-tracker`](candidate-fit-tracker/SKILL.md) | 根据真实客户岗位上下文评估候选人匹配度，整理证据、风险、下一步动作和筛选记录。 | `powershell -ExecutionPolicy Bypass -File candidate-fit-tracker\scripts\reset-local-context.ps1` |
| [`candidate-comments-template`](candidate-comments-template/SKILL.md) | 根据候选人简历和聊天记录生成可直接转发的 comments 模板，包含背景概述、看机会原因、薪酬、级别和绩效。 | 不需要初始化 |
| [`ai-news-gossip-comic`](ai-news-gossip-comic/SKILL.md) | 抓取并核实最近的 AI 新闻，用八卦/搞笑风格改写成新闻卡片、分镜表和多格漫画提示词，并生成漫画。 | 不需要初始化 |

每个 skill 的详细用法和示例，请看对应目录下的 README 或 SKILL.md。

## 通用使用方式

这个仓库里的 skill 基本遵循同一套循环：

1. 用公开模板初始化本地私人文件。
2. 把你的真实背景、案例、偏好、岗位信息或流程细节写进 `.hj-skill-local/<skill-name>/*.local.md`，或者通过 `-LocalRoot` 指定其他目录。
3. 让 Codex 调用对应 skill，例如：`请使用 $hackathon-application-answerer 帮我回答这份报名表`。
4. 检查、修改并使用输出结果。
5. 把有用的最终版本和新的经验沉淀回本地文件。

这样公开 skill 保持干净，你自己的本地版本也会越用越贴近你。

## 目录结构

```text
skill-name/
  SKILL.md                  # 必需：skill 的可复用指令
  README.md                 # 可选：英文说明
  README.zh-CN.md           # 可选：中文说明
  agents/
    openai.yaml             # Codex agent 配置
  references/               # 可选：公开模板和通用方法
    public-template-or-guidance.md
  scripts/                  # 可选：本地文件初始化/重置脚本
    setup-or-reset-script.ps1
```

只有 `SKILL.md` 是必需的；`references/` 和 `scripts/` 按 skill 的需要添加。`references/` 放公开模板和通用方法。私人记忆应该放在安装后的 skill 文件夹外面，通常是当前工作区的 `.hj-skill-local/<skill-name>/`。

## 隐私规则

可以提交：

- `SKILL.md`
- `README.md`
- `README.zh-CN.md`
- `agents/openai.yaml`
- 不包含私人信息的 `references/*.md`
- 不包含私人数据的通用脚本

不要提交：

- `local/`
- `.hj-skill-local/`
- `*.local.md`
- `*.private.md`
- 简历、候选人记录、作品集、截图、日志、生成文件、公司内部流程或内部话术

根目录 `.gitignore` 已经默认忽略本地私人文件。

## 添加新 Skill

新增 skill 时，建议遵循这个结构：

1. 将可复用指令放入 `SKILL.md`。
2. 将公开模板和通用方法放入 `references/`。
3. 将真实个人资料或公司内部信息放入 `local/*.local.md`。
4. 如果需要生成本地模板，添加一个小的初始化或重置脚本。
5. 发布前验证 skill。

这样这个仓库既能被别人拿去改造成自己的工具箱，也能支持每个人在本地保留真正适合自己的私人版本。
