---
name: ai-news-gossip-comic
description: Fetch and verify the latest five AI news stories, rewrite them in lively Chinese gossip/comedy style, turn them into a storyboard, and generate a multi-panel comic with mixed square, rectangular, diagonal, and trapezoid panels. Use when the user asks for 最新 AI 新闻、AI 新闻漫画、科技八卦、新闻段子、漫画分镜、多格漫画, or a recurring news-to-comic workflow.
---

# AI News Gossip Comic

Produce a source-backed Chinese AI-news comic from current reporting. Keep facts accurate while making the presentation playful.

## Workflow

1. Confirm only preferences that materially change the result: target platform/aspect ratio, visual style, audience, and whether to generate the image now. If unspecified, use a vertical 4:5 social post, colorful editorial cartoon style, general tech audience, and generate the image.
2. Search the web for AI stories published or materially updated in the last 72 hours. If fewer than five substantial stories exist, widen to seven days and disclose the window.
3. Prefer primary sources: company announcements, research papers, regulator statements, court documents, and official repositories. Use reputable reporting as secondary confirmation. Never rely on search snippets alone.
4. Select five distinct stories using recency, significance, source quality, visual potential, and topic diversity. Avoid five minor updates from one company.
5. Record title, event date, source links, verified facts, uncertainty, and why it matters. Distinguish the event date from the article publication date.
6. Rewrite each story as witty commentary. Preserve names, numbers, chronology, and attribution. Label rumor or disputed claims explicitly. Do not invent quotes, motives, scandals, private behavior, or allegations. Punch up at products, strategies, and public corporate behavior; avoid harassment and protected-class stereotypes.
7. Produce five separate comic pages: exactly one news story per page. Give every story its own dramatic setup, escalation, reveal, reaction, and punchline. Never compress all five stories into one roundup page. Use a recurring host/narrator to make the five-page series feel connected. Read [references/output-contract.md](references/output-contract.md) before drafting.
8. Create a 4–7 panel map for each news story, yielding five independent multi-panel storyboards. Mix square/rectangular panels with 1–2 diagonal or trapezoid panels per page. Keep reading order unmistakable and reserve gutters.
9. Write image prompts that specify the complete page layout, each panel's composition, recurring character continuity, palette, lettering zones, and prohibited artifacts. Keep essential Chinese text short because image models often distort typography.
   Default narrative direction: embed each verified news item inside an original, self-contained melodramatic gossip story rather than explaining it directly. First extract the news's real tension—launch rivalry, price gap, access restriction, safety conflict, alliance, replacement, comeback, or policy pressure—then choose a fitting fictional genre and cast. Vary genres across the five pages: possible frames include palace intrigue, dating-show love triangle, workplace succession battle, family inheritance feud, spy thriller, school rivalry, entertainment-industry scandal management, courtroom showdown, sports transfer drama, or fantasy guild politics. Technical facts must drive the plot as story mechanisms. Never include a presenter, journalist, microphone, news desk, or character speaking directly to the audience unless explicitly requested.
10. Generate the comic with the available image-generation tool. For reliable Chinese copy, prefer generating clean speech bubbles/caption boxes and then adding exact text in a layout tool when available. Inspect the result for missing panels, duplicated subjects, broken reading order, illegible text, factual mismatches, and unsafe caricature. Regenerate or repair if necessary.
11. Return the comic, a five-item source ledger with clickable links and dates, and a short disclosure that humorous lines are commentary rather than quotations.

## Freshness and sourcing rules

- Always browse; “latest” cannot be answered from memory.
- Cite every story near its factual summary and use direct source URLs.
- Do not claim exhaustive coverage. Say “selected five” rather than “the five most important” unless a ranking method was requested.
- Exclude sponsored content, content farms, duplicate syndication, and stories with no verifiable underlying event.
- If a breaking claim has only one weak source, omit it or mark it unverified and do not dramatize it as fact.

## Tone controls

Default to `spicy=3` on a 0–3 scale:

- `0`: straight news with light warmth.
- `1`: playful metaphors and gentle teasing.
- `2`: energetic tech gossip, punchlines, reaction beats, no fabricated scandal.
- `3`: tabloid-energy tech gossip with a dramatic headline, rivalry framing, reversals, reaction shots, savage metaphors, and a hard punchline. Aim satire at public product claims, benchmark theater, pricing, corporate strategy, and policy contradictions; retain all factual safeguards. Make it feel explosive through framing and wordplay, never through invented facts.

For `spicy=3`, use this beat pattern on every page: `爆点标题 → 谁在抢戏 → 事实炸点 → 圈内人式吐槽 → 反转/代价 → 收尾补刀`. Prefer phrases such as “连夜掀桌”, “贴脸开大”, “卷到冒烟”, “算盘珠崩一地”, and “台上秀肌肉，台下算电费” when they fit the verified facts. Do not repeat the same catchphrase across pages.

Default to a six-panel melodrama arc: `爆炸性关系登场 → 欲望/竞争升级 → 新闻事实化成剧情机关 → 第三方或隐藏条件闯入 → 反转揭示代价 → 狗血余震`. Do not force a mansion, locked gate, mysterious visitor, board meeting, cold anime heir, or closing aphorism. Select scenes and character archetypes from the news tension. For example, benchmarks may become rankings or auditions; model tiers may become rival contestants or siblings; pricing may become dowry, contract, rent, or restaurant bill; safety controls may become prenup clauses, school rules, court injunctions, or mission protocols; governance may become a chaotic family mediation, courtroom, summit, or neighborhood committee. Do not invent crimes, affairs, deaths, or misconduct about real entities.

Interpret “高校” as likely “搞笑” when the surrounding request asks for funny/gossip copy, but preserve a literal university/campus meaning when context supports it.

## Output order

Return artifacts in this order:

1. `今日 AI 瓜田` — five concise sourced news cards.
2. `趣味改写` — hook, setup, punchline, and factual anchor for each story.
3. `分镜表` — five separate tables, one per story; include panel number, shape, shot, action, dialogue/caption, and transition.
4. `五页漫画提示词` — one production-ready page prompt per story plus shared negative constraints.
5. Five generated comic images, one multi-panel page per news story, when image generation is available or requested.
6. `来源与声明` — direct links, dates, uncertainty notes, and commentary disclosure.

Never present comic dialogue as a real quotation unless the source contains that exact quote.
