# Aesthetic Directions Catalog

Eight committed design directions with concrete implementation choices. Pick **one**, follow it fully. Font names are archetypes — substitute any face with the same character.

---

## 1. Brutalist Editorial
Print-magazine energy: stark, typographic, confident.
- **Type:** massive serif or slab display (e.g. a high-contrast editorial serif) at 64–120px; body in a neutral grotesque.
- **Color:** near-black on off-white (`#141414` / `#f4f1ea`), one hot accent (red-orange). No gradients, no shadows.
- **Layout:** hard grid with visible rules/borders (1–2px solid), asymmetric columns, sharp corners (0px).
- **Motion:** minimal — instant hovers, underline animations only.
- **Fits:** publications, portfolios, manifestos, agencies.

## 2. Dense Pro Tool
Trading-terminal / IDE aesthetic: information-dense, fast, serious.
- **Type:** monospace or compact grotesque throughout; sizes 12–14px body, small caps for labels.
- **Color:** dark UI (`#0d1117`-family), muted text, semantic accents only (green=good, red=bad, one brand accent).
- **Layout:** tight 4px spacing scale, tables and panels over cards, 2–4px radius, dividers not whitespace.
- **Motion:** none decorative; instant state changes.
- **Fits:** dashboards, admin tools, dev tools, analytics.

## 3. Warm Paper & Ink
Field-notebook / letterpress warmth: humane, trustworthy, quiet.
- **Type:** literary serif for body *and* display; italic for emphasis.
- **Color:** cream (`#faf6ef`), ink (`#2a2620`), muted terracotta or forest accent.
- **Layout:** generous whitespace, narrow reading measure (~65ch), subtle 1px borders, 4–6px radius.
- **Motion:** gentle fades (200ms), nothing bouncy.
- **Fits:** writing tools, journals, wellness, education, docs.

## 4. Swiss / International
Grid-worship: rational, timeless, extremely tidy.
- **Type:** one neutral grotesque family, 3 weights; tight tracking on headlines; flush-left everything.
- **Color:** white, black, one primary (classic: pure red or cobalt). Large fields of flat color.
- **Layout:** strict 12-column grid, mathematical 8px spacing, no radius or shadow — alignment does the work.
- **Motion:** restrained slide/fade, easing `ease-out`.
- **Fits:** B2B, agencies, architecture, systems products.

## 5. Neon Terminal / Cyber
CRT-glow, hacker-adjacent: energetic, technical, nocturnal.
- **Type:** monospace display; wide-tracked uppercase labels.
- **Color:** near-black background, phosphor accent (green/cyan/magenta) with restrained glow (`text-shadow`), scanline or grid texture at low opacity.
- **Layout:** bordered panels with corner accents, ASCII/typographic ornaments, 0–2px radius.
- **Motion:** typing effects, blinking cursor, quick flickers — used sparingly.
- **Fits:** dev tools, security, gaming, launch/teaser pages.

## 6. Soft Depth / Modern Product
Contemporary SaaS done properly (not the generic version).
- **Type:** characterful grotesque display (something with personality, not the default) + clean body face.
- **Color:** light neutral base with *one* saturated accent; large soft shadows only on primary surfaces; at most one subtle gradient, in the accent hue.
- **Layout:** 8px scale, 10–14px radius consistently, cards used for genuinely card-like things only.
- **Motion:** 150–200ms ease transitions, slight lift on hover.
- **Fits:** consumer SaaS, onboarding flows, marketing for friendly products.

## 7. Retro-Futurist / Vapor
70s-sci-fi-poster meets modern layout: bold, nostalgic, graphic.
- **Type:** chunky rounded or extended display face; wide uppercase headers.
- **Color:** sunset palette (deep purple base, orange/pink accents) or two-tone duotone imagery; noise/grain texture overlay.
- **Layout:** big geometric shapes, oversized numerals, horizon lines, pill buttons.
- **Motion:** slow parallax, drifting gradients.
- **Fits:** music, events, creative tools, consumer brands with attitude.

## 8. Monochrome Luxury
Fashion-house minimalism: austere, expensive, whisper-quiet.
- **Type:** ultra-light or high-contrast serif display, widely tracked uppercase nav; tiny body sizes with generous leading.
- **Color:** strictly black/white/gray; imagery carries all color.
- **Layout:** extreme whitespace (128px+ sections), center-axis symmetry, hairline rules, no radius.
- **Motion:** slow (400–600ms) fades and reveals; nothing snaps.
- **Fits:** premium brands, photography, architecture, high-end commerce.

---

## Using a direction

1. State your pick and one sentence on why it fits the content.
2. Extract its rules into CSS custom properties / Tailwind config *first* (colors, type scale, spacing, radius).
3. During screenshot review, the question is always: *"does this frame look unmistakably like the direction?"* — not "does it look nice."
