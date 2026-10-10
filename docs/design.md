# Intellect Frontend Design Reference

**Written:** 2026-10-10  
**Derived from:** `frontend/src/` (especially `monochrome.css`, `App.css`, `assistant.css`, `projects.css`, `login.css`, and related component styles)  
**Purpose:** Describe the visual system currently implemented in the Intellect frontend. This is a reference for extending the existing UI, not a proposal to replace it.

> Values below are observed in the current CSS. The stylesheet system has accumulated base styles and later overrides; where that makes the rendered intent uncertain, the ambiguity is called out rather than resolved by inventing a token.

## 1. Product direction

Intellect is a collaborative document intelligence workspace. Its interface emphasizes focused reading and writing, project-scoped navigation, grounded answers, evidence, and generated knowledge views.

- **Aesthetic:** restrained, technical, monochrome, and compact.
- **Brand character:** the owl mark and wordmark provide identity. The signed-in workspace is predominantly grayscale; blue remains in some secondary styles and state treatments.
- **Primary surfaces:** near-black canvas, slightly lifted dark panels, fine gray borders, and high-contrast light controls.
- **Density:** compact metadata and controls, with larger readable answer content and spacious page-level document tools.
- **Themes:** the active workspace is dark. `index.css` defines a light base, but the application imports `theme-dark.css` and `monochrome.css`; no user-facing theme switch is present in the inspected UI.

## 2. Typography

### Typeface

The interface uses **JetBrains Mono** for the global UI, loaded from Google Fonts in `frontend/src/index.css`. The stack falls back to common system monospace fonts (`ui-monospace`, SFMono-Regular, Menlo, Consolas, monospace). The monospace choice is part of the product's technical character and applies to body copy, controls, headings, and data labels.

### Observed scale and roles

There is no centralized type scale. CSS uses a broad range of explicit pixel sizes, often smaller than conventional product UI defaults. These are the current patterns, not a recommendation to shrink new content further.

| Role | Observed size / treatment | Examples |
|---|---|---|
| Main page heading | 29px, tight tracking; login hero uses `clamp(38px, 5vw, 68px)` | Documents page, sign-in context |
| Workspace welcome | 31px, 600 weight | Chat welcome heading |
| Section / panel heading | 13–17px, usually medium or semibold | Insights, dialogs, sign-in form |
| Main answer body | 16px in the active monochrome rules, line-height about 1.5 | Assistant markdown |
| Supporting body | 11–14px | Descriptions, login copy, insights |
| Controls and metadata | commonly 10–13px | Buttons, table labels, status, source details |
| Fine metadata | 7–10px | File type, process status, helper text |

Use semibold weight sparingly for page headings, labels, and key numbers. Body text is generally regular; conversation and file names use medium weight.

## 3. Color

The UI has no formal CSS-variable palette. The values below summarize the active monochrome treatment and important existing state colors.

### 3.1 Core dark palette

| Role | Current value / examples |
|---|---|
| App canvas | `#090909` (also `#0b0e14` in earlier dark theme rules) |
| Panels and headers | `#0d0d0d` |
| Inputs and inset surfaces | `#111111` to `#151515` |
| Hover / selected surface | `#1b1b1b` to `#252525` |
| Borders and dividers | `#292929` to `#3a3a3a` |
| Primary text | `#ededed` to `#f5f5f5` |
| Secondary text | `#999999` to `#aaaaaa` |
| Muted metadata | `#666666` to `#888888` |
| Light action surface | `#eeeeee` to `#f3f3f3`, with dark text |

### 3.2 Accent and status

- Earlier workspace styling uses a medium blue (`#3473e6`, with related shades around `#3b73da`) for primary actions, selected graph nodes, evidence, and focus/drag states. The final monochrome layer replaces many prominent blue fills with neutral light fills, but blue remains in some component-specific rules. Reuse an existing component's local state treatment when matching that component.
- Status indicators in the document list use green for ready, amber for processing/uploaded, and red for failed. `monochrome.css` overrides these dots to grayscale in its sidebar list; document table status labels retain distinct failed text styling.
- Errors use muted red text such as `#e48a8a` or `#e79292` against dark surfaces.
- Do not rely on color alone for status: the existing UI also uses text labels and icons.

## 4. Layout, spacing, and shape

### App shell

- Desktop workspace: fixed-height viewport with a left project/navigation sidebar, central content, and an optional right intelligence panel.
- In the active monochrome rules, the sidebar is 280px; opening the intelligence panel splits the remaining layout with a second flexible column. Earlier rules specify a 360px panel, so treat panel width as responsive rather than a fixed universal token.
- The top header is 68px high in the active workspace styling.
- The main chat reading area is centered, with a maximum width around 840–920px depending on content type.
- The documents view uses a centered maximum width of 1120px and responsive horizontal gutters.
- At widths below 900px the intelligence panel becomes an overlay; below 640px the sidebar becomes a slide-in drawer. The sign-in page hides its marketing/context column below 800px.

### Spacing

Spacing is specified directly in component CSS. Common increments are 4, 6, 7, 8, 10, 12, 14, 16, 20, 24, and 32px. Prefer the familiar 4px rhythm where it fits; match neighboring component spacing in dense UI.

