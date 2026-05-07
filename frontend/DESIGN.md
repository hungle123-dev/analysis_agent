# DESIGN.md

## Design Goal

Build a focused **AI Analysis Workbench** for data analysis with human approval. This should not look like a generic admin dashboard. It should feel like a lightweight analysis IDE:

- dataset context on the side
- AI request at the top
- generated code as the main object
- approval as an explicit gate
- execution artifacts and audit logs as evidence

The current UI direction should be simplified. It has too many visible regions competing for attention. The next version should reduce visual weight and make one decision obvious: **review this code, approve it, then run locally**.

## Research Notes

### DESIGN.md Pattern

`awesome-design-md` recommends keeping design systems in Markdown so AI coding agents can consistently apply the intended visual language. It structures design docs around theme, color roles, typography, component styling, layout, depth, do/don't rules, responsiveness, and agent guidance.

Useful takeaway for this project:

- Keep this file prescriptive, not inspirational.
- Give semantic tokens and layout rules.
- Include anti-patterns so future agents do not generate bulky cards.

Reference: https://github.com/VoltAgent/awesome-design-md

### Cursor-Inspired Direction

Cursor-style systems work for this app because they are designed around AI-first code editing: dark interface, compact chrome, editor-centered hierarchy, and subtle gradient/accent use.

Useful takeaway:

- Monaco/editor should be the visual center.
- AI affordances should be subtle, not cartoonish.
- Keep the shell dark and controlled.

Reference: https://getdesign.md/cursor/design-md

### Warp-Inspired Direction

Warp is relevant because it treats command execution as block-based, inspectable, and developer-focused. This maps well to the app's `proposal -> approval -> execution -> output` model.

Useful takeaway:

- Treat each execution as a block with input/code/status/output.
- Use status chips and compact command blocks.
- Keep terminal/output evidence visually separate from the editor.

Reference: https://getdesign.md/warp/design-md

### Sentry-Inspired Direction

Sentry is useful for audit timelines and error/result inspection: dark dashboard, dense data, clear severity/status accents.

Useful takeaway:

- Logs should be compact and timestamped.
- Failure states should be impossible to miss.
- Avoid decorative charts; artifacts are evidence, not decoration.

Reference: https://getdesign.md/sentry/design-md

### Tremor Direction

Tremor is relevant for chart/table/report panels. It provides React + Tailwind + Radix dashboard/chart components and emphasizes polished defaults for data interfaces.

Useful takeaway:

- Use KPI/data cards sparingly.
- Tables and charts should be clean, small, and evidence-oriented.
- Consider Tremor/Recharts later for real result rendering.

Reference: https://www.tremor.so/

### shadcn Dashboard Direction

shadcn dashboard templates are useful for consistent button/input/card/table primitives, responsive sidebar patterns, and accessible component behavior.

Useful takeaway:

- Use shadcn-style primitives if we need dialogs, tabs, dropdowns, command palette, toast, select, or resizable panels.
- Do not import a whole admin template look. This app is not an admin panel.

Reference: https://github.com/NaveenDA/shadcn-nextjs-dashboard

### Monaco Direction

`@monaco-editor/react` wraps Monaco, the web editor that powers VS Code. It supports React integration and multi-model editor patterns.

Useful takeaway:

- Keep Monaco, but reduce surrounding visual noise.
- Use editor tabs only if there are multiple generated files.
- Later, use Monaco markers for policy warnings instead of separate noisy warning boxes.

Reference: https://github.com/suren-atoyan/monaco-react

## Final Visual Direction

Use this blend:

```text
Cursor shell + Warp execution blocks + Sentry audit density + Tremor artifact polish
```

Do not copy any brand exactly. Use the patterns, not the trade dress.

## Layout Recommendation

### Preferred Desktop Layout

Use a 3-zone workbench, not 4 equally loud columns.

```text
┌────────────────────────────────────────────────────────────────────┐
│ Top command bar: dataset / request input / status                  │
├───────────────┬──────────────────────────────────────┬─────────────┤
│ Dataset       │ Main review area                      │ Inspector   │
│ context       │ - AI proposal summary                 │ - Artifacts │
│ + sessions    │ - Monaco code editor                  │ - Logs      │
│               │ - Approval gate                       │ - Policy    │
└───────────────┴──────────────────────────────────────┴─────────────┘
```

Target proportions:

- Left sidebar: 240-280px.
- Main editor: flexible, at least 560px.
- Inspector: 340-400px.
- Activity rail is optional. If kept, make it 48px and very quiet.

### Better Alternative For Less Bulk

Move artifacts/logs/policy into inspector tabs:

```text
Inspector tabs: Result | Logs | Policy
```

This will immediately make the UI feel less heavy because result, audit log, and policy do not all compete at once.

### Mobile Layout

Collapse to:

1. Dataset selector.
2. Prompt.
3. Proposal/editor.
4. Approval actions.
5. Result/log tabs.

Do not try to preserve the desktop IDE layout on mobile.

## Color System

Use a dark neutral shell with role-based accents.

