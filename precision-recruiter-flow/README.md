# 精准猎头流

适用于 Codex 桌面版的单岗位猎头工作流：先理解职位，再在 5 分钟内定标杆，随后用 2 小时定向 sourcing，人工电话跟进，并在每天 12:00、18:00 复盘。触发语包括「新岗位」「开一个单」「用精准猎头流」，或直接粘贴 JD 要求按猎头流程推进。

## 安装

```bash
git clone https://github.com/HanjingLaura/hj.skill.git
cp -R hj.skill/precision-recruiter-flow ~/.codex/skills/
```

Windows 可将 `precision-recruiter-flow` 文件夹复制到 `C:\Users\<用户名>\\.codex\\skills\\`。安装后在 Codex 桌面版输入 `使用 $precision-recruiter-flow 开一个新岗位`。

## 文件说明

- `SKILL.md`：触发条件、流程、状态机、硬规则和 Automation 协议。
- `agents/openai.yaml`：桌面版显示名、简介和默认提示词。
- `references/templates/`：开岗时复制的 7 个岗位文件及复盘模板。
- `references/images/`：目录树、状态机、Automation 时间线示意图。
- `.hj-skill-local/precision-recruiter-flow/jobs/<slug>/`：工作区私有岗位数据；简历、通话和复盘不提交 git。

![目录树](references/images/directory-tree.svg)

![状态机](references/images/state-machine.svg)

![Automation 时间线](references/images/automation-timeline.svg)

## 完整用法

1. 说“新岗位：……”，skill 创建 `.hj-skill-local/precision-recruiter-flow/jobs/<slug>/`，复制模板。
2. 共同整理 JD，写入 `01-职位理解.md`；你确认“理解 OK”后才进入下一步。
3. Codex 桌面版自行创建一次「5 分钟定标杆」Automation：读取 01 和 leader 样板、自搜高匹配、客户面到 offer、在岗画像，写出 `02-标准简历.md`。
4. 你确认标杆后，创建「Sourcing 2 小时」Automation：按公司、业务线、级别、地点、薪资拆搜索，目标约 10 个准人，更新 `05-搜索清单.md`、`03-候选人-list.md` 和 `resumes/`。禁止过宽搜；不自动外呼、不自动推客户。
5. 使用 `04-电话话术.md` 人工打电话，每次把时间、候选人、结果、要点纪要、下次动作写入 `07-通话记录.md`，再更新 03 的状态、通话次数和最近触达日。
6. 岗位进行中创建每日 12:00、18:00 的复盘 Automation，生成 `reviews/YYYY-MM-DD-HH-复盘.md`。复盘检查准人进度、呼出、是否搜超时、标杆/职位理解是否回写，并给出下一步 1–2 条。

`06-目标公司-核心人.md` 是公司地图（在岗对标人、上级/协作、同方向未触达、行业标杆、可选离职不久），含“是否已转入 list”；开始打后转入 03。03 只放本单已决定建联、在打或在推的人。人工肉眼搜建议 ≤4h/日，日有效呼出参考 20–30。

如果桌面版不能由 skill 直接创建 Automation，skill 会输出可复制的触发、prompt、读写文件配置，仍由你在 Automations 面板创建。