### Corners

Rounded corners are consistent but not tokenized:

| Radius | Common use |
|---|---|
| 4–6px | Small chips, inline code, table status, compact controls |
| 7–9px | Buttons, inputs, nav items, file icons, graph nodes |
| 12–14px | Dialogs, message bubbles, composer, larger containers |
| 50% / full | Avatars and circular count markers |

Borders are generally 1px and low contrast. Elevation comes mostly from subtle borders and soft shadows, not large layered shadows.

## 5. Components and patterns

### Navigation and project sidebar

- Brand mark and lowercase `intellect` wordmark sit at the top.
- Project selection precedes a two-item Chat / Documents navigation.
- Chat history uses compact rows with a clear active/hover background; search is inline.
- New chat is a full-width bordered control. Account identity and sign-out sit at the bottom, separated by a divider.
- On narrow screens, the sidebar is a drawer with a dark scrim.

### Chat

- The welcome state centers the owl mark, a short heading, supporting copy, and suggestion chips.
- User messages align right in a contrasting bubble. Assistant responses align left with a small assistant mark and markdown content.
- The composer is a bordered, rounded panel anchored to the bottom of the reading area. Attachments appear as compact file cards; sending and canceling use a square icon button.
- Grounding evidence is expandable beneath answers. Sources and retrieval chunks use bordered inset cards, with source number, filename/metadata, and excerpt.
- Processing status uses a short sequence of labels and animated dots. Follow-up prompts appear as compact outlined chips.

### Documents

- Page heading and upload action sit above a dashed drop zone.
- Files appear in a bordered table with document identity, processing status, size, page count, and row actions. On mobile, the header and secondary columns are hidden and rows collapse to a simpler two-column layout.
- Empty, loading, uploading, and failed-upload states have dedicated inline treatments.

### Project intelligence

- Right-side panel has a heading, current-conversation context, generate/regenerate action, and Graph / Insights tabs.
- Graphs use a dark grid canvas, neutral node styling, connecting edges, and interactive expand/collapse nodes.
- Insights are a scrollable list of takeaways and prioritized actions with numbered markers and source-turn metadata.

### Dialogs and forms

- Dialogs are centered, dark, bordered, rounded panels over a dark translucent scrim, with concise title/description and right-aligned actions.
- Inputs use dark inset fills and subtle borders. Focus treatment varies by component; preserve visible keyboard focus when adding controls.
- Destructive actions use confirmation dialogs.

### Icons and illustration

- Use Lucide icons for interface controls and actions.
- The owl mascot and app mark are custom SVG/image assets. They are decorative when paired with a visible text label.
- Avoid emoji as interface icons.

## 6. Motion and interaction

Motion is subtle and supports state changes rather than decoration:

- Sidebar and panel transitions use opacity/position and grid resizing, generally around 150–350ms with ease-out style curves.
- Dialogs fade in and rise slightly; graph nodes widen when expanded.
- Upload and answer-processing states animate a pulse; spinners rotate linearly.
- Hover states usually transition through background, border, or text color.

Honor reduced-motion preferences when adding longer or repeated motion. Keep interaction states understandable without animation.

## 7. Accessibility and implementation notes

- Preserve semantic buttons, labels, table headings, and dialog primitives already used in the app.
- Icon-only controls need accessible names; decorative mascot and icons should remain hidden from assistive technology when adjacent text supplies the meaning.
- Keep keyboard focus visible. `focus.css` currently removes the outline on focused controls in some contexts, so new components should not copy that removal without a clear replacement focus indicator.
- Keep status meaning in text as well as color.
- The current smallest metadata text is 7px. Avoid using that size for essential instructions or content; prefer a legible size for new work.

## 8. Source and cascade caveats

- `CollaborativeApp.tsx` imports `monochrome.css` after the other workspace styles. Its later, more specific overrides define much of the active signed-in appearance.
- `theme-dark.css` and several component styles still contain earlier blue-accent/dark-theme values. Not every value is overridden by the monochrome layer, so localized blue remains in evidence, attachment, and some graph states.
- `index.css` sets a light root default and a focus-visible outline, while `theme-dark.css` and `monochrome.css` set dark rendering and `focus.css` later removes some outlines. Treat this as an implementation caveat, not as a documented light theme or a universal focus recipe.
- Styles for the sign-in screen are in `login.css`; it is a separate near-black experience with a light primary submit button and an animated typing headline.
- There is no shared token file or CSS custom-property contract yet. If the frontend adopts reusable design tokens, derive and consolidate them from this reference without changing the existing visual direction unintentionally.

## 9. Practical checklist for new UI

- [ ] Use the dark near-black canvas, restrained borders, and high-contrast text.
- [ ] Use JetBrains Mono and follow the neighboring component's type size and density.
- [ ] Reuse existing button, input, card, dialog, and status treatments before adding new patterns.
- [ ] Keep blue use consistent with the local component state; avoid introducing a second unrelated accent.
- [ ] Make status understandable through text or an icon as well as color.
- [ ] Check narrow layouts, keyboard focus, and reduced-motion behavior.
- [ ] Treat values here as observed implementation details; update this document when the frontend's visual system materially changes.
