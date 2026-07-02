# Library Guide: docx / xlsx / pptx / pdf

Per-format guidance: what to use, what breaks, and minimal working patterns. All Python unless noted. Install what you need; none are stdlib.

## .docx — python-docx

**Use for:** creating documents, filling templates, targeted edits (replace text, add sections, tables).

```python
from docx import Document
doc = Document("template.docx")          # omit arg for a blank doc
doc.add_paragraph("Findings", style="Heading 1")
doc.add_paragraph("Body content.", style="Body Text")
doc.save("out.docx")                     # never save over the template
```

**Gotchas:**

- A paragraph's text is split across multiple `run` objects, often mid-word (spell-check history causes this). Naive per-run find-and-replace misses matches that span runs — join runs first or use a run-merging helper.
- Style names must already exist in the document — `style="Heading 1"` raises `KeyError` in a blank doc created without those styles. Templates solve this; that's another reason to use them.
- python-docx does not model everything (comments, some content controls, tracked changes). Unmodeled features usually *survive* a load/save, but verify (§4 of the skill). For what it can't reach, a .docx is a zip of XML — `document.xml` can be edited directly, carefully.
- Headers/footers are per-section: `doc.sections[0].header`.

## .xlsx — openpyxl (and pandas for analysis)

**Use for:** creating/editing workbooks (openpyxl); reading tabular data for analysis (pandas `read_excel`).

```python
from openpyxl import load_workbook
wb = load_workbook("book.xlsx")               # keep_vba=True for .xlsm or macros are destroyed
ws = wb["Sheet1"]
ws["B2"] = 1234.5                             # real number, not "1,234.50"
ws["B2"].number_format = "#,##0.00"
ws["C2"] = "=B2*1.2"                          # written as formula text
wb.save("out.xlsx")
```

**Gotchas:**

- **openpyxl never evaluates formulas.** `ws["C2"].value` after writing returns the formula string. Reading a workbook, `load_workbook(..., data_only=True)` returns the *cached* values from the last time Excel/LibreOffice saved it — `None` if it was never opened by a real app. To get computed values: convert via `libreoffice --headless` and re-read, or compute in Python.
- Write typed values: `datetime` objects for dates (plus a date `number_format`), floats for numbers. Strings that look like numbers poison every downstream sort/sum.
- `ws.max_row`/`max_column` count formatted-but-empty cells; don't trust them for data extent.
- Column width `#####` display: set `ws.column_dimensions["B"].width` after writing wide values.
- Merged cells: only the top-left cell holds the value; writing into another cell of a merged range raises or silently misplaces.

## .pptx — python-pptx

**Use for:** creating decks from a template's layouts, editing existing decks, extracting text.

```python
from pptx import Presentation
prs = Presentation("template.pptx")
layout = prs.slide_layouts[1]                  # inspect the template to map indices → layouts
slide = prs.slides.add_slide(layout)
slide.placeholders[0].text = "Quarterly Findings"   # title placeholder
slide.placeholders[1].text = "• Point one"
prs.save("out.pptx")
```

**Gotchas:**

- Layout indices are template-specific — print `[l.name for l in prs.slide_layouts]` first; guessing indices puts titles in body boxes.
- Use placeholders, not `add_textbox`, wherever possible: placeholders inherit the template's position/typography; free boxes must be positioned manually in EMUs and drift per-slide.
- python-pptx **cannot delete slides** via public API (only workarounds through the XML). Plan slide count up front, or start from a copy of the deck with slides to keep.
- Text overflow is invisible in code: a placeholder holds any amount of text; the render just clips it. This is the #1 reason the render-and-inspect loop is mandatory for decks.
- Charts: `chart.replace_data()` on an existing template chart is far more reliable than building charts from scratch.

## .pdf

**Producing** (in order of preference):

1. **HTML/CSS → headless browser print** (Chromium `--headless --print-to-pdf`, or Playwright `page.pdf()`): full layout control, fast iteration, CSS `@page` for margins/headers. Best default for reports and designed documents.
2. **docx/md → LibreOffice/pandoc convert:** best when the source document already exists or must also ship as docx. `libreoffice --headless --convert-to pdf in.docx`.
3. **reportlab:** programmatic canvas drawing; verbose, but precise for label/ticket/form-like output.

**Editing:**

- **pypdf** for page-level operations: merge, split, rotate, extract pages, fill AcroForm fields, stamp/watermark (overlay one PDF on another).
- Content edits (changing text/layout): **regenerate from source.** Tools that rewrite PDF text in place break kerning, fonts, and reflow; treat them as a last resort for one-word fixes only.

**Extracting:**

- **pdfplumber** for text + tables with positions; `pdftotext -layout` (poppler) for fast bulk text.
- Extraction quality varies wildly with the PDF's internals: text may be out of reading order, hyphen-split, or absent entirely (scanned image PDFs need OCR, e.g. tesseract/ocrmypdf). Always spot-check extracted text against the rendered page.

## Rendering & inspection toolbox (used by every format)

```sh
libreoffice --headless --convert-to pdf file.docx   # docx/xlsx/pptx → pdf
pdftoppm -png -r 100 out.pdf page                    # pdf → page-1.png, page-2.png…
```

Then view the images. LibreOffice's rendering differs slightly from Word/PowerPoint (fonts, exact pagination) — good enough to catch structural defects (overflow, broken tables, missing content), not pixel-exact fidelity. Note that in your report if exact-fidelity matters.
