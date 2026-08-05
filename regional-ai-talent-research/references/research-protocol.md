# Fixed research and evidence protocol

## Contents

1. Variable boundary
2. School discovery
3. School and laboratory search
4. Person resolution
5. Paper-author expansion
6. Alumni and former-member tracing
7. Contact evidence
8. Background evidence
9. Identity resolution
10. Coverage and stop conditions
11. Final acceptance

## 1. Variable boundary

Only these project inputs vary by run:

- `target_region`: country or region whose universities are in scope.
- `school_scope`: user-supplied schools or criteria; may be empty.
- `output_path`.
- `as_of_date`.

Do not weaken or silently alter the people scope, research topics, evidence rules, expansion loops, deduplication, workbook fields, or acceptance checks when the region changes.

## 2. School discovery

Do not force a fixed school count or create empty/low-value sheets. Build the school queue from:

1. Universities in `target_region` appearing in the latest available QS World University Rankings top 500 at execution time.
2. Members of the region's authoritative national university association or equivalent.
3. Locally prominent technical and comprehensive universities.
4. Lower-ranked schools with valuable AI, computer vision, robotics, embodied intelligence, world-model, or AI-infrastructure labs.
5. Universities closely linked to major national research organisations, publicly funded centres, or discipline-specific research hubs.
6. New in-region universities or high-value labs discovered through people, projects, or paper-author expansion.

Record the ranking edition/date, membership source, inclusion reason, official university URL, and source URLs. Rankings are selection evidence, not talent scores.

## 3. School and laboratory search

For every queued school, search its official site and public web sources for:

- Computer Science / Computing
- Artificial Intelligence / Machine Learning
- Engineering
- Robotics / Mechatronics
- Data Science
- Electrical and Electronic Engineering
- Autonomous Systems
- Research Centre / Institute / Laboratory
- Staff / People / Researchers
- PhD Students / HDR Students
- Postdocs
- Alumni / Former Members

Inspect each relevant lab's Team, People, Faculty, Researchers, Postdocs, PhD Students, Alumni, Former Members, Publications, Projects, Contact, and Join Us pages. Treat all relevant listed people, including departed members, as leads.

Use search-engine queries as complements, not substitutes, for site navigation. Useful patterns include:

- `site:<school-domain> ("artificial intelligence" OR robotics OR "machine learning") (people OR staff OR students)`
- `site:<school-domain> (alumni OR "former members" OR postdoc) (AI OR vision OR robotics)`
- `site:<school-domain> filetype:pdf (CV OR thesis OR paper) "<person name>"`
- `"<lab name>" (people OR alumni OR publications)`

Record directories and member pages that were checked, even when they yield no relevant people.

## 4. Person resolution

Include relevant:

- professors, associate professors, lecturers, and other faculty;
- lab PIs, researchers, research fellows, and research scientists;
- postdocs;
- PhD candidates and doctoral students;
- research engineers;
- master's students with important papers or projects;
- graduated PhDs;
- departed postdocs;
- lab alumni and former members;
- former school/lab staff now at other universities or companies.

For every lead, search:

1. current school official profile;
2. personal homepage;
3. public CV;
4. lab profile;
5. Google Scholar;
6. GitHub;
7. ORCID, DBLP, and Semantic Scholar;
8. paper PDF or proceedings page;
9. project page;
10. current institution page.

Capture research area, representative work/project, status, lab/department, current destination, public email or explicit missing-email marker, profiles, source URLs, and verification date. Keep a high-value lead without email if a trackable profile or paper source exists.

Core research topics include AI, machine learning, deep learning, reinforcement learning, computer vision, NLP, LLMs, VLMs, multimodal and generative AI, agents, post-training, inference and reasoning, AI infrastructure, MLSys, training/inference systems, distributed computing, world models, VLA, embodied intelligence, robotics, robot learning, autonomous systems, autonomous driving, 3D/4D vision, AI safety, and AI4Science.

## 5. Paper-author expansion

Inspect recent top-conference/top-journal work and important lab papers, including where relevant:

- NeurIPS, ICML, ICLR;
- CVPR, ICCV, ECCV, SIGGRAPH;
- ACL, EMNLP, NAACL;
- CoRL, RSS, ICRA, IROS;
- MLSys, OSDI, SOSP, NSDI;
- TPAMI, IJCV, JMLR and comparable venues.

