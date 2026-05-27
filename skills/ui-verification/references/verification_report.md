# Verification Report

Generate a structured markdown report covering both visual verification (deterministic CSS checks) and flow verification (Gherkin scenarios). The combined report at `reports/<run-timestamp>/report.md` is human-readable, links to the live app, and embeds annotated screenshots and per-flow detail.

If a run produces only one mode's output (the user asked for visual-only or flow-only), the other section is omitted entirely from the combined report.

## Output Location

```
<output_dir>/.ui-verification/reports/
  <run-timestamp>/                ← UTC YYYYMMDD-HHmmssZ (a run can span multiple sessions)
    report.md                     ← combined visual + flow summary
    screenshots/                  ← visual annotated failures (one per category)
      visual_style.png
      component_rules.png
      ...
    flow-reports/                 ← per-flow reports (one per .feature run)
      <flow-name>.report.md
    sessions.json                 ← manifest of session IDs that participated in this run
```

**Hard rule: ALL report artifacts MUST be written inside `<output_dir>/.ui-verification/`.** This includes:
- Annotated failure screenshots → `reports/<run-timestamp>/screenshots/`
- Per-flow reports → `reports/<run-timestamp>/flow-reports/`
- The combined report → `reports/<run-timestamp>/report.md`
- The sessions manifest → `reports/<run-timestamp>/sessions.json`

Any `screenshot()` call whose output is referenced in the report MUST pass a `destination` path under this directory. Screenshots taken purely for agent-side reasoning (Phase 1 exploration in spec generation) may go to `/tmp/` since they are ephemeral working memory not referenced in any persisted artifact. But if a screenshot is embedded or linked in `report.md` or a per-flow report, it MUST live in `reports/<run-timestamp>/screenshots/`.

Visual assertion JSON written by the MCP server lives at `<output_dir>/.ui-verification/sessions/<session_id>/<category>_assertions.json` — under a sibling `sessions/` tree, not inside `reports/<run-timestamp>/`. The report renderer reads it from there at report-time and references it by relative path (`../../sessions/<session-id>/...`); no duplication into the run directory.

## Sessions Manifest

Each run directory has a `sessions.json` manifest listing the session IDs that participated:

```json
{
  "run_timestamp": "20260515-143022",
  "sessions": [
    {"session_id": "abc123-def456", "mode": "visual", "url": "https://example.com/app"},
    {"session_id": "ghi789-jkl012", "mode": "flow", "flow_id": "mira-2", "url": "https://aws-mira-prod.turing.com"}
  ]
}
```

The manifest connects the run to per-session artifact directories under `sessions/<session-id>/`. Visual runs produce assertion JSON there; flow runs may produce screenshots or other per-session output. The manifest is the source of truth for "which sessions belong to this run" — useful when a run spans multiple sessions (one per flow plus one for visual).

**Write semantics.** Build the full manifest in memory across the run, then write it once at end-of-run via the temp-then-rename pattern. Same atomicity guarantee as `.integrity.json`:

```bash
# Build the JSON in memory as sessions are opened, then at end of run:
cat > .ui-verification/reports/<run-timestamp>/sessions.json.tmp <<EOF
{
  "run_timestamp": "<run-timestamp>",
  "sessions": [ ... every session opened during this run ... ]
}
EOF
mv .ui-verification/reports/<run-timestamp>/sessions.json.tmp \
   .ui-verification/reports/<run-timestamp>/sessions.json
```

Do NOT write incrementally as each session is opened — partial manifests left behind by a crashed run are worse than no manifest. End-of-run rewrite + atomic rename is the canonical pattern (`mv` is atomic on POSIX). Crash mid-run leaves no `sessions.json` for that run; the rest of the report directory documents what happened.

## Combined Report Format

The combined `report.md` has up to two main sections: **Visual Verification** and **Flow Verification**. Each section is omitted if that mode didn't run. When both ran, visual comes first, then flow.

```markdown
# UI Verification Report

**Site:** [https://example.com/app](https://example.com/app)
**Run:** 20260515-143022 (UTC)
**Total Duration:** 47.3s
**Scope:** <what the user asked to verify — e.g. "all categories + flows mira-2 mira-3" or "visual only">

# Visual Verification

(visual section — see § Visual Section Format below)

# Flow Verification

(flow section — see § Flow Section Format below)
```

