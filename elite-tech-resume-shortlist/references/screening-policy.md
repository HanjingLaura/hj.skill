# Screening policy

## Decision order

Apply checks in this order:

1. exact and semantic duplicate;
2. complete education-chain hard exclusions;
3. explicit age evidence when an age rule was requested;
4. qualifying school evidence and non-overlapping tier assignment;
5. actual large-company employment context;
6. hands-on technical role;
7. formal versus internship tier.

Do not score or rank a candidate who fails a hard check.

## Education evidence

### Tier 1: elite school

Require at least one qualifying degree from the task's declared elite tier:

- historical 985/211 project institution; or
- an overseas institution within the declared ranking or reputation threshold.

Set an explicit overseas threshold before reviewing. If the user does not provide one, use a conservative current QS or THE top-100 threshold and disclose it. A qualifying degree is sufficient even if another public degree is not in the target tier, provided no hard exclusion appears.

### Tier 2: conservative expanded school set

Tier 2 must be mutually exclusive with Tier 1. It accepts:

- current Double First-Class institutions that are not 985/211; and
- reputable public first-tier universities on an explicit task-local whitelist.

Do not equate “public undergraduate institution” with “一本” or “respectable school.” Use a conservative whitelist approved or disclosed for the task. Record every included Tier 2 institution in Methodology. When the school cannot be classified confidently, use `school-tier-unverifiable`.

### Hard exclusion

Exclude if any visible degree segment is:

- junior college, higher vocational, associate degree, adult junior college, or equivalent;
- 专升本、专接本、专插本、高起本 or another upgrade path;
- a private bachelor's institution or historical independent college when the policy forbids them;
- missing enough detail that the complete bachelor-and-above chain cannot be verified in strict mode.

Judge historical institution status using the enrollment/graduation period when possible. Do not infer that every school ending in “学院” is private.

### Common mistakes

- Matching `电子科技大学` inside `杭州电子科技大学`.
- Treating an exchange university as the degree-granting school.
- Treating a certificate, MOOC, laboratory, or executive course as a degree.
- Checking only the master's school and ignoring the bachelor's route.
- Treating “第二学位” as incomplete without reading the complete line and primary major.

## Age evidence

Apply age only when the user explicitly requests it. Record the as-of date in ISO format.

Accept:

- a stated age such as `年龄：28` or `28岁`;
- an explicitly labeled birth date or year such as `出生日期：1998-05-10`, `出生年月：1998.05`, or `DOB: 1998`.

For year-only birth evidence, use the conservative interpretation: the birthday may already have occurred in the as-of year. If that age reaches the ceiling, use `age-boundary-unverifiable` unless the exact birthday is available.

Reject as age evidence:

- graduation year;
- first-job year or claimed years of experience;
- appearance or photograph;
- seniority, title, family status, or probabilistic inference.

If explicit age evidence is absent, use `age-unverifiable` and keep the candidate out of selected tables. If evidence conflicts, use `age-conflict-review` until manually resolved.

## Large-company evidence

### Accept

- Formal technical employment at the company or a verified employing subsidiary.
- A technical internship, but place internship-only candidates in a separate tier.
- Acquired or spun-out entities only when the resume shows the employment relationship and the task policy accepts it.

### Reject as evidence

- AWS, Azure, Alibaba Cloud, Google API, or another tool or platform in a technology stack.
- A famous company listed as a customer, supplier, competitor, certification issuer, contest organizer, or research partner.
- “Compatible with,” “benchmarked against,” model or paper citations, or an email domain.
- A famous company where the actual role was product, strategy, sales, operations, legal, design, or another non-technical function.

For each accepted company, retain a short work-history excerpt containing company, role, dates, and technical responsibility.

## Pure technical evidence

Strong evidence includes:

- production code, algorithms, models, data pipelines, hardware, drivers, protocols, test frameworks, automation platforms, infrastructure, or security engineering;
- architecture with direct implementation ownership;
- measurable engineering results, performance work, reliability work, or shipped systems.

Weak evidence includes:

- keyword-only skill lists;
- “worked with R&D” without technical contribution;
- product roadmaps, delivery coordination, PMO, business analysis, presales, or team management without hands-on work.

Technical QA qualifies only when the resume proves automation, platform, coding, performance, protocol, model evaluation, or comparable engineering work.

## Conservative resolution

Use `excluded` rather than optimistic inclusion when a strict rule cannot be verified after:

1. text extraction;
2. layout or visual review;
3. institution and company context review.

State the unresolved fact in the exclusion reason. Never invent an age, school type, corporate relationship, or employment status.