| Token | Hex | Role |
| --- | --- | --- |
| `ink` | `#0F1012` | app background |
| `panel` | `#17181B` | main panels |
| `panelRaised` | `#202126` | controls/cards |
| `panelHover` | `#292B31` | selected/hover |
| `line` | `#30323A` | borders |
| `lineSoft` | `rgba(255,255,255,0.08)` | subtle separators |
| `text` | `#F4F1EA` | primary text |
| `muted` | `#A8A39B` | secondary text |
| `dim` | `#76716A` | tertiary labels |
| `ai` | `#8F7CF6` | AI proposal/accent |
| `approve` | `#4FD1B8` | approved/success/run allowed |
| `review` | `#E0AD4F` | pending/review/warning |
| `danger` | `#EE6B7C` | reject/error |
| `data` | `#7EB6FF` | dataset/artifact |

Rules:

- Use only one primary accent per component.
- Do not make everything teal.
- AI accents are violet.
- Execution success is mint.
- Dataset/artifact indicators are blue.
- Review/waiting states are amber.
- Reject/failure states are rose.

## Typography

Use compact tool typography.

| Element | Size | Weight | Notes |
| --- | --- | --- | --- |
| App title | 20-22px | 700 | only once |
| Panel title | 15-17px | 700 | compact |
| Body | 13-14px | 400-500 | normal UI text |
| Metadata | 12px | 500 | timestamps, rows |
| Labels | 11px | 800 uppercase | sparse use |
| Code | 13-14px | normal | Cascadia Code/Consolas |

Avoid oversized headings. This is an operational tool.

## Component Rules

### Command Bar

The command bar should contain:

- dataset name or selector
- prompt input
- generate button
- current workflow status

It should feel like a command input, not a chat app.

### Dataset Sidebar

Keep it dense:

- dataset list
- selected dataset metadata
- schema rows
- optional session list

Do not show every log here. Logs belong in inspector.

### AI Proposal Header

Should show:

- proposal title
- concise summary
- risk chips
- generated time or proposal id

Avoid alert-style yellow boxes unless there is a real warning.

### Monaco Code Editor

The code editor should be the main surface.

Rules:

- stable height
- no layout jumping when code loads
- tabs only if multiple files exist
- line numbers visible
- no minimap for this app
- policy warnings can later become Monaco markers

### Approval Gate

Approval must be visually distinct and semantically clear.

It should show:

- current state
- code hash
- approver
- approve/reject buttons
- run button disabled until approved

Use fixed action order:

```text
Reset | Reject | Approve | Run local
```

### Inspector Panel

Use tabs:

- `Result`: chart/table/stdout artifacts
- `Logs`: audit timeline
- `Policy`: checker results and blocked operations

This reduces clutter. It also maps to how teachers will inspect the demo.

### Result Artifacts

Results are evidence, not decoration.

Display:

- chart preview
- table preview
- stdout/stderr
- artifact paths

Do not show fake decorative charts once backend exists. Chart must come from execution artifact.

### Audit Timeline

Use compact rows:

```text
time / actor / event type / short detail
```

Important events:

- request created
- proposal generated
- code edited
- approved/rejected
- execution started
- execution succeeded/failed

## Interaction Model

State should drive UI:

| State | Main UI behavior |
| --- | --- |
| `pending_review` | editor enabled, run disabled |
| `edited` | editor enabled, approve highlighted |
| `approved` | run enabled, code hash visible |
| `running` | actions disabled except cancel if implemented |
| `succeeded` | result tab opens automatically |
| `failed` | policy/error tab opens automatically |
| `rejected` | run disabled, proposal can be regenerated |

## Anti-Bloat Rules

- Do not show sidebar, artifacts, logs, policy, and review note with equal weight.
- Do not put cards inside cards.
- Do not use long explanatory paragraphs inside controls.
- Do not keep policy gates permanently large; make them a tab or compact checklist.
- Do not use more than 2 visible borders around a single content region.
- Do not use decorative gradients behind every panel.
- Do not use status chips everywhere. One global status plus local action state is enough.
- Do not let Monaco overlap or intercept approval controls.

## Concrete Redesign Plan

### Pass 1: Simplify Layout

- Remove right policy rail.
- Move policy into inspector tab.
- Keep left dataset sidebar.
- Keep center editor.
- Keep right inspector with tabs.

### Pass 2: Reduce Visual Noise

- Replace many small cards with table-like rows.
- Remove duplicate status labels.
- Use one panel border per major zone.
- Make proposal summary one line unless expanded.

### Pass 3: Improve Result Area

- Use real tabs: `Result`, `Logs`, `Policy`.
- Result shows artifact cards only after execution.
- Empty states should be small and quiet.

### Pass 4: Improve Review Flow

- Approval bar always visible under editor.
- Run button disabled until approved.
- After run succeeds, auto-switch inspector to `Result`.
- After failure, auto-switch inspector to `Policy` or `Logs`.

## Tailwind Implementation Guidance

Use Tailwind utility classes for most styling. Keep `src/styles.css` limited to:

- `@import "tailwindcss"`
- `@theme` tokens
- base html/body reset

Extract repeated patterns into small React components, not large CSS classes:

- `Panel`
- `PanelHeader`
- `StatusBadge`
- `ActionButton`
- `InspectorTabs`
- `SchemaRow`
- `TimelineRow`

## Recommended Next UI Change

The next implementation should not just recolor the current UI. It should change information architecture:

```text
Current: left sidebar + center editor + result panel + policy rail
Better:  left sidebar + center editor + right tabbed inspector
```

This is the highest-impact fix for the current "xau va cong kenh" problem.
