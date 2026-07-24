# Technical Candidate Ranking Policy

Score only candidates who have passed hard role and education screening.

## Score Weights (100)

| Dimension | Weight | Main evidence |
|---|---:|---|
| School background | 10 | Full visible education chain, institution quality |
| Major-company/platform experience | 10 | Scale and quality of the actual engineering platform |
| Career stage | 5 | Relevant work years, not direct birth-age judgment |
| Technical scarcity | 20 | Supply/demand, replacement difficulty, niche depth |
| Technical depth | 20 | Architecture, fundamentals, performance, core modules, ownership |
| Technical breadth | 10 | Useful cross-domain engineering coverage |
| Project complexity and results | 20 | Scale, difficulty, measurable outcomes, production landing |
| Stability and credibility | 5 | Timeline consistency, evidence quality, continuity |

## Score Anchors

### School background (10)

- 10: top domestic or global institution.
- 9: 985 or comparable institution.
- 8: 211, Double First-Class, or strong overseas institution.
- 5: other public bachelor's institution.
- 3 or lower: incomplete or weakly evidenced education; conservative mode normally excludes before scoring when the hard chain cannot be verified.

### Major-company/platform experience (10)

- 10: first-tier technology company or platform with core engineering responsibility.
- 8-9: leading or well-established technical platform.
- 6: credible mid-sized platform with meaningful engineering scope.
- 4: small, unclear, or lightly evidenced platform.

Do not award points for a famous company when the candidate's role there was non-technical.

### Career stage (5)

- 5: 3-9 relevant work years.
- 4: 2 or 10-12 years.
- 2: 1 or 13-15 years.
- 1: 16-20 years.
- 0: no relevant experience or more than 20 years.

Use relevant work years as a job-fit proxy. Do not rank directly on protected or sensitive personal characteristics.

### Technical scarcity (20)

Highest anchors include inference frameworks, LLM post-training/alignment, embodied intelligence, chip/SoC, autonomous-driving localization and perception, low-level drivers, and rare materials/process expertise. Mature general backend, frontend, data, QA, or standard application roles score lower unless the resume proves unusually rare expertise.

### Technical depth (20)

Award for bottom-up technical understanding, architecture, performance work, core-module ownership, 0-to-1 construction, incident/problem resolution, published research, patents, open source, or sustained specialization. Separate personal contribution from team or company claims.

### Technical breadth (10)

Award useful cross-domain coverage such as model plus data plus backend, frontend plus Node plus engineering systems, hardware plus firmware plus validation, or testing plus platform plus performance. Keyword lists without applied evidence do not earn full credit.

### Project complexity and results (20)

Award for production systems, large scale, high concurrency, complex reliability or safety constraints, multi-system integration, measurable performance/quality/cost improvements, and clear ownership. Prefer metrics and shipped results over generic responsibility statements.

### Stability and credibility (5)

Award for a coherent timeline, reasonable tenure, internally consistent claims, and clear evidence. Deduct for repeated short tenure, unexplained contradictions, weak extraction, or unverifiable claims.

## Tie-Break Order

1. Technical scarcity plus technical depth.
2. Project complexity and results.
3. Major-company/platform experience.
4. School background.
5. Name for deterministic output.

## Naming

- Sort descending by the score and tie-break order.
- Use three-digit ranks for fewer than 1,000 retained resumes.
- Output filename: `001-姓名-期望地点.ext`.
- Use the resume-internal name; only use a resume-displayed alias when no other name is available.
- Use `未提及` unless the resume explicitly states an expected location.
