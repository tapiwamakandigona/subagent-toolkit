---
name: document-handling
description: Procedures for producing and editing office and PDF artifacts — docx, xlsx, pptx, and PDF files. Covers choosing the right library for each format and operation, template-based generation over from-scratch construction, using named styles instead of inline formatting, a mandatory render-and-inspect verification loop, and the common gotchas of each format. Use when a deliverable is a Word document, Excel workbook, PowerPoint deck, or PDF — whether creating, editing, or filling one.
license: MIT
metadata:
  version: "1.1.0"
---

# Document Handling

Office documents are the deliverables people actually open — and the ones agents most often ship broken, because the source code of a document and its rendered appearance can differ wildly. The core rule: **never ship a document you haven't rendered and looked at.**

## 1. Choose the right tool for the operation

The library that creates a format well is often wrong for *editing* it. Decision table (full guidance, gotchas, and code snippets in [references/library-guide.md](references/library-guide.md)):

| Format | Create from scratch | Edit existing | Extract content |
|---|---|---|---|
| .docx | python-docx | python-docx (or direct XML for what it can't reach) | python-docx / pandoc / markitdown |
| .xlsx | openpyxl | openpyxl (`keep_vba=True` for .xlsm) | openpyxl (values) / pandas (analysis) |
| .pptx | python-pptx | python-pptx | python-pptx |
| .pdf | HTML/CSS → headless-browser print, or a doc format → convert | pypdf (pages/forms) — content edits: regenerate instead | pdfplumber / pdftotext |

Two rules that prevent most disasters:

- **PDF is an output format, not an editing format.** To "edit" PDF content, edit the source (or an HTML/docx intermediate) and re-export. In-place PDF text editing is a last resort that breaks layout.
- **Round-tripping is lossy.** Converting docx→markdown→docx destroys styles, headers/footers, and embedded objects. Edit in the native format when the original formatting must survive.

## 2. Templates over from-scratch construction

When output must look professional or match an existing house style:

- **Start from a template file** — a real .docx/.pptx/.xlsx with the styles, masters, headers/footers, and branding already right — and fill in content programmatically. Getting typography and layout right *in code, from nothing* takes 10× longer and looks worse.
- The template workflow: open the template → find placeholder content (by style, by placeholder text like `{{title}}`, or by slide-layout position) → replace with real content → save as a new file. **Never overwrite the template.**
- For pptx specifically: use the template's **slide layouts** (`slide_layouts[n]`) and their placeholder shapes rather than free-positioning text boxes; free-floating boxes are how decks end up misaligned on every slide.
- No template available? Build one first (or generate via a format that handles layout for you — HTML/CSS → PDF gives you full layout control with tools you can iterate fast in).

## 3. Styles, not inline formatting

- Apply **named styles** (`Heading 1`, `Body Text`, a defined cell style, layout placeholders) instead of setting font/size/bold on every run, cell, or box. Inline formatting produces documents that are inconsistent now and unmaintainable later — one change means touching every element.
- Define or modify the style once, apply it everywhere. If a document needs a look no existing style has, add a style, don't scatter overrides.
- This is also how TOCs, navigation panes, and accessibility work: a "heading" that is merely bold 16pt text is invisible to all three.
- Numbers stay numbers: in xlsx, write real numbers/dates with a **number format** (`#,##0.00`, `yyyy-mm-dd`), never pre-formatted strings — strings break sorting, formulas, and downstream analysis.

## 4. Render and inspect — mandatory, not optional

Document source that "looks right" routinely renders wrong: overflowing text boxes, tables sliced across pages, fonts silently substituted, formulas showing `#REF!`. The loop:

1. **Render to final form**: export/convert to PDF (`libreoffice --headless --convert-to pdf file.docx`) or screenshot the opened file. For xlsx, also re-open and read back computed values — openpyxl does not evaluate formulas.
2. **Convert pages to images and actually look at them** (e.g. `pdftoppm -png`): every page, at readable size.
3. Check the worst cases, where defects hide: the longest text value, the widest table row, page/slide 2+ (pagination breaks), the last page (orphaned content).
4. Specific checks: clipped/overflowing text • tables split badly across pages • wrong/substituted fonts • broken images • empty sections/placeholders left in (`{{title}}` shipping to a customer is the classic) • header/footer/page numbers correct • xlsx: formula errors, column widths hiding data (`#####`).
5. Fix in source, re-render, re-inspect. Repeat until clean. **Budget for 2–3 loops** — first renders are rarely right.

If you cannot render (no converter available), say so explicitly in your report — an uninspected document is an unverified deliverable.

## 5. Cross-format gotchas (top of the list)

- **Fonts:** a font not installed on the rendering machine gets silently substituted, changing line breaks and overflow. Stick to universally available faces or embed fonts.
- **The placeholder leak:** grep your output for `{{`, `TODO`, `Lorem`, and template boilerplate before shipping. Every time.
- **Encoding/locale in xlsx:** CSV imports with the wrong delimiter or encoding corrupt silently; dates interpreted in the wrong locale (`03/04` — March or April?) corrupt *plausibly*, which is worse.
- **Editing preserves what you don't touch** — usually. Verify the untouched parts survived (page count, images, headers) after any programmatic edit; some libraries drop features they don't model when saving.
- **File size sanity:** a 40MB deck usually means uncompressed images — resize/compress before embedding, not after.

## Pre-submit checklist

- [ ] Right library for the operation (create vs edit vs extract); no lossy round-trips
- [ ] Built from a template with named styles; no ad-hoc inline formatting
- [ ] Rendered to final form and every page visually inspected (worst-case content included)
- [ ] No placeholders, TODOs, or template boilerplate left in the output
- [ ] xlsx: real typed values + number formats; formulas evaluated and checked
- [ ] Untouched parts of edited documents verified intact
