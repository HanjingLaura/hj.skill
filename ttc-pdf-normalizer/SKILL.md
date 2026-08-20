---
name: ttc-pdf-normalizer
description: "Normalize one candidate or resume file into a validated 姓名-TTC-MMDDNN.pdf, conservatively remove detected Boss top-right numeric watermarks, verify the candidate name from the visible resume identity block, and preserve the source. Use for TTC resume conversion, renaming, watermark cleanup, or standardized delivery."
---

# TTC PDF Normalizer

Turn one candidate file into a visually faithful PDF named `<candidate-name>-TTC-MMDDNN.pdf`. Preserve the original file and do not rewrite the candidate's content.

## Workflow

1. Resolve the input file.
   - Use the attachment or path the user supplied.
   - Process one file per invocation unless the user explicitly requests a batch.
   - Never modify, move, or delete the source.
2. Determine the candidate name using the visible resume identity block, not the filename.
   - Render the first page and inspect the header/identity area glyph by glyph. Text extraction or OCR is supporting evidence only; if it is garbled or disagrees with the rendered page, the rendered identity block wins.
   - Require a visible identity-block name plus one corroborating signal when available, such as the same name in the filename, document metadata, contact block, or experience text. A filename alone is never sufficient.
   - For Chinese names, copy the exact 2–4 Chinese characters shown in the identity block. Do not complete, transliterate, or autocorrect a partially recognized name.
   - Do not mistake a recruiter, employer, school, email handle, job title, section title, or document label for the candidate.
   - A user's explicit correction overrides the document only when the user states that the resume name itself is wrong.
   - If the visible identity block is unclear, conflicting, or absent, ask the user before creating the final file.
3. Convert the source to PDF with the format-specific route below.
4. Run `scripts/finalize_ttc_pdf.py` on the converted PDF. It automatically checks for a high-confidence Boss numeric watermark in the top-right margin and visually covers it only when detected.
5. Render every required final page and inspect the name, layout, and top-right corner. If no watermark exists, the page must remain unchanged. If an image-only watermark remains, remove it manually only when visual inspection confirms it sits entirely in blank margin space; otherwise report it instead of covering resume content.
6. Return the final PDF as a clickable download and state that the original was preserved.

## Format Routing

- PDF: use the source directly as the conversion input; do not reflow or rasterize it.
- DOC, DOCX, ODT, or RTF: export through the document runtime, Microsoft Word, or LibreOffice. Prefer a native PDF export that preserves fonts, links, pagination, and images.
- JPG, JPEG, PNG, TIFF, BMP, or WEBP: convert without cropping or stretching. Preserve multi-page TIFFs and the user's stated order for multiple images.
- XLS, XLSX, ODS, or CSV: export through the spreadsheet runtime. Check print areas, page orientation, scaling, repeated headers, and hidden sheets before accepting the PDF.
- PPT, PPTX, or ODP: export through the presentation runtime. Preserve slide size, fonts, and one slide per PDF page unless the user requests handouts.
- TXT, Markdown, or HTML: create a readable document first, preserving text exactly, then export it to PDF with Unicode-capable fonts.
- Other formats: inspect the actual file type and use an available native application or safe converter. If faithful conversion is unavailable, explain the missing converter instead of changing the extension or inventing content.

Use OCR only to identify the candidate or verify text. Do not replace the visible source pages with OCR-generated text unless the user explicitly requests OCR reconstruction.

## Boss Watermark Rule

- Automatic removal is intentionally conservative: only a small, light-colored 8–20 digit mark in the top-right margin is covered.
- Do not remove phone numbers, dates, IDs in the resume body, logos, decorative content, or any uncertain mark.
- The finalizer reports `boss_watermark_cleanup`, `boss_watermarks_removed`, `boss_watermark_pages`, and warnings. Treat `not_detected` as “no supported text watermark detected,” not proof that an image-only watermark is absent.
- Use `--keep-boss-watermark` only when the user asks to preserve it or the mark is legitimate resume content.
- Always verify the rendered result; automatic cleanup is not a substitute for visual QA.

## Filename Rules

### Required daily filename

Name every delivered resume as `<candidate-name>-TTC-MMDDNN.pdf`, using ASCII hyphens and uppercase `TTC`. `MMDD` is the current task date. `NN` is the two-digit, output-directory-wide daily candidate sequence, starting at `01` and resetting each day.

Pass the current `MMDD` explicitly with `--date-mmdd`. The finalizer scans the output directory and allocates `NN`. It reuses the same candidate's same-content file on the same date. A same-name candidate with different content receives the next number and must not overwrite an existing output. If the user explicitly supplies the daily number, pass `--daily-sequence <NN>`.

- Produce exactly `<candidate-name>-TTC-MMDDNN.pdf`.
- Preserve the candidate's natural script and capitalization, including Chinese characters and diacritics.
- Collapse repeated whitespace and remove filesystem-invalid characters only.
- Strip an existing trailing TTC/date suffix before adding the new suffix so `TTC` appears once.
- Do not add words such as `resume`, `CV`, `简历`, dates, roles, or version numbers.
- If the exact destination exists with different content, do not overwrite it unless the user explicitly authorizes replacement.

## Finalization

Place temporary conversions under `tmp/ttc-pdf-normalizer/`. Place a final downloadable artifact under `output/pdf/` when working in a repository, or another user-requested output directory.

Run:

```bash
python scripts/finalize_ttc_pdf.py <converted.pdf> --name "<candidate-name>" --output-dir <output-directory> --date-mmdd <MMDD>
```

If the shell corrupts a non-ASCII name, UTF-8 encode the verified name and pass its hexadecimal bytes instead:

```bash
python scripts/finalize_ttc_pdf.py <converted.pdf> --name-utf8-hex <hex-bytes> --output-dir <output-directory> --date-mmdd <MMDD>
```

Add `--overwrite` only when replacement is explicitly authorized. The script sanitizes the verified name, performs conservative Boss watermark cleanup by default, verifies the PDF structure, copies atomically, and reports the final path, hash, page count, daily sequence, and cleanup result.

## Quality Checks

- Confirm the final filename matches the convention exactly.
- Confirm the file opens as a PDF and has at least one nonblank page.
- Render every page for files up to 10 pages. For longer files, inspect the first page, last page, and representative middle pages.
- Check for clipped or missing text, substituted glyphs, blank pages, cropped images, incorrect orientation, broken tables, and changed pagination.
- Compare the PDF with the source in the native format when conversion occurred.
- Verify the final first-page name exactly matches the visible source identity block.
- Inspect the top-right corner of every rendered page; confirm a detected Boss number is gone and legitimate header content remains intact.
- Treat password-protected, corrupted, unsupported, or ambiguous files as blockers; do not deliver an unverified output.

## Delivery

Return a clickable link to the final `<candidate-name>-TTC-MMDDNN.pdf`. Keep the response concise and mention any conversion or watermark-cleanup limitation that could affect fidelity. Never include the candidate file or extracted personal data in the public Skill repository.
