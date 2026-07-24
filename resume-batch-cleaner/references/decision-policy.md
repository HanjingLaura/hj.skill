# Decision Policy

Apply hard screening before score-based ranking.

## Exclude

Exclude a resume when any of these are true:

- The actual role is legal, marketing, sales, BD, investment, operations, product, pure design, pure project management, or another non-technical function.
- Any education segment clearly says junior college, higher vocational college, associate degree, adult junior college, or equivalent.
- Any education segment is a college-to-bachelor upgrade path, including 专升本、专接本、专插本、高起本 and equivalent wording.
- Any bachelor's segment is from a private Chinese undergraduate institution or historical independent college under the task's strict rule.
- The supplied resume does not contain enough education information to verify the hard education rules under conservative mode.

Do not let a later bachelor, master, or doctorate override an earlier disqualifying education segment.

## Keep

Keep only when all of these are true:

- The role has clear hands-on technical evidence from the resume body.
- No hard education exclusion is found across the complete visible education chain.
- Extraction or visual review is sufficient to identify the candidate and evaluate the role.
- The file is not a duplicate of a more complete usable copy.

## Review

Route to manual review when any of these are true:

- Text extraction is missing, incomplete, garbled, or layout-dependent.
- The resume is image-only, scanned, or a legacy document whose visible content differs from extracted text.
- The filename/folder indicates a technical role but the body suggests a different function.
- A school has changed ownership, name, or status, or may be a historical independent college.
- The resume-internal name or expected location is uncertain.
- A contact-based possible duplicate needs confirmation.

Before final packaging, resolve every review item to keep, exclude, or duplicate. Do not leave unresolved reviews in the final output.

## Duplicate

- Detect exact duplicates by SHA-256.
- Detect semantic duplicates by strong contact identifiers such as email and phone.
- Prefer the most complete, readable, and currently relevant copy.
- Keep one copy only and record the retained source in the audit data.

## Reporting

For every file record:

- source batch and source path;
- extraction status;
- resume-internal name and confidence;
- role decision and reason;
- education decision, institutions, and evidence;
- expected location and evidence;
- duplicate source when applicable;
- all score components and total;
- final output filename when retained.

Never modify or delete source files in the standard ranking workflow.
