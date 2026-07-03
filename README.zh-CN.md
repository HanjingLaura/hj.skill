# hj.skill

[English](README.md) | [中文](README.zh-CN.md)

`hj.skill` 是一组可复用的 Codex skills，用来把真实工作流沉淀成稳定的小工具。

这个仓库的核心思路是：公开部分只放可复用方法，私人资料和公司内部信息都放在本地。这样别人可以直接复用 skill 的方法，每个人也可以在自己的电脑里维护一份不会提交到 GitHub 的私人记忆。

## 快速开始

1. 克隆这个仓库。
2. 从下面的列表里选择一个想用的 skill 文件夹。
3. 把这个 skill 文件夹复制到 Codex 的 skills 目录。
4. 运行该 skill 的初始化脚本，生成会被忽略的 `local/` 文件。
5. 在生成的 `local/*.local.md` 文件里填写你自己的背景、岗位、流程或偏好。
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
| [`recruiting-screening-assistant`](recruiting-screening-assistant/README.zh-CN.md) | 生成招聘电话初筛话术、分析电话记录，并维护按推荐顺序排序的候选人总表。 | `powershell -ExecutionPolicy Bypass -File recruiting-screening-assistant\scripts\reset-local-context.ps1` |

每个 skill 的详细用法和示例，请看对应目录下的 README。

## 通用使用方式

这个仓库里的 skill 基本遵循同一套循环：

1. 用公开模板初始化本地私人文件。
2. 把你的真实背景、案例、偏好、岗位信息或流程细节写进 `local/*.local.md`。
3. 让 Codex 调用对应 skill，例如：`请使用 $hackathon-application-answerer 帮我回答这份报名表`。
4. 检查、修改并使用输出结果。
5. 把有用的最终版本和新的经验沉淀回本地文件。

这样公开 skill 保持干净，你自己的本地版本也会越用越贴近你。

## 目录结构

```text
skill-name/
  SKILL.md
  README.md
  README.zh-CN.md
  agents/
    openai.yaml
  references/
    public-template-or-guidance.md
  scripts/
    setup-or-reset-script.ps1
  local/
    private-context.local.md
```

`references/` 放公开模板和通用方法，`local/` 放私人记忆。`local/` 不应该提交到 Git。

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
