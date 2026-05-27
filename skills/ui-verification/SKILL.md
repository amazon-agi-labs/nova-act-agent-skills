---
name: ui-verification
version: 0.1.0
description: Verify whether a live web app matches its design specification using deterministic CSS checks against the DOM, AND verify user flows by executing Gherkin scenarios via Nova Act. Translates design claims into rules and runs them via verify_* MCP tools; executes flows via act() and act_get(). Produces a combined visual + flow report with annotated screenshots and per-flow detail. Use when checking visual style, component rules, accessibility, project conventions, platform patterns, or end-to-end user journeys against a live site.
license: Apache-2.0
compatibility: Requires the `nova-act-mcp` MCP server. Designed for Claude Code and Kiro.
metadata:
  author: Amazon
  displayName: UI Verification
  keywords: browser, verification, css, design, visual, ui, ux, style, accessibility, components, flow, gherkin, mcp
---

# Overview

UI Verification covers two parallel modes against a live web app:

1. **Visual verification** — checks whether the page matches its design specification. Translates design claims into CSS rule checks, runs them against the live DOM via `getComputedStyle()`. Deterministic; the browser's computed styles are the source of truth.
2. **Flow verification** — checks whether user journeys complete correctly. Executes Gherkin scenarios from `.feature` files via Nova Act's `act()` (actions) and `act_get()` (assertions). Non-deterministic; results vary run-to-run with network timing and live UI shifts.

Both modes share the skill, the MCP server, and the browser session. A single run can produce both kinds of output, combined into one report. Or either mode can run alone; the other section is omitted from the combined report.

Each run produces:

1. **Structured artifacts** — per-category JSON for visual; per-flow execution data for flows
2. **Annotated screenshots** — red bounding boxes highlighting visual failures on the page
3. **Verification report** — markdown combining a visual summary, a flow summary (per-flow status table), and links to per-flow detail reports

The verify_* tools are deterministic — no vision model, browser's computed styles are the source of truth. The compile and audit passes for visual are LLM-driven (best-effort), reconciling design intent against the app's actual structure. Flow steps are interpreted by Nova Act each run; flow runs are inherently non-deterministic.

# Reconciliation inputs

**Visual verification.** The 5 compiled category files (`.ui-verification/specs/*.md`) are reconciled from up to three inputs:

| Input | What it provides | Required? |
|---|---|---|
| **`design.md`** | Free-form design intent — tokens, prose, design language, component definitions | Required |
| **The running app** | Live DOM observed via `start_browse` + `verify_*` — real selectors, real computed values | Required for verification (informs selectors and validates rules) |
| **App source code** | Components, theme/tokens, CSS files — implementation truth | Optional. When accessible, makes selectors deterministic and divergence classification more precise |

**Flow verification.** Flows are authored or generated as `.feature` files at `.ui-verification/flows/`:

| Input | What it provides | Required? |
|---|---|---|
| **`.feature` files** | Gherkin scenarios with metadata header (flow ID, type, app URL, optional auth and cleanup) | Required for flow verification |
| **The running app** | Target of the scenarios; Nova Act executes against the live URL | Required |
| **Auth credentials** | Provided when a flow's `# user:` metadata declares a required login | Conditional |

When source code is accessible (the user is a developer working on their own app), the agent should detect it and use it during compile, audit, and spec generation. Source can live at the project root (`package.json` + `src/` at `output_dir`) OR one level deeper (e.g. `output_dir/<package-name>/package.json` — a workspace layout where the verifier opens at the workspace root and one or more app packages live as subdirs). Sniff both. When source is not available (verifying an external site, black-box check), the skill operates in DOM-only mode — selectors are best-effort, audit relies on design.md + DOM only.

The 5 category files grow as the app develops:
- design.md grows via Scribe (user expressing design intent in chat → design.md edits)
- 5 mds grow as the Compiler discovers more verifiable surfaces in the app and source

Both layers can grow, but only via their own author paths. The 5 mds are NEVER edited to record observations or freeze divergent live-site values — see hard rules below.

# Three names — don't conflate them

