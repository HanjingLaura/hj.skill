---
name: ttc-pdf-normalizer
description: "Normalize one candidate or resume file into a validated PDF named 姓名-TTC.pdf while preserving the source. Use when the user attaches or points to a PDF, Word document, image, spreadsheet, presentation, text file, or other candidate document and asks to convert it to PDF, apply the TTC filename convention, rename a resume for TTC, or return a standardized downloadable file."
---

# TTC PDF Normalizer

Turn one candidate file into a visually faithful PDF named exactly `<candidate-name>-TTC.pdf`. Preserve the original file and do not rewrite the candidate's content.

## Workflow

1. Resolve the input file.
   - Use the attachment or path the user supplied.
   - Process one file per invocation unless the user explicitly requests a batch.
   - Never modify, move, or delete the source.
2. Determine the candidate name.
   - Prefer a name explicitly supplied by the user.
   - Otherwise inspect the document header, first page, metadata, and source filename.
   - Accept a name only when it is supported by the document's identity block or equally strong evidence.
   - Do not mistake a recruiter, employer, school, email handle, job title, or document label for the candidate.
   - If no name is reliable or multiple names remain plausible, ask the user for the name before creating the final file.
3. Convert the source to PDF with the format-specific route below.
4. Run `scripts/finalize_ttc_pdf.py` on the converted PDF.
5. Render and inspect the final PDF.
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

## Filename Rules

- Produce exactly `<candidate-name>-TTC.pdf` with one ASCII hyphen before `TTC` and uppercase `TTC`.
- Preserve the candidate's natural script and capitalization, including Chinese characters and diacritics.
- Collapse repeated whitespace and remove filesystem-invalid characters only.
- Strip an existing trailing `-TTC` before adding the suffix so the suffix appears once.
- Do not add words such as `resume`, `CV`, `简历`, dates, roles, or version numbers.
- If the exact destination exists with different content, do not overwrite it unless the user explicitly authorizes replacement.

## Finalization

Place temporary conversions under `tmp/ttc-pdf-normalizer/`. Place a final downloadable artifact under `output/pdf/` when working in a repository, or another user-requested output directory.

Run:

```bash
python scripts/finalize_ttc_pdf.py <converted.pdf> --name "<candidate-name>" --output-dir <output-directory>
```

If the shell corrupts a non-ASCII name, UTF-8 encode the verified name and pass its hexadecimal bytes instead:

```bash
python scripts/finalize_ttc_pdf.py <converted.pdf> --name-utf8-hex <hex-bytes> --output-dir <output-directory>
```

Add `--overwrite` only when replacement is explicitly authorized. The script sanitizes the name, verifies the PDF structure, copies atomically, and reports the final path, size, hash, and page count when `pypdf` is available.

## Quality Checks

- Confirm the final filename matches the convention exactly.
- Confirm the file opens as a PDF and has at least one nonblank page.
- Render every page for files up to 10 pages. For longer files, inspect the first page, last page, and representative middle pages.
- Check for clipped or missing text, substituted glyphs, blank pages, cropped images, incorrect orientation, broken tables, and changed pagination.
- Compare the PDF with the source in the native format when conversion occurred.
- Treat password-protected, corrupted, unsupported, or ambiguous files as blockers; do not deliver an unverified output.

## Delivery

Return a clickable link to the final `<candidate-name>-TTC.pdf`. Keep the response concise and mention any conversion limitation that could affect fidelity. Never include the candidate file or extracted personal data in the public Skill repository.
