# Dataset contract

## Contents

1. Canonical JSON shape
2. Fixed vocabularies
3. Field rules
4. Workbook mapping

## 1. Canonical JSON shape

Maintain one UTF-8 JSON file:

```json
{
  "project": {
    "target_region": "澳大利亚",
    "as_of_date": "2026-07-29",
    "ranking_snapshot": "QS 2027",
    "ranking_reference": "https://...",
    "notes": ""
  },
  "schools": [
    {
      "name": "Example University",
      "sheet_name": "Example University",
      "official_url": "https://...",
      "inclusion_basis": "最新QS前500；国家大学协会成员；高价值机器人实验室",
      "selection_references": ["https://..."],
      "coverage_status": "进行中",
      "units_checked": ["School of Computing"],
      "labs_checked": ["Example AI Lab"],
      "faculty_checked": true,
      "doctoral_checked": true,
      "postdoc_checked": true,
      "alumni_checked": true,
      "paper_expansion_completed": true,
      "expansion_round_new_counts": [4, 0, 0],
      "blocked_pages": [
        {"url": "https://...", "reason": "页面无法访问"}
      ],
      "coverage_notes": ""
    }
  ],
  "people": [
    {
      "person_id": "P000001",
      "name": "Example Person",
      "status": "博士生",
      "school_affiliations": [
        {
          "school": "Example University",
          "unit_lab": "School of Computing / Example AI Lab",
          "association_note": "导师：Example PI"
        }
      ],
      "current_destination": "Example University",
      "background_status": "背景未确认",
      "background_evidence": "",
      "research_areas": ["Robot Learning", "Computer Vision"],
      "representative_works": ["Example Paper, CVPR 2026"],
      "email": "person@example.edu",
      "email_confidence": "已核验",
      "email_sources": ["https://example.edu/profile"],
      "other_contacts": "",
      "profiles": [
        {"type": "个人主页", "url": "https://..."},
        {"type": "Google Scholar", "url": "https://..."},
        {"type": "GitHub", "url": "https://..."}
      ],
      "references": [
        {"type": "学校页", "url": "https://...", "note": "身份、学院、Email"},
        {"type": "论文", "url": "https://...", "note": "研究方向与代表作"}
      ],
      "notes": "",
      "verified_date": "2026-07-29",
      "review_reasons": [],
      "identity_match_basis": "个人主页与Email一致",
      "related_person_ids": []
    }
  ]
}
```

Arrays may be empty only when the corresponding evidence was not found or the check is incomplete. Do not omit required keys merely because a value is unknown; use an empty string/list or `false`.

## 2. Fixed vocabularies

`coverage_status`:

- `完成`
- `进行中`
- `受阻`

`background_status`:

- `公开证据明确`
- `大陆经历明确`
- `港澳台经历明确`
- `姓名线索待核验`
- `背景未确认`

`email_confidence`:

- `已核验`
- `较可信`
- `待复查`

The `status` field is descriptive rather than closed, but prefer concise values such as `教师`, `教授`, `副教授`, `讲师`, `研究员`, `Research Fellow`, `博士后`, `博士生`, `研究工程师`, `已毕业`, `Alumni`, and `Former Postdoc`.

## 3. Field rules

- `person_id`, `name`, `status`, `school_affiliations`, `background_status`, `email`, `email_confidence`, and `verified_date` are required.
- `email` must be an exact public email or `未找到公开Email`.
- Every actual email requires at least one `email_sources` URL.
- `未找到公开Email` must use `待复查` unless the user explicitly adopts a different review convention.
- `公开证据明确`, `大陆经历明确`, and `港澳台经历明确` require a factual `background_evidence` note and at least one supporting reference.
- Every school in `school_affiliations` must appear in `schools`.
- Every person must have at least one of: non-empty research areas, an actual public email, or at least one public profile URL.
- `person_id` is globally unique. Cross-school affiliations stay on one person record.
- `review_reasons` contains concrete unresolved items such as `Email可能过期`, `身份重名待核验`, `姓名线索待核验`, or `当前去向未确认`.
- A school marked `完成` must satisfy every completion gate and end with two zero-new-person expansion rounds.

## 4. Workbook mapping

Every school sheet uses exactly these 14 headers in order:

1. 姓名
2. 人员状态
3. 学院 / 实验室
4. 当前或最新去向
5. 相关背景
6. 研究方向
7. 代表著作 / 项目
8. Email
9. 其他联系方式
10. 联系方式可信度
11. 个人主页 / Scholar / GitHub
12. Reference
13. 备注
14. 核验日期

The same canonical person is rendered once in each associated school sheet. Merge multiple same-school affiliations into the `学院 / 实验室` cell. `Reference` combines email sources, background evidence sources, school/lab pages, profiles, CVs, papers, and project pages without removing source labels.

`跨校去重` is the canonical identity view and includes the global ID, all associated schools, identity evidence, email, profiles, and match basis. `待复查` includes every record with missing/stale contact information, unresolved background clues, ambiguous identity, missing destination, or explicit review reasons.
