---
product: LLM Output Arbitration System
accent: teal
radius: 8px controls / 12px panels
theme: auto (light + dark, no mid-page inversion)
---

# DESIGN.md

Forensic evaluation workspace for AI answers. Not a marketing landing page, not a SaaS dashboard template.

## Intent

The UI is a docket: submit a question and a model answer, then inspect extracted claims, independent judge votes, and a preliminary confidence score. Trust and readability beat decoration. Every number is a score, never decoration.

## Audience

Engineers and researchers checking whether an LLM answer is supported. They need contrast, keyboard access, and honest empty/loading/error states.

## Theme

One theme family for the whole product. Default to `prefers-color-scheme`. Manual toggle persists in `localStorage`.

Do not invert a section to the opposite theme. Tint within the same family only (`--bg` next to `--bg-raised`).

### Tokens

| Token | Light | Dark |
| --- | --- | --- |
| `--bg` | `#eceef1` | `#121316` |
| `--bg-raised` | `#f7f8f9` | `#1b1c20` |
| `--bg-inset` | `#e4e6ea` | `#0e0f12` |
| `--text` | `#1a1c1f` | `#f2f3f4` |
| `--text-muted` | `#5c6168` | `#a7adb6` |
| `--line` | `#d5d8de` | `#2a2d33` |
| `--accent` | `#0f766e` | `#2dd4bf` |
| `--accent-fg` | `#f7f8f9` | `#102422` |
| `--supported` | `#047857` | `#34d399` |
| `--incorrect` | `#b42318` | `#f87171` |
| `--uncertain` | `#b45309` | `#fbbf24` |
| `--focus` | `#0f766e` | `#2dd4bf` |

Accent is teal only. Verdict greens/reds/ambers are semantic status, used only on verdicts, votes, and related labels.

No pure `#000000` or `#ffffff`. No purple glow. No gradient text.

## Type

- UI: Outfit (variable), 15px body, 500 for labels, 600 for titles.
- Numbers, IDs, scores, claim IDs: IBM Plex Mono.
- Display score: IBM Plex Mono, large, tabular figures.
- Max body measure: 65ch.
- Do not use Inter, Fraunces, or Instrument Serif.

## Shape

- Panels: 12px radius.
- Inputs, buttons, chips: 8px radius.
- No pills on primary actions.
- Nested radii: child 8px inside 12px parent.

## Layout

Desktop: 12-column workspace. Intake is 5 columns, docket is 7. Mobile (`< 768px`): single column, intake first, docket second.

Header is one line, max 64px. No second nav row.

Use hairlines and spacing for grouping. Cards only when a block is a self-contained exhibit (one claim with its votes).

## Motion

`MOTION_INTENSITY: 4`. Opacity and transform only. Spring on result enter. Honor `prefers-reduced-motion` (instant, no stagger). Minimum loading visibility 400ms so skeletons do not flicker.

## Icons

Phosphor only, `weight="regular"`, size 16 or 20. No Lucide, no hand-drawn SVG marks. Product mark is Phosphor `Scales`.

## Copy

Plain, second person, no filler verbs (elevate, seamless, unleash). No em-dash or en-dash. Hyphen only. Primary CTA label: `Evaluate`. Secondary: `Load example`.

## States

- Empty docket: tell the user what to paste and what will appear.
- Loading: skeleton that matches the verdict + claim layout.
- Error: inline under the form, first error focused, submit stays enabled until the request starts.
- Success: announce via `aria-live="polite"`.

## Forms

Labels above fields. Helper text in markup. Errors below fields. Placeholders are examples ending with an ellipsis. Textareas: Enter inserts a line, Ctrl/Cmd+Enter submits. Do not disable paste. Do not pre-disable submit.

## Accessibility

Visible `:focus-visible` rings using `--focus`. Hit targets at least 24px (44px on mobile). Icon-only buttons have `aria-label`. Semantic `button`/`label`/`output`. Do not rely on color alone for verdict: include a text label.

## Out of scope for this file

Marketing landing, logo walls, bento marketing grids, fake product screenshots.
