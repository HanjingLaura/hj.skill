# Decision Policy

Use this policy when classifying resume files.

## Delete

Mark a file `delete` when any of these are true:

- Any education segment clearly says junior college, associate degree, higher vocational college, adult junior college, or equivalent.
- The resume clearly says the candidate completed or entered a college-to-bachelor upgrade path.
- Local screening rules clearly mark the school background as disqualifying.
- Local screening rules clearly mark the company background as disqualifying.
- Local screening rules provide another explicit delete condition that the file satisfies.

## Check

Move a file to `check` when any of these are true:

- Text extraction is missing, incomplete, or garbled.
- Education is unclear and might include a junior-college segment.
- A school/company judgment is plausible but not explicit under local rules.
- There are conflicting signals, such as strong company experience but weak school evidence.
- The file format is unsupported.
- The candidate looks potentially useful but one rule is uncertain.

## Keep

Keep a file only when:

- No junior-college or upgrade signal is found.
- Local rules do not identify a clear school/company disqualifier.
- There is no unresolved ambiguity that requires human review.

## Reporting

For every file, record:

- relative path
- decision: `delete`, `check`, or `keep`
- reason
- evidence snippet when available
- action taken
- extraction status

Prefer a conservative `check` decision over an unsupported delete.
