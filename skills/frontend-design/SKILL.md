---
name: frontend-design
description: Design direction for building web UI that doesn't look like generic AI output. Covers committing to a bold aesthetic before writing code, typography and spacing systems, color discipline, and an iterative review-by-screenshot loop. Use when building any user-facing interface — landing pages, dashboards, apps, or components — where visual quality matters.
license: MIT
metadata:
  version: "2.0.0"
---

# Frontend Design

Generic AI UI has a recognizable signature: centered hero, gradient-on-purple, three feature cards with icons, `Inter` everywhere, uniform rounded corners, no point of view. The cure is **committing to a specific design direction before writing any code**, then verifying visually.

## 1. Commit to an aesthetic first

Before any markup, write 2–3 sentences declaring the direction. Name a real-world reference ("brutalist editorial, like a print magazine", "dense pro tool, like a trading terminal", "warm paper-and-ink, like a field notebook"). Pick from a deliberately distinct palette of directions — see [references/aesthetic-directions.md](references/aesthetic-directions.md) for eight worked options with concrete type/color/layout choices.

Rules:

- **One direction, fully committed.** A timid blend of two aesthetics reads as no aesthetic.
- The direction must fit the content: a compliance dashboard and a music festival page should be unmistakably different.
- Every subsequent choice (font, spacing, corner radius, motion) is checked against the stated direction. If you can't justify a choice in terms of the direction, it's a default sneaking in.

## 2. Typography carries the design

Typography is 80% of perceived design quality:

- **Pick one distinctive display face + one workhorse body face.** Never default to the system stack or the same overused sans for both. Serif/sans contrast, or a characterful grotesque, immediately de-generifies a page.
- **Establish a type scale** and stick to it, e.g. `12 / 14 / 16 / 20 / 28 / 40 / 64px`. Ad-hoc font sizes are the #1 tell of unsystematic design.
- Big is a design decision: headlines at 56–96px with tight line-height (1.0–1.1) and slight negative letter-spacing read as intentional. Body text: 16–18px, line-height 1.5–1.7, measure 60–75 characters — unless the chosen direction dictates otherwise (e.g. Dense Pro Tool runs 12–14px deliberately).
- Use weight and size for hierarchy before reaching for color.

## 3. Spacing system

- All spacing from one scale (e.g. multiples of 4 or 8: `4/8/12/16/24/32/48/64/96`). Consistent rhythm is felt even when unnoticed.
- **Be generous, then asymmetric.** Cramped layouts look amateur; uniform padding everywhere looks templated. Give sections room (64–128px vertical) and let some elements break the grid deliberately.
- Group by proximity: related items close (8–16px), unrelated far (48px+). Spacing *is* information architecture.

## 4. Color discipline

- One dominant neutral family + **one** committed accent. Not three accents. Off-blacks (`#111` on `#fafaf7`) beat pure black-on-white.
- Decide light or dark deliberately from the aesthetic, not by default.
- Gradients, glassmorphism, and glow effects are opt-in per the direction — never reflexive.
- Check contrast (WCAG AA: 4.5:1 body text) — stylish and unreadable is failed design.

## 5. Details that separate designed from generated

- Corner radius is a *voice*: sharp (0–2px) = editorial/serious, medium (6–10px) = product, full pill = playful. Pick one, apply consistently.
- Borders vs. shadows: choose one elevation language.
- Real content in layouts — realistic names, plausible numbers, varied string lengths. Lorem ipsum hides layout bugs and looks lazy.
- Micro-interactions: hover/focus states on every interactive element; 150–250ms transitions; visible focus rings.
- Empty states, loading states, and long-content states are part of the design, not an afterthought.

## 6. The review-by-screenshot loop

You cannot judge UI from source code. Iterate visually:

1. Build → render in a real browser → **screenshot**.
2. Critique the screenshot as a demanding design reviewer: What looks templated? Where does hierarchy fail? What would a designer fix first? Is the stated aesthetic actually visible, or did defaults creep back?
3. Fix the top 2–3 issues. Re-screenshot. Repeat — plan for **at least 2–3 rounds**; first renders are never right.
4. Check multiple states: mobile (375px), desktop (1440px), longest text, dark/light if applicable, keyboard focus.

If you can screenshot but the result "looks fine," you're not critiquing hard enough — name three specific improvements anyway; the first render is never the ceiling.

## Anti-pattern checklist (reject your draft if any are true)

- [ ] Uses the same ubiquitous sans-serif for everything with no display face
- [ ] Purple-to-blue gradient hero with centered text and three icon cards
- [ ] Every element has the same corner radius and same shadow
- [ ] No spacing scale — padding values are improvised per element
- [ ] Shipped without ever viewing a rendered screenshot
- [ ] Could be swapped onto any other product without anyone noticing