## Visual Section Format

When the visual section is rendered as part of the combined report, it sits under `# Visual Verification` (a section, not a top-level heading). The structure below uses `##` as the leading section header inside the combined report.

```markdown
# Visual Verification

**Site:** [https://example.com/app](https://example.com/app)
**Date:** 2026-05-14T15:30:00Z
**Session:** abc123-def456
**Scope:** <what the user asked to verify — e.g. "all categories" or "design.md lines 7–8 colors.primary">

## Summary

| Category | Rules | Verified | Passed | Failed | Skipped (audit) |
|---|---|---|---|---|---|
| Visual Style | 13 | 12 | 10 | 2 | 1 |
| Components | 8 | 8 | 8 | 0 | 0 |
| Accessibility | 6 | 6 | 5 | 1 | 0 |
| Project Rules | 5 | 5 | 5 | 0 | 0 |
| Platform Conventions | 4 | 4 | 3 | 1 | 0 |
| **Total** | **36** | **35** | **31** | **4** | **1** |

**Column meanings:**
- `Rules` = total rules in scope, including skipped
- `Verified` = rules actually run through verify_* (= Passed + Failed)
- `Skipped (audit)` = rules excluded from this run because audit classified them ORPHAN or DIVERGENT
- `Rules` = `Verified` + `Skipped (audit)` always — the arithmetic must close

If any rule was skipped, the report MUST include an "Audit Findings" section (see below) before the Failures section. Skipped rules are NOT failures — they're contamination the user resolves separately.

## Audit Findings

**(Include this section ONLY if rules were skipped. Place between Summary and Failures so the user sees it before reading the failure table — contamination context changes how the user interprets the rest of the report.)**

The integrity ledger (`.ui-verification/.integrity.json`) was missing / had hash mismatches, so an audit ran before verification. The following rule(s) were flagged and not run:

**DIVERGENT — `<rule name from category file>`** (in `<category>.md` under `<scope>`)

- Selector: `<selector>`
- Property: `<property>`
- Constraint in rule: `<constraint>`
- Why divergent: <one-paragraph diagnosis: which design.md claim it conflicts with, what the rule asserts vs what design.md assigns>

Resolution options for the user (do NOT auto-apply any of these):
1. **Drop the rule** — remove from category file
2. **Update design.md** — add the missing assignment so the rule reflects intent
3. **Recompile from scratch** — re-derive from design.md alone

The ledger has NOT been written this run because contamination exists. Next run will re-audit until contamination is resolved.

**ORPHAN — `<rule name>`**

(Same structure for any orphans. Use ORPHAN when the rule has no design.md/source backing at all; DIVERGENT when there's partial backing but the constraint contradicts.)

## Failures

### Visual Style

**Page:** [https://example.com/app](https://example.com/app)

| # | Rule | Selector | Expected | Actual | Match shape | Failing instances |
|---|---|---|---|---|---|---|
| 1 | Canvas background dark: rgb(10,14,26) | `body` | ~rgb(10,14,26) | rgb(15,23,42) | categorical (1 of 1) | BODY |
| 2 | section-subtitle size: 19.2px | `.section-subtitle` | =19.2px | 16px | partial (1 of 2) | H3.section-subtitle |

![Visual Style Failures](screenshots/visual_style.png)

### Accessibility

**Page:** [https://example.com/app](https://example.com/app)

| # | Rule | Selector | Expected | Actual | Match shape | Failing instances |
|---|---|---|---|---|---|---|
| 1 | navigation landmark present | `[role=navigation]` | !=none | selector not found | not-found (0 matches) | — |

_(No screenshot — element not found in DOM)_

### Platform Conventions

**Page:** [https://example.com/app](https://example.com/app)

| # | Rule | Selector | Expected | Actual | Match shape | Failing instances |
|---|---|---|---|---|---|---|
| 1 | Hero CTA button | `.hero-cta` | !=none | selector not found | not-found (0 matches) | — |

![Platform Conventions Failures](screenshots/platform_conventions.png)

## Passing Rules

<details>
<summary>31 rules passed (click to expand)</summary>

| Category | Rule | Selector |
|---|---|---|
| Visual Style | body text primary | `body` |
| Visual Style | body font family | `body` |
| Visual Style | hero-title font family | `.hero-title` |
| ... | ... | ... |

</details>
```

