# Tech Talent

[English](README.md) | [中文](README.zh-CN.md)

Tech Talent 是一个 local-first 的 Codex 工作流，用于公开技术人才检索、证据复核和受控邮件触达；它不是自主招聘机器人。

## 本目录包含的内容

本目录只发布 **可复用的 Skill 指令和产品契约**，不包含 Python 运行时、虚拟环境、SQLite 数据库、凭据或生成输出。

完整的本地 Core 和 CLI 单独管理，默认位于 `~/.codex/state/tech-talent/`，由源仓库的 `scripts/bootstrap.py` 和 `uv.lock` 引导安装。

## 子 Skill

Tech Talent 暴露四个薄 Skill，按严格阶段顺序执行：

| 阶段 | Skill | 用途 |
| --- | --- | --- |
| 1 | [`talent-search`](skills/talent-search/SKILL.md) | 有边界的公开检索和搜索入库。 |
| 2 | [`candidate-review`](skills/candidate-review/SKILL.md) | 人工复核身份、证据和联系方式来源；通过 CAS 保护记录批准/拒绝决定。 |
| 3 | [`candidate-outreach`](skills/candidate-outreach/SKILL.md) | DB 化 Campaign、精确邮件起草/审批、HMAC Dry-run、显式发送授权和持久 SMTP 投递。 |
| 4 | [`reply-monitor`](skills/reply-monitor/SKILL.md) | Polling-only IMAP 收件箱同步、确定性分类和人工复核歧义条目。 |

每个子 Skill 只路由确定性 Core 命令，并保留各自的 stage gate。

## 安全模型

- **Fail-closed / 人工审批**：每个真实批次都必须由人明确批准精确的收件人、发件人、主题、正文和 Dry-run 数量。
- **禁止自主发送**：准备触达的一般请求不等于发送许可。
- **寻访/触达分离**：寻访链路永不起草或发送邮件；触达链路永不发现新候选人。
- **隐私**：只使用公开页面、公开 API、仓库、论文和用户授权的本地导出。不登录招聘平台、不绕过访问控制、不采集凭据、不抓取候选人隐私数据。

## 产品契约

V1 权威边界见 [`docs/product-contract-v1.md`](docs/product-contract-v1.md)。

## Plugin 清单

[`.codex-plugin/plugin.json`](.codex-plugin/plugin.json) 为 Codex Plugin 壳层声明了四个 Skill。Plugin 尚未安装或发布。