For potentially relevant co-authors, resolve school/unit, lab, advisor/PI, current destination, email, homepage, Scholar, GitHub, and representative work. Add newly discovered in-region schools or high-value labs to the queue.

An expansion round is one documented pass over newly added people, papers, collaborators, labs, and destinations. Record leads found, accepted, rejected, and rejection reasons. Stop only after two consecutive rounds add zero new relevant people for that school.

## 6. Alumni and former-member tracing

Do not stop at an old lab page. Follow:

`original school/lab → personal site or CV → current institution → current email → current papers → new collaborators/labs`

Retain the original school's sheet association. Mark the historical status accurately, such as `已毕业`, `Alumni`, or `Former Postdoc`, and record departure/graduation year when supported. Prefer the current public email; if only an old email remains, mark it `待复查` or `较可信` according to its source and explain possible staleness.

## 7. Contact evidence

Allowed confidence labels:

- `已核验`: current school official page, personal homepage, personal CV, or current institution official page.
- `较可信`: paper PDF, old lab page, formal conference material, or older school page.
- `待复查`: likely stale, status changed without a newer email, ambiguous page ownership, or another unresolved issue.

Rules:

- Store exact email source URL(s) separately from general references.
- Never infer an address from a naming convention or another person's address.
- If no public email is found, enter `未找到公开Email`.
- Preserve homepage, Scholar, GitHub, paper, and project references for email-missing people.
- Other public professional contact methods may be recorded; do not collect private/personal contact data unrelated to professional work.

## 8. Background evidence

Use exactly one label:

- `公开证据明确`: an autobiographical, official, or authoritative source explicitly states the relevant Chinese or ethnic-Chinese background.
- `大陆经历明确`: verified education, long-term research, or employment experience in mainland China.
- `港澳台经历明确`: verified education, research, or employment experience in Hong Kong, Macau, or Taiwan.
- `姓名线索待核验`: a Chinese-style, pinyin, or Cantonese-style name is only a search lead and no sufficient public background evidence was found.
- `背景未确认`: no verifiable relevant evidence was found.

Do not assert nationality or ethnicity from a name, photo, or appearance. A mainland/Hong Kong/Macau/Taiwan experience label describes public experience evidence, not nationality or ethnicity. Record the supporting URL and a short factual note for the first three labels. For `姓名线索待核验`, state that the name is only an unresolved search clue.

## 9. Identity resolution

Create one stable canonical `person_id` per real person. Resolve duplicates using, in order:

1. identical email;
2. identical personal homepage, ORCID, Scholar, or GitHub identity;
3. matching name plus school, advisor, and paper combination;
4. manual review of conflicting evidence.

Treat same-name people with different emails, profiles, or histories as separate people. A shared lab page does not prove identity. Keep all school associations under the canonical record, render the person in each relevant school sheet, and count the canonical record once globally.

Do not auto-merge ambiguous records. Mark them for review with the compared IDs and evidence.

## 10. Coverage and stop conditions

A school may be marked `完成` only when all are true:

- relevant department/personnel directories were checked;
- discovered AI/robotics lab member pages were checked;
- faculty, doctoral, postdoc, alumni, and former-member pages were checked or explicitly recorded as unavailable;
- one high-value paper-author expansion cycle was completed;
- two consecutive expansion rounds produced no new relevant people;
- inaccessible or unconfirmable pages were recorded with URLs and reasons.

Use `进行中` before the gates pass and `受阻` when material pages cannot be accessed or verified. Do not fabricate completion flags.

## 11. Final acceptance

Before delivery, confirm:

- every non-missing email has a public email-source URL;
- no address was guessed;
- departed people were retained and traced;
- every person has at least one of research information, a public contact, or a trackable profile;
- references support manual review;
- cross-school identity deduplication is complete or ambiguity is queued;
- school sheets use identical headers;
- every sheet has filters, frozen headers, and wrapped text;
- no formulas or formula errors exist;
- every sheet was reopened, structurally checked, rendered, and visually inspected;
- the workbook is saved to the requested final path.