## Assertion JSON Schema

`verify_*` writes one file per category at `<output_dir>/.ui-verification/sessions/<session_id>/<category>_assertions.json` with this exact shape:

```json
{
  "category": "visual_style",
  "url": "http://localhost:3000/",
  "created_at": "2026-05-19T06:51:44.747419+00:00",
  "updated_at": "2026-05-19T06:51:44.747419+00:00",
  "assertions": [
    {
      "name": "Hero primary CTA radius: 10px",
      "selector": ".hero-cta.btn-primary",
      "property": "border-radius",
      "constraint": "=10px",
      "passed": true,
      "total_elements": 1,
      "passed_elements": 1,
      "failed_elements": 0,
      "failures": [],
      "verified_at": "2026-05-19T06:51:44.747419+00:00"
    }
  ]
}
```

Top-level keys: `category`, `url`, `created_at`, `updated_at`, `assertions`. Per-assertion keys: `name`, `selector`, `property`, `constraint`, `passed`, `total_elements`, `passed_elements`, `failed_elements`, `failures`, `verified_at`. Each entry in `failures[]` has `actual` (the value found) and `element` (`TAG.first-class` form, e.g. `BUTTON.btn-primary`). **Note:** the top-level array is `assertions` (not `rules`), and each entry stores rule fields directly (not wrapped under a `rule` key).

**Use the Read tool to consume this file, not `python3 -c`.** Read returns the full file with line numbers — the assertion array is small (one entry per rule, typically tens, not thousands), so the whole file fits in context. Reading lets you reason about failures natively rather than building one-shot Python parsers. Reach for `python3 -c` only if a specific run's JSON is genuinely too large to read (rare) or you need a structural transformation (e.g. JSON → CSV); for "show me which rules failed and why," Read is the right tool.

## Workflow (Visual)

Run this after all verify_* calls are complete:

1. **Collect inputs (read-only, never modify):**
   - **Assertion JSON** at `<output_dir>/.ui-verification/sessions/<session_id>/<category>_assertions.json` — write-once OUTPUT of verify_*. Read for verdicts, selectors, actuals, failure detail. NEVER edit. See § Assertion JSON Schema above for the file shape.
   - **Category files** at `<output_dir>/.ui-verification/specs/<category>.md` — read for `## Scope:` membership of each rule.
   - **Audit results** from `verification.md` step 4 — list of rules classified ORPHAN or DIVERGENT (skipped this run).