| Name | What it identifies |
|---|---|
| `ui-verification` | This skill (the agent's playbook) |
| `nova-act-mcp` | The MCP server providing browser + verify_* tools |
| `.ui-verification/` | The artifact directory at the project root (compiled specs, assertion JSON, reports) |

These are unrelated despite words overlapping. The skill does NOT live inside the artifact dir; the artifact dir is at the project root, not inside the skill.

# Capabilities

| Capability | Tool | Source File | What It Checks |
|---|---|---|---|
| Visual Style | `verify_visual_style` | `specs/visual-style.md` | Colors, typography, spacing, radii, shadows |
| Components | `verify_components` | `specs/component-rules.md` | Component presence, variants, props |
| Accessibility | `verify_accessibility` | `specs/accessibility.md` | Aria roles, landmarks, heading hierarchy |
| Project Rules | `verify_project_rules` | `specs/project-rules.md` | Layout structure, spacing system, conventions |
| Platform Conventions | `verify_platform_conventions` | `specs/platform-conventions.md` | Navigation patterns, page structure |
| User Flows | `act` + `act_get` | `flows/<flow-name>.feature` | End-to-end user journeys, functional correctness |

Visual rules can be **route-scoped**: each category file may contain `## Scope: any` (default) and `## Scope: route=<glob>` sections. See `references/spec_authoring.md`. Flow scenarios target the URL declared in their `# app:` metadata; route scoping is per-flow rather than per-rule.

# Available MCP Tools (19 total)

### Session Management
- `start_browse(url, intent, browser_mode)` — open a URL, get a `session_id`. **Use `browser_mode="local"` for verification.**
- `session_close(session_id)` — terminate browser session
- `session_list()` — list active sessions

### Verification — Visual only (all require `session_id` and `rules` JSON; ALWAYS pass `output_dir` = absolute path to project root)
- `verify_visual_style(session_id, rules, output_dir)`
- `verify_components(session_id, rules, output_dir)`
- `verify_accessibility(session_id, rules, output_dir)`
- `verify_project_rules(session_id, rules, output_dir)`
- `verify_platform_conventions(session_id, rules, output_dir)`

These are the visual-mode verification tools. For flow verification, `act()` and `act_get()` (below) are the primary drivers — `verify_*` doesn't apply to Gherkin steps.

If `output_dir` is omitted, the server writes assertions to a `/tmp/` temp dir and downstream report/annotation steps can't find them.

### Browser Interaction (all require `session_id`)
- `navigate(session_id, url)` — go to URL
- `click(session_id, selector)` — click element
- `scroll(session_id, direction, selector?)` — scroll up/down
- `hover(session_id, selector)` — hover element
- `press_key(session_id, key)` — keyboard input
- `type_text(session_id, selector, text, clear_first?)` — type into input

### Content & Capture (all require `session_id`)
- `evaluate_js(session_id, script)` — run JavaScript in page context
- `get_page_content(session_id, format?)` — page as `"text"` or `"html"`
- `screenshot(session_id, destination?)` — capture viewport to file path

### Natural Language (all require `session_id`)
- `act(session_id, prompt)` — instruct browser actions (scroll, click, navigate, fill forms). For **flow verification**, this is the primary driver of `Given` and `When` steps. For **visual verification**, do NOT use `act()` for CSS checks — use `verify_*` instead.
- `act_get(session_id, prompt, schema?)` — structured data extraction or state verification. For **flow verification**, this is the primary driver of `Then` and `And` (after `Then`) assertions; supplement with `evaluate_js` for deterministic checks. For **visual verification**, do NOT use `act_get()` for CSS checks — perception/reasoning over the page is the agent's job using `screenshot` + `get_page_content`, and CSS verdicts come from `verify_*`.

# Artifact Structure

```
<project_root>/
  visual/design.md                   ← visual source spec (or .ui-verification/design.md)
  .ui-verification/
    .integrity.json                  ← compile-state ledger (visual only — see spec_sync.md)
    specs/                           ← compiled visual category files (INPUT to verify_*)
      visual-style.md                  (clean markdown — integrity tracked in .integrity.json)
      component-rules.md
      accessibility.md
      project-rules.md
      platform-conventions.md
    flows/                           ← flow .feature files (INPUT to act() / act_get())
      <flow-name>.feature
    sessions/                        ← per-session output (MCP-owned)
      <session_id>/
        <category>_assertions.json    (visual assertion JSON, write-once)
    reports/                         ← per-run output (skill-owned)
      <YYYYMMDD-HHmmssZ>/            ← UTC run-timestamp (a run can span multiple sessions)
        report.md                    ← combined visual + flow summary
        screenshots/                 ← visual annotated failures
        flow-reports/                ← per-flow reports
          <flow-name>.report.md
        sessions.json                ← manifest of session IDs in this run
```

# Hard rules every run obeys

## Default mode is "both" unless user narrows scope

When the user says "verify [url]", "run verification on [url]", or any unqualified verification request, the run MUST include BOTH visual and flow verification. Do NOT default to visual-only. Only narrow to one mode when the user explicitly requests it ("check styles only", "run flows only") or when the disambiguation table clearly matches a single-mode pattern.

If no `.feature` files exist, generate them (see `references/flow_generation.md`). If no `design.md` exists, generate it (see `references/spec_generation.md`). Missing artifacts trigger generation, not scope narrowing.

## Audit when the integrity ledger triggers

Before calling any `verify_*` tool, check the integrity ledger (see § "The integrity ledger covers the clean case" below for the trigger conditions). When the audit runs, reconcile each in-scope rule against the inputs (design.md, app source if accessible, running app DOM). This is a best-effort LLM check — not a substring match — because the Compiler is itself LLM-driven and rules can legitimately encode information that isn't a literal substring of design.md.

For each rule (`{Name, Selector, Property, Constraint, Scope}`), answer three questions:

1. **Intent traceable** — does the rule's claim (what's being asserted: a token value, a property/value pair, an element's presence) correspond to something stated or implied by design.md, OR a component definition / theme token in source code, OR an idiom present in the running app?
2. **Constraint reconciles** — does the constraint value match what design.md assigns to this element/property combination, OR what source code's theme/token files assign, OR what the running app's component renders at rest? Constraints lifted from the live site WITHOUT a design.md or source backing are contamination.
3. **Selector plausible** — does the selector target the element that design.md (or source) describes? Selectors can come from the app (more specific than design.md alone could specify), but the *target* must match the described element.

Classify each rule as:

- **PASS** — all three questions reconcile against at least one input
- **ORPHAN** — the rule's claim has no source. design.md doesn't make this assertion; source doesn't define this assignment; the only "evidence" is what the live site happens to render. This is the contamination case.
- **DIVERGENT** — the claim IS in design.md (token defined, component referenced) but the rule's constraint contradicts design.md's assignment. E.g. design.md says component X uses token Y, but the rule asserts component X has the value of token Z.

**Skip ORPHAN and DIVERGENT rules in the current run; surface them in the report's Audit Findings section** (see `references/verification_report.md`). Verifying them would either pass (silently confirming contamination) or fail (without the right reason). Continue verifying the PASS rules. The user resolves contamination on their own time with three options: drop the rule, upstream the claim into design.md and recompile, or recompile from scratch.

**When to write the integrity ledger.** Single rule: write it when the category files on disk equal what the Compiler would emit from the current `design.md` right now.

- **Compile finished cleanly, no skipped rules** → write.
- **Selector repair or constraint syntax fix completed** → write (those repairs ARE what the Compiler would emit now that the original was known to fail).
- **Audit skipped any rules (ORPHAN/DIVERGENT)** → don't write. Those rules are still in the file but they're NOT what a fresh compile would emit. Leave the ledger missing/stale so the next run re-audits.
- **Verify-only run, files unchanged** → no-op; don't touch the existing ledger.

The origin of selectors (DOM observation in heuristic mode, source code in source-aware mode) does NOT determine ledger eligibility. As long as rules' claims and constraints trace to design.md (the audit verifies this), the ledger reflects a valid Compiler-approved state. See `references/spec_sync.md` Compilation step 7 for the full case table.

**The integrity ledger (`.integrity.json`) covers the clean case.** If the ledger says all hashes match — `design.md` and every category file — the file state is provably what the Compiler last wrote, no audit needed. See `references/spec_sync.md` § Integrity Ledger.

Audit runs when:
- Any category file's hash mismatches the ledger (file edited outside Compiler — prior buggy run, hand-edit, partial-write)
- Ledger is missing (no integrity baseline, run conservatively)
- User explicitly requests re-audit (manual correctness check; hashes can be stale even when valid if a Compiler bug wrote bad rules and updated its own hash)

Skip-audit when hashes match is a real efficiency improvement for repeat runs. But periodic manual re-audit ("re-audit visual-style") is recommended after any large compile or after suspicious changes.

**Audit cost.** This is one LLM reasoning pass per scoped category file (or per rule batch — agent's choice). Not free, but bounded: proportional to the rules being verified, no MCP calls. The same kind of reasoning the Compiler used to write the rules; the audit just checks "would I write this rule if I compiled fresh now?"

## Assertion JSON is immutable

Files at `<output_dir>/.ui-verification/sessions/<session_id>/*_assertions.json` are write-once OUTPUT of `verify_*`. **NEVER edit them.** No exceptions.

The JSON records what `verify_*` saw against the live DOM. Don't rewrite values, change pass/fail, add scope, "annotate" findings, or add commentary. If a field seems missing (e.g. scope), the report layer joins it in from the source it came from (e.g. the category file) — assertion JSON itself stays exactly as the MCP server wrote it.

If you find yourself opening assertion JSON to fix something, stop — that's the report's job. The agent reads the JSON; the JSON does not change after `verify_*` writes it.

## The 5 category files are reflections of design.md

The 5 compiled `.ui-verification/specs/*.md` files are derived from `design.md`. They are NOT a scratch pad, working memory, or place to record observations.

**Verification mode (design.md exists):**

Edit a category file ONLY when:
- `design.md` changed (or chat became a design.md edit) → recompile the affected rules
- Selector repair: an existing rule's selector returned "selector not found" and you found a working replacement (selector update only — name/property/constraint stay)

Do NOT edit category files to:
- Capture an observation about the live site (that's the report's job)
- Add a rule that "documents a divergence" with a constraint that matches the divergent live-site value (this silently encodes site bugs as truth and prevents future detection)
- Make a failing rule pass by relaxing the constraint
- Record findings, notes, or context

For partial / scoped verification, **pick existing rules from the right category files** — don't author new ones unless they're traceable back to a design.md claim that was missed during the prior compile (which is a Compiler bug to surface, not a routine action).

**Generation mode (cold-compile from a live site, no `design.md` yet):**

The above rule is RELAXED during generation, because the 5 mds are being seeded for the first time. Generation observes the running app and writes both `design.md` and the 5 mds in one pass. The constraints in the 5 mds at end-of-generation match the observed DOM values — that is the reverse-engineering contract, not contamination.

The "no recording observations" guard kicks in **after generation completes** and the user has reviewed `design.md`. From that point forward, the verification-mode rules above apply: edits go through `design.md` + recompile, never directly to the 5 mds.

See `references/spec_generation.md` § Phase 5 for the generation-mode rules. Source code, when accessible during generation, informs **names** (token names, component names) but NOT **values** — the DOM is authoritative for values. There is no "source vs DOM divergence" during generation: the DOM is the cascade-resolved outcome of all source CSS, and any apparent disagreement is between one source file the agent read and the same source compiled by the browser.

## Each run is independent

Do NOT read prior assertion JSON or `report.md` from earlier `sessions/<session_id>/` or `reports/<run-timestamp>/` directories. The only state carried across runs is the compiled `specs/*.md` files plus the `.integrity.json` ledger (re-compile is skipped if all ledger hashes match current files). Prior assertions and reports are historical artifacts; they don't inform the current run.

If you find yourself reading a prior session's assertions to "compare," stop — that's cross-session warm-start, which is deferred. Run fresh, write a fresh report.

## Flow files at `flows/` are the only flow input

The `.feature` files at `<output_dir>/.ui-verification/flows/` are the only input to flow verification. Never compose flows ad-hoc from chat input mid-run; never modify `.feature` files mid-run. If the user wants to change a scenario, the change goes through the Scribe (see `references/flow_sync.md`) before the next run.

## Flow runs are non-deterministic

Do NOT carry forward prior flow session results across runs. Nova Act re-interprets steps each run, network timing varies, the live UI shifts. Carrying forward "passed" verdicts would mask real flakiness or environmental drift. Every flow runs every time. Flow-side regressions surface via the per-flow status table in the combined report, not a warm-start mechanism.

## Every run produces a report

This rule has no exceptions. Whether the user asks to verify a whole site or a single line of `design.md`, the run isn't done until:

1. **Rules persist on disk** — every rule passed to verify_* at *verification time* (step 6) must already exist in a category file under the right `## Scope:` section. (Compile-time selector validation is a separate use of verify_*; see verification.md step 4.)
2. **Scope is joined at report-time, not stamped onto assertions** — the report reads BOTH the assertion JSON (for verdicts) and the category file (for scope) and joins them on rule name. Assertion JSON stays exactly as the MCP server wrote it. See `references/verification_report.md` for the join.
3. **A report is written** — `<output_dir>/.ui-verification/reports/<run-timestamp>/report.md`, with the failure table and any annotated screenshots. See `references/verification_report.md` for format. Even an all-pass run produces a report.
4. **The user-facing summary links the report**, not the assertion JSON. The JSON is intermediate output; the report is the deliverable.

A "quick check" of one or two claims is still a verification run. The same four rules apply.

# Workflow

For visual verification tasks, load `references/verification.md`. For flow verification tasks, load `references/flow_verification.md`. Both reference docs have a complete decision flow for their mode.

| User intent | Reference |
|---|---|
| Verify a live site against a design spec (visual) | `references/verification.md` |
| Run user flows against a live site | `references/flow_verification.md` |
| Generate spec from live site (no design.md exists) | `references/spec_generation.md` |
| Generate flows from a live site (no .feature files exist) | `references/flow_generation.md` |
| Compile design.md → category files; sync chat edits | `references/spec_sync.md` |
| Sync user intent → `.feature` files | `references/flow_sync.md` |
| Set up MCP server + browser session | `references/setup.md` |
| Write/edit design spec files | `references/spec_authoring.md` |
| Write `.feature` files | `references/flow_authoring.md` |
| Generate verification report (visual + flow) | `references/verification_report.md` |
| Annotate failures visually on the page | `references/annotate_failures.md` |
| Constraint syntax reference | `references/constraint_reference.md` |
| Per-category translation patterns | `references/verify_visual_style.md`, `references/verify_components.md`, `references/verify_accessibility.md`, `references/verify_project_rules.md`, `references/verify_platform_conventions.md` |
| Cross-session warm-start (deferred — not in scope) | `references/warm_start.md` |

All references live at `./references/<name>.md` relative to this SKILL.md file. The absolute path depends on where the skill is installed:

- **Global install:** `~/.<agent>/skills/ui-verification/references/<name>.md`
- **Workspace install:** `<project_root>/.<agent>/skills/ui-verification/references/<name>.md`

To resolve references, use the directory containing this SKILL.md as the base — NOT the workspace root. If your skill loader's progressive disclosure hasn't surfaced them mid-session, read them directly with the Read tool using the appropriate absolute path — never search the filesystem with `find`.

## Disambiguation: visual vs flow vs both

Match the user's request to the right mode:

| Phrase pattern | Mode | Action |
|---|---|---|
| "verify design", "check styles", "match the spec", "is it on-brand" | Visual only | Load `references/verification.md` |
| "run flows", "test the user journey", "verify login works" | Flow only | Load `references/flow_verification.md` |
| "verify [url]", "run verification on [url]" with no further qualifier | Both | Visual first, then flow, into one combined report |
| User names a specific `.feature` file or flow ID | Flow only | Load `references/flow_verification.md` and run only that flow |
| User selects text from `design.md` or names a category | Visual only | Load `references/verification.md` and use partial-selection flow |

When in doubt, ask the user once: "Run visual verification, flow verification, or both?" Don't guess at scope when the request is genuinely ambiguous.

## Where this skill lives

This skill is at `<output_dir>/.<agent>/skills/ui-verification/` for workspace-local installs, OR at `~/.<agent>/skills/ui-verification/` for global installs — wherever the skill loader picked it up from is its installed location. **Do NOT search the filesystem for it.** No `find ~/.<agent>`, no `find /`. Activation is the runtime's job; if you've reached this SKILL.md, the runtime already knows where you are.

### Resolving the references directory

The `references/` folder is **always co-located with this SKILL.md file**, not with the workspace or output directory. Use the path that the runtime used to load this file as the base:

| Install type | SKILL.md location | References at |
|---|---|---|
| **Global** | `~/.<agent>/skills/ui-verification/SKILL.md` | `~/.<agent>/skills/ui-verification/references/` |
| **Workspace** | `<project>/.<agent>/skills/ui-verification/SKILL.md` | `<project>/.<agent>/skills/ui-verification/references/` |

When reading a reference, construct the absolute path from the skill's install location. Example for a global install:
```
~/.<agent>/skills/ui-verification/references/verification.md
~/.<agent>/skills/ui-verification/references/spec_sync.md
```

Do NOT assume references are at `<output_dir>/.<agent>/skills/ui-verification/references/` when the skill was loaded from the global location — the workspace may not have a copy.

If you're a fresh agent on a new turn and you don't immediately have a tool from `nova-act-mcp` available, the MCP server may still be starting — wait for the runtime to surface it on the next user turn rather than searching the filesystem to "find" the skill yourself. The skill is already loaded; the tools are not always synchronously available with skill activation.

## Don't search for tool implementations

Never `find` for the MCP server source code, the constraint engine source, or any other tool implementation. The behavior of `verify_*`, the constraint syntax, the selector matching algorithm — all of this is documented in `references/constraint_reference.md` and the per-category deep-dives. If a constraint or property behaves unexpectedly during a run, **read the reference, not the implementation.** The references are the agent-facing documentation of record; reaching for `find` to spelunk the engine is a sign the reference needs an update, which the user can address — but in-session, work from documented behavior.
