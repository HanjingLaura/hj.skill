# Screening Rules Template

Copy this file to `.hj-skill-local/resume-batch-cleaner/screening-rules.local.md` and fill it with your private screening standards. Do not commit filled local rules.

## Education Hard Delete Rules

These are global defaults. Keep them strict unless the user explicitly changes the workflow.

- Delete if any education segment is junior college / associate degree.
- Delete if the resume shows college-to-bachelor upgrade.
- Delete even if a later degree is bachelor's, master's, or PhD.
- Move to `check` if education extraction is unclear and the file may contain a junior-college segment.

## School Background Rules

Delete when the school evidence clearly matches these disqualifying patterns:

- 

Keep when the school evidence clearly matches these acceptable patterns:

- 

Move to `check` when:

- The school name is unclear.
- The candidate has mixed school backgrounds and the rule is not explicit.
- The file text extraction is incomplete.

## Company Background Rules

Delete when company evidence clearly matches these disqualifying patterns:

- 

Keep when company evidence clearly matches these acceptable patterns:

- 

Move to `check` when:

- Company names are unclear.
- Work experience is too vague to classify.
- The candidate has a mix of strong and weak company evidence.

## Custom Keywords

Additional delete keywords:

- 

Additional check keywords:

- 

## Notes

- Keep private client-specific standards here, not in the public skill.
- Make rules concrete enough that another Codex instance can apply them consistently.