2. **Join scope onto each rule for the report.** Build a per-rule view in memory: take each assertion's `name`, look up which `## Scope:` section(s) it lived under in the category file, attach the scope(s) to the row. This join happens at report-render time only — assertion JSON itself stays exactly as the MCP server wrote it.

   **Rule names that appear in multiple scope sections.** A rule's `Name` can appear in more than one `## Scope:` section when the Compiler duplicated the row across routes (design.md expressed the rule once but it applies to several routes — see `references/spec_sync.md` § Category File Format). Each duplicated row sits in exactly one scope section on disk; the same Name just shows up on multiple rows. In that case, render the joined scope as a comma-separated list (e.g. `route=/, route=/app/**`) rather than a single value. Pass/fail verdicts come from each verify_* call's URL-filtered run; the rendered scope just reflects every scope section the rule name lived under.

   **Filter out stale assertion entries.** Assertion JSON accumulates rules by `name` across multiple verify_* calls in the same session (the MCP server's per-session merge behavior). If a rule was renamed between calls, the old name's assertion stays in the JSON. The report renders ONLY rules whose `name` exists in the current category file — entries in the JSON with no matching rule in `specs/<category>.md` are silently dropped from the report. They aren't deleted from the JSON (it stays write-once), just excluded from the rendered output. This keeps the report a faithful view of "what the current spec asserts" rather than "what was ever asserted in this session."
3. **Compute the summary counts.** For each category:
   - `Rules` = rules in scope including skipped
   - `Verified` = rules run through verify_* (Passed + Failed)
   - `Skipped (audit)` = rules excluded by audit
   - Sanity check: `Rules == Verified + Skipped (audit)` for every row
4. **If any rule was skipped, write the Audit Findings section** (between Summary and Failures). For each skipped rule, include name, selector, property, constraint, why divergent/orphan, and the three resolution options. Note that the integrity ledger has NOT been written this run.
5. **For each category with failures:**
   a. Navigate to the page where failures occurred (if multi-page).
   b. Scroll to bring failing elements into viewport if needed.
   c. Run the annotation script (see `references/annotate_failures.md`) with that category's failures.
   d. Capture screenshot: `screenshot(session_id, destination="<output_dir>/.ui-verification/reports/<run-timestamp>/screenshots/<category>.png")`
   e. Run cleanup script to remove overlay before next category.
6. **Write report.md** to `<output_dir>/.ui-verification/reports/<run-timestamp>/report.md`.
7. **Respond to user** linking the report — never the assertion JSON.

## Workflow (Flow)

Run this after all flows finish executing (see `references/flow_verification.md`):

1. **Collect inputs (read-only, never modify):**
   - **Per-flow execution data** — gathered during the run by `flow_verification.md` (step results, timings, findings, cleanup status).
   - **`.feature` files** at `<output_dir>/.ui-verification/flows/<flow-name>.feature` — read for the original Goal text and step structure.
2. **Write per-flow reports.** For each flow, write `<output_dir>/.ui-verification/reports/<run-timestamp>/flow-reports/<flow-name>.report.md` using the per-flow format above. Every flow gets a report regardless of pass/fail/skipped — including skipped flows (the report explains why it was skipped).
3. **Aggregate the flow section.** Build the Run Info table, Results table (with relative links to per-flow reports), Audit Findings (skipped flows only), and Warnings.
4. **Render to the combined `report.md`.** If the visual section already wrote to `report.md`, append the flow section beneath it. If flow-only run, the combined report is just the flow section under the top-level header.
5. **Update `sessions.json` manifest.** Add each flow's session ID with mode=`flow` and the flow ID. The manifest is the source of truth for which sessions belong to this run.
6. **Respond to user** linking the combined report — not individual per-flow reports unless the user named a single flow.

## Workflow (Combined run)

When both visual and flow verification ran in the same run:

1. **Visual runs first**, writes its section to `report.md` (using the Workflow (Visual) above).
2. **Flow runs next**, appends its section beneath the visual section. Per-flow detail goes to `flow-reports/<flow-name>.report.md`.
3. **Single `sessions.json` manifest** — both visual and flow sessions are recorded together.
4. **Single combined report** at `reports/<run-timestamp>/report.md` covers both modes. The user-facing summary links this combined report.

## Building the Failures Array for Annotation

The screenshot uses **numbered badges**; the report's failure table uses the same numbers as the legend. There are no text labels on the screenshot — keep all rule detail in the markdown table.

From the artifact JSON, each failure has:
- `name` — the rule name
- `selector` — CSS selector
- `constraint` — what was expected
- `total_elements` — how many instances the predicate matched
- `passed_elements` / `failed_elements` — per-instance verdict
- `failures[].actual` — what was found on a failing instance
- `failures[].element` — which element failed (tag + first class)

**Step 1 — assign numbers per category.** For each category's failures, assign 1-indexed rule numbers in the order they'll appear in the report's failure table:

```python
number_to_rule = {}
for i, rule in enumerate(category_failures, start=1):
    number_to_rule[i] = rule  # rule is the full assertion dict
```

Numbers are **within-report identifiers** — they connect each badge in the screenshot to a row in this report's failure table. Numbers are NOT stable across runs (sequential by appearance order). To compare two reports run-over-run, use the rule's `name` column (verbatim from design.md, never changes).

**Step 2 — build annotation input.** The annotation script only needs `selector` and `number`:

```javascript
const failures = [
  {selector: "<selector>", number: 1},
  {selector: "<selector>", number: 2}
];
```

**Step 3 — render the legend table.** The `#` column in the failure table IS the legend. Each row's number matches the badge in the screenshot.

The table's job is to show the **extent** that diverged from the rule's intent: how many instances the predicate matched, how many failed, and which ones. Use these columns:

```markdown
| # | Rule | Selector | Expected | Actual | Match shape | Failing instances |
|---|---|---|---|---|---|---|
| 1 | Canvas Deep \| #0a0e1a \| Page background | `body` | ~rgb(10,14,26) | rgb(15,23,42) | categorical (1 of 1) | BODY |
| 2 | Button radius: 8px | `button[class*=primary]` | >=8px | 0px | partial (47 of 53) | BUTTON.btn-cta, BUTTON.btn-cta-large, BUTTON.btn-cta-mobile, ... (+44 more) |
| 3 | Hero CTA button present | `.hero-cta` | !=none | selector not found | not-found (0 matches) | — |
```

**Match shape** classifies the failure type — the user reads this column to decide what action to take:

| Match shape | When | Meaning | User action |
|---|---|---|---|
| `not-found (0 matches)` | `total_elements == 0` | Predicate matched nothing on the page. | Check selector — rule's predicate may be wrong, or the element isn't on this page/route. |
| `categorical (N of N)` | `failed_elements == total_elements` | Every instance the predicate matched failed. | Either the rule is wrong (intent doesn't match site) or the site is broken (every instance violates intent). |
| `partial (N of M)` | `0 < failed_elements < total_elements` | Some matched instances pass, some fail — heterogeneous extent. | Either fix the failing instances, or split the predicate (these are a separate variant). See `verification.md` step 7. |

**Failing instances** — list the elements that failed, derived from `failures[].element`. Show up to ~5 inline; if more, use `+N more` notation. The annotated screenshot has a red box around each one (all stamped with the same rule number from the `#` column).

When `Match shape` is `partial`, this column is the most useful single piece of the report — it points at the divergent extent, which is what the user has to act on.

## Multi-Page Reports

For specs covering multiple pages:
- Group failures by URL.
- Navigate to each URL, annotate, screenshot.
- Each screenshot is labeled with its page URL in the report.
- Link text in the report is the live URL — user can click to see the exact page.

## Screenshot Naming

```
screenshots/
  visual_style.png                ← failures on the main page
  visual_style_page2.png          ← failures on a second page (if multi-page)
  component_rules.png
  platform_conventions.png
```

Only capture screenshots for categories that have failures. No screenshot = all passed.

## Link Format

Every page URL in the report is a clickable markdown link:
```markdown
**Page:** [https://example.com/app](https://example.com/app)
```

The user can click the link to see the live page where the failure was observed. If the page requires authentication or specific state, note that in the report.

## Flow Section Format

The flow section of the combined report aggregates per-flow results. Detail for each flow lives in its own `flow-reports/<flow-name>.report.md`; the combined report links to them.

```markdown
# Flow Verification

## Run Info

| Field | Value |
|---|---|
| Run | 20260515-143022 |
| Viewport | 1280x800 |
| Total Flow Duration | 32.1s |
| Flows Run | 7 |
| Passed | 5 |
| Failed | 1 |
| Skipped | 1 |

## Results

| Flow | Type | Status | Duration | Report |
|---|---|---|---|---|
| mira-2 | happy_path | ✅ | 4.3s | [mira-2.report.md](./flow-reports/mira-2.report.md) |
| mira-3 | happy_path | ✅ | 6.1s | [mira-3.report.md](./flow-reports/mira-3.report.md) |
| mira-4 | error_path | ❌ | 5.7s | [mira-4.report.md](./flow-reports/mira-4.report.md) |
| mira-20 | state_completeness | ⏭️ | — | [mira-20.report.md](./flow-reports/mira-20.report.md) |

## Audit Findings

**(Include this section ONLY if any flows were skipped.)**

The following flow(s) were skipped before execution:

- **mira-20** — `# user:` declares an auth-gated journey but no credentials were resolved by the runtime. Skipped with reason `blocked: auth required`.

Resolution options for the user:
1. **Provide credentials** — make the role identifier in `# user:` resolvable to the runtime (env var, secrets file, or whatever the runtime uses)
2. **Drop the auth requirement** — remove `# user:` from `mira-20.feature` if the journey doesn't actually need auth
3. **Skip the flow** — leave as-is; mira-20 will continue to skip until credentials resolve

## Warnings

- mira-2: cleanup ran successfully but took 7.2s (slow).
- mira-3: `act_get` returned medium confidence on the "board contains 3 columns" assertion — supplement with `evaluate_js` next time.
```

Status indicators: ✅ passed, ❌ failed, ⏭️ skipped (auth required, missing required metadata, or other configuration issue).

The combined report links to each per-flow report by relative path. The user clicks through to see step-by-step detail.

**Hard rule: The Results table MUST include a `Report` column with a relative markdown link to each per-flow report file.** The link format is `[<flow-name>.report.md](./flow-reports/<flow-name>.report.md)`. Every flow that ran (passed, failed, or skipped) gets a link. Without these links, the combined report is a dead end and the user cannot navigate to step-level detail. This is not optional.

## Per-Flow Report Format

Each flow gets its own `<flow-name>.report.md` under `reports/<run-timestamp>/flow-reports/`:

```markdown
# mira-2 (happy_path) — ✅ PASSED

## Metadata

| Field | Value |
|---|---|
| App URL | https://aws-mira-prod.turing.com |
| Run | 20260515-143022 |
| Session | ghi789-jkl012 |
| Viewport | 1280x800 |
| Duration | 4.3s |
| Source | [flows/mira-2.feature](../../../flows/mira-2.feature) |

## Goal

Create a new "Design" column on the Mira project board and move tickets into it.

## Steps

| # | Type | Step | Status | Duration |
|---|---|---|---|---|
| 1 | Given | I am on the "Mira Project Management" project board | ✅ | 320ms |
| 2 | When | I create a new column named "Design" with color "pink" | ✅ | 1.1s |
| 3 | Then | the board should contain a column named "Design" with pink color | ✅ | 410ms |
| 4 | When | I move the ticket "Login page design" from "ToDo" to "Design" | ✅ | 850ms |
| 5 | And | I move the ticket "Design OTP screen" from "ToDo" to "Design" | ✅ | 760ms |
| 6 | Then | the "Design" column should contain "Login page design" | ✅ | 290ms |
| 7 | And | the "Design" column should contain "Design OTP screen" | ✅ | 270ms |

## Findings

None

## Cleanup

**Status:** passed

Deleted column "Design" from the project board.

## Warnings

None
```

If the flow failed, replace the Findings section with a populated table:

```markdown
## Findings

| Assertion | Confidence | Impact | Details |
|---|---|---|---|
| The "Design" column should contain "Login page design" | high | high | act_get reported the column was empty; evaluate_js confirmed `.column[data-name=Design] [data-testid=ticket]` matched 0 elements |

**Evidence:** Step 4 ran successfully (drag operation completed visually), but the ticket reverted to "ToDo" when the page settled. Network log shows a 500 from POST /api/tickets/move.
```

### Status indicators

| Indicator | Status | Meaning |
|---|---|---|
| ✅ | passed | Step or flow completed as expected |
| ❌ | failed | Step or flow did not complete as expected |
| ⏭️ | skipped | Step skipped (typically because a prior Given failed) or flow skipped (auth missing or required metadata absent) |

### Required sections

Every per-flow report MUST include all of: Metadata, Goal, Steps, Findings, Cleanup, Warnings. Use "None" placeholder when a section is empty (no findings, no warnings). Don't omit sections — the consistent structure makes per-flow reports comparable across runs.

### Confidence and Impact

Every finding gets two scores:

| Score | Levels | Meaning |
|---|---|---|
| Confidence | high / medium / low | high = deterministic check failed (`evaluate_js` confirms); medium = `act_get` pattern match with some ambiguity; low = subjective judgment |
| Impact | high / medium / low | high = missing functionality, broken flow; medium = convention deviation; low = non-critical content deviation |

When `act_get` and `evaluate_js` agree on a failure, mark confidence `high`. When only `act_get` reports the failure, mark `medium` — Nova Act's interpretation may be off.

### Timing

All durations are wall-clock time as the user perceives them.

- **Step duration** — elapsed time from first tool call for that step to resolution.
- **Flow duration** — elapsed time from session open to session close.
- **Total flow duration** — span from first session open to last session close across all flows.

Don't sum individual `time_worked_s` values from tool calls — they overlap when Nova Act runs internal retry loops. Use wall-clock from the agent's perspective.

## Visual Section: When to Generate a Report

- After a full verification run (all categories checked)
- User explicitly asks for a report
- Can be skipped for quick single-category checks where terminal output suffices

The agent should offer: "Verification complete. 4 failures found. Want me to generate an annotated report?"
