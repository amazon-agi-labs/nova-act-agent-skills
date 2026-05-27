# Spec Sync

Keeps the visual design expected-state layer consistent. The agent acts as scribe, compiler, and auditor across three surfaces: user input (chat or design.md edits), category files (the verification input), and live site results.

## Artifact Hierarchy

```
<project_root>/
  visual/design.md                   ← intentional layer (human-authored, REQUIRED)
                                       (or .ui-verification/design.md — see verification.md step 1)
  .ui-verification/
    .integrity.json                  ← compile-state ledger (hashes for design.md + each category file)
    specs/                           ← compiled rule layer (INPUT to verify_*)
      visual-style.md                  (clean markdown — no frontmatter; integrity tracked in .integrity.json)
      component-rules.md
      accessibility.md
      project-rules.md
      platform-conventions.md
    sessions/                        ← results layer (MCP output)
      <session_id>/
        visual_style_assertions.json     (read at report-time only; never re-input)
        component_rules_assertions.json
        accessibility_assertions.json
        project_rules_assertions.json
        platform_conventions_assertions.json
    reports/<run-timestamp>/         ← human-readable reports (skill-owned, UTC YYYYMMDD-HHmmssZ)
      report.md
      screenshots/<category>.png
      sessions.json                  ← manifest of session IDs in this run
```

## Integrity Ledger (`.integrity.json`)

The Compiler maintains an integrity ledger at `<output_dir>/.ui-verification/.integrity.json` that records the state at the last successful compile pass. Every run's first action is to compare current files against this ledger to decide cold compile / re-compile / skip / audit.

**Schema:**

```json
{
  "design_md": {
    "path": "visual/design.md",
    "hash": "<sha256 of design.md at compile time>",
    "compiled_at": "<ISO timestamp of last compile pass>"
  },
  "category_files": {
    "visual-style.md":          "<sha256 of file>",
    "component-rules.md":       "<sha256 of file>",
    "accessibility.md":         "<sha256 of file>",
    "project-rules.md":         "<sha256 of file>",
    "platform-conventions.md":  "<sha256 of file>"
  }
}
```

**What the ledger does NOT track:**

- **Source code hashes.** Source is consulted *during* compile and audit (see § Source-aware selector derivation), never tracked between runs. Source files churn faster than design intent; tracking them would force spurious recompiles. The verification source of truth is the running app, not source code.
- **Per-rule hashes.** The category file hash covers the whole file. Per-rule integrity is unnecessary — a corrupted rule changes the file hash, which triggers audit (which reasons rule-by-rule).
- **Assertion JSON / reports.** Those are per-session output, not compile state.

**Decision matrix on run-start:**

| Ledger state vs current | Action |
|---|---|
| `.integrity.json` doesn't exist | Cold compile, then write ledger |
| design.md hash mismatches ledger | design.md changed → recompile affected scopes → update ledger |
| Any category file hash mismatches ledger | File was edited outside Compiler → audit runs (LLM reconciliation) → on resolution, update ledger |
| All hashes match ledger | Verified state. Skip audit. Proceed to verify_*. |

**Canonical write recipe.** The agent runs this as a single Bash invocation when finalizing a run that should write the ledger:

```bash
cd <output_dir>

# 1. Compute current hashes
DESIGN_HASH=$(shasum -a 256 visual/design.md | awk '{print $1}')
VS_HASH=$(shasum -a 256 .ui-verification/specs/visual-style.md | awk '{print $1}')
CR_HASH=$(shasum -a 256 .ui-verification/specs/component-rules.md | awk '{print $1}')
A_HASH=$(shasum -a 256 .ui-verification/specs/accessibility.md | awk '{print $1}')
PR_HASH=$(shasum -a 256 .ui-verification/specs/project-rules.md | awk '{print $1}')
PC_HASH=$(shasum -a 256 .ui-verification/specs/platform-conventions.md | awk '{print $1}')
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# 2. Write to a temp file (NOT the real path)
cat > .ui-verification/.integrity.json.tmp <<EOF
{
  "design_md": {
    "path": "visual/design.md",
    "hash": "$DESIGN_HASH",
    "compiled_at": "$NOW"
  },
  "category_files": {
    "visual-style.md":          "$VS_HASH",
    "component-rules.md":       "$CR_HASH",
    "accessibility.md":         "$A_HASH",
    "project-rules.md":         "$PR_HASH",
    "platform-conventions.md":  "$PC_HASH"
  }
}
EOF

# 3. Atomic rename — must be last
mv .ui-verification/.integrity.json.tmp .ui-verification/.integrity.json
```

`mv` is atomic on POSIX. Crash mid-write leaves the previous valid ledger in place — next run sees the older state, falls back to audit, self-heals.

If `design.md` lives elsewhere (e.g. `.ui-verification/design.md` instead of `visual/design.md`), substitute its actual path in both the `shasum` call and the `path` field. Always reflect the actual on-disk location.

**Concurrency.** The skill is single-run-at-a-time per `output_dir`. Two verifications against the same project simultaneously will race on the ledger; whichever finishes last wins. Subsequent runs' audits detect any inconsistencies. For parallel verifications, use different `output_dir`s. Mid-run edits to design.md are out of scope — the agent captures design.md's hash at step 1 and works against that snapshot.

## design.md is required — no exceptions

**Every flow that writes to category files MUST go through design.md first.** It is the intentional layer the user reads and edits — prose, tokens, predicates expressed in design language. Category files are the *first place rules become machine-checkable*; depending on how selectors are written, individual rules can be intentional (`button` → all buttons) or effectively extensional (`header [role=search] button[aria-label=Search]` → one specific instance). Either way, they should not be the *first place* design intent lives. Bypassing design.md to write rules directly is forbidden because:

- The user loses the readable artifact they edit by hand (design.md is prose; category files are rule tables).
- Future re-compilation has nothing to compile *from* if intent changes.
- Rules become orphaned observations with no documented "why" — "what was intended?" has no canonical answer when contradictions arise.

(Layer model: **design.md** = intentional. **5 category files** = compiled rules, mixed intentional/extensional based on selector specificity. **assertions.json + report** = extensional projection — every matched element, per-rule pass/fail.)

### Bootstrap: no design.md yet

When you would otherwise write a category-file rule and design.md doesn't exist:

1. **Tell the user the gate.** "design.md is where visual intent lives. The verifier compiles category files from it; without one, rules become orphaned observations with no documented intent. I'll create design.md before continuing."
2. **Propose a location.** Default: `<project_root>/visual/design.md` (or `<project_root>/.ui-verification/design.md` for projects that prefer to keep all verifier artifacts under the dot-directory).
3. **Confirm with the user.** "Create design.md at `<default>`? Or give me a different path."
4. **If user accepts a path** → create the file, seed it with the intent they just expressed in chat, then proceed with normal flow (Scribe updates design.md → Compiler re-emits category files).
5. **If user opts out** ("don't create design.md, just check this thing") → **short-circuit out of the verifier**. Do NOT write category-file rules. Tell the user: "Without design.md, I can't track this through the verifier. I can still answer your styling question as a plain coding/inspection task — but no rule will be persisted, no verify_* run, no report. Want me to do that instead?"

The short-circuit path is genuinely outside this skill. The agent answers as a coding/inspection assistant, not as a verifier. Nothing lands in `.ui-verification/`.

## Routing: which role handles which input

User input comes from chat or design.md edits. Routing into the right role:

| User input | First role | Then |
|---|---|---|
| Chats design intent, design.md exists | Scribe — propose edit to design.md, confirm, write | Compiler — "design.md changed" trigger re-emits affected category files |
| Chats design intent, no design.md | Bootstrap (above) — create design.md or short-circuit | Scribe → Compiler if design.md gets created |
| Edits design.md directly | (no Scribe — user did the write) | Compiler — "design.md changed" trigger re-emits affected category files |
| Says "verify URL", no design.md | Bootstrap → spec_generation.md (cold start, observed) | Compiler runs as part of generation; specs land at `.ui-verification/specs/` |
| Says "verify" with design.md present | (no compile-source change) | Verification flow at `verification.md` step 4 (warm or cold compile depending on category files state) |

In every row, the input lands in `design.md` first (or is rejected via short-circuit). Category files are never the *first* place rules appear.

## Roles

### Scribe

Captures user intent into the intentional layer (design.md), never directly into category files. Category files are downstream — they may be intentional (broad selectors) or effectively extensional (narrow selectors targeting specific instances), but either way they're written by the Compiler from design.md, not by the Scribe from chat.

**Trigger:** User expresses design intent in chat ("header should be blue," "increase button radius to 12px," "use Inter for headings").

**Behavior:**
1. **If design.md exists** → propose the edit to design.md, confirm with user, write it.
2. **If no design.md** → run the Bootstrap flow (see top of this file). Do NOT write rules to category files first. Either design.md gets created, or the agent short-circuits to plain coding-assistant mode with no verifier persistence.
3. After design.md is updated, the Compiler runs (via the "design.md changed" trigger below) and re-emits the affected category files.

### Compiler

Translates design.md into the 5 structured category files that verify_* tools consume.

**Trigger:** Any of:
- **design.md changed** — detected either by user edit / Scribe role, or by `design.md` hash mismatch against the integrity ledger (re-compile skipping in `verification.md` step 4). Both paths converge here.
- **No category files yet** — cold start.
- **Partial-spec selection with gaps** — user selected text from design.md that has no matching rule.
- **Selector repair** — verify_* returned "selector not found" (verification.md step 7a) and the agent is fixing the rule.
- **Scope move** — user moved a rule between `## Scope:` sections.

It does NOT run on every verification. Once selectors are derived and validated, subsequent runs read category files directly → filter by URL scope → call verify_* → done.

**Inputs:** the Compiler reconciles up to three sources to produce category files. See `SKILL.md` § Three reconciliation inputs for the full model. Quick recap:

- **`design.md`** (required) — YAML frontmatter with tokens, token references, prose describing components, value tables
- **App source code** (optional, when accessible) — theme/token files, component definitions, global CSS. When present, ground selectors and constraints in source rather than guessing.
- **Running app** (required during compile) — DOM observed via the open browser session. Validates that derived selectors resolve.

When source is available, the Compiler should detect it and read the relevant files before deriving selectors. **Detection:** look for `package.json` + `src/` at `output_dir` (project root layout) OR one level deeper (e.g. `output_dir/<package-name>/package.json` — workspace layout where the verifier opens at the workspace root and one or more app packages live as subdirs). Look for theme/token files in the detected source root: `theme.ts`, `tokens.json`, `tailwind.config.js`, `Config/` etc. If multiple candidates exist, prefer the one whose name or `dev`/`start` script matches the URL being verified. If neither default location yields source, ask the user once: "Where is the source root for the app at `<URL>`? (relative path from `<output_dir>`, or `none` to compile in DOM-only mode)". Do NOT search the filesystem broadly. When source is not available, the Compiler operates in DOM-only mode.

**Output:** 5 category .md files (clean markdown — no frontmatter) with one or more `## Scope:` sections containing structured tables, AND one update to `<output_dir>/.ui-verification/.integrity.json` recording the new hashes.

Example `component-rules.md`:

```markdown
# Component Rules

## Scope: any

| Name | Selector | Property | Constraint |
|---|---|---|---|
| button-primary: backgroundColor is #06b6d4 | button[data-variant="primary"], .btn-primary | background-color | ~rgb(6,182,212) |
| button-primary: border-radius rounded.base | button[data-variant="primary"], .btn-primary | border-radius | >=8px |
```

The corresponding `.integrity.json` after this compile records `design.md`'s hash and `component-rules.md`'s body hash. See § Integrity Ledger above for schema and decision matrix.

A category file with route-scoped rules adds additional `## Scope: route=<glob>` sections — see § Category File Format below.

**Compilation steps:**

1. **Resolve tokens.** Expand `{colors.primary}` → `#06b6d4` → `~rgb(6,182,212)`. If source code is accessible, also resolve via the source theme file — confirms the token import path matches design.md's value (and surfaces drift between design.md and the implemented theme).
2. **Classify claims.** Each resolved claim maps to one category (use the classification table in verification.md § Category Mapping).
3. **Determine scope.** Read each design.md section's heading to detect route-specific intent. A section named `## Landing page`, `## App`, or `## /admin` typically corresponds to a route scope; a section named `## Color Palette` or `## Typography` is global (`any`). When in doubt, default to `any`. See § Scope Detection below.
4. **Derive selectors.** Translate each claim's description into a CSS selector (see § Selector Derivation and § Source-aware selector derivation below). When source is accessible, ground selectors in source-defined component classes/attributes rather than guessing — far more deterministic.
5. **Validate via verify_*.** Navigate to a representative URL for the rule's scope (or stay on the current page for `any`-scoped rules), then call the appropriate verify_* tool to confirm selectors resolve. **This is the one verify_* call that happens before category files are written** — it's a compile-time selector-resolution check, not a verification run. The "category files are the ONLY input to verify_*" rule (verification.md step 4) applies to verification runs (step 6); compilation legitimately uses verify_* for its own validation.
6. **Write category files.** Each rule lands under its `## Scope:` section in the category file. One structured table per scope section. A category file with no route-specific rules has a single `## Scope: any` section (or no section heading at all — equivalent). No frontmatter — clean markdown only.
7. **Update the integrity ledger — when the files match what a fresh compile would emit.** See § Integrity Ledger above for the schema and the canonical write recipe.

   **The single rule:** write the ledger when the category files on disk equal what the Compiler would emit from the current `design.md` right now. That's the test for whether skip-recompile next run will be telling the truth.

   Applied to common cases:

   | Situation | Files match a fresh compile? | Write ledger? |
   |---|---|---|
   | Compile completed cleanly, no skipped rules | Yes | **Write** |
   | Selector repair completed (verify_* found "not found", agent updated the selector) | Yes — the new selector is what the Compiler would emit now that the original is known to fail | **Write** |
   | Constraint syntax fix (`==` → `=`, property typo) | Yes — the value was right, only typo fixed | **Write** |
   | Audit found ORPHAN or DIVERGENT rules; agent skipped them; rules still on disk | No — those rules are still in the file but they're NOT what a fresh compile would emit | **Don't write.** Forces next run to re-audit and re-surface the contamination. |
   | Verify-only run (hashes already matched at run-start, no compile happened) | Files unchanged | **No-op** — the existing ledger is still correct, don't touch it |
   | Compile partially failed (some rules unresolved) | No — partial state | **Don't write** — resolve failures first |

   What's NOT a reason to skip the write: the *origin* of selectors. Selectors come from observing the DOM during compile (heuristic mode) or from source code (source-aware mode); either way they're what the Compiler would emit. As long as the rules' *claims* and *constraints* trace to design.md (which the audit verifies), the ledger reflects a valid Compiler-approved state.

   **Permitted in-flight category-file edits during a run:**

   The Compiler may edit a category file mid-run in two narrow cases. Both update the file's hash in the ledger when the run finalizes (assuming all other write conditions are met).

   | Edit | When | What changes | What never changes |
   |---|---|---|---|
   | **Selector repair** | `verify_*` returned "selector not found" for a rule (verification.md step 7a) | The rule's `Selector` column | `Name`, `Property`, `Constraint` |
   | **Constraint syntax fix** | The constraint engine rejected the rule due to a syntax typo (e.g. `==48px` → `=48px` (doubled operator), `~rgba(10,14,26,1)` → `~rgb(10,14,26)` (the rgba trap — see `constraint_reference.md`), `backgroundColor` → `background-color` (camelCase property name)) | The `Property` or `Constraint` column's *syntax* — the operator, the format, the property casing | The constraint's *intended value*. `=48px` keeps `48px`; never becomes `=64px` to match the live site. |

   Constraint *value* changes are spec rewrite — forbidden, regardless of how the value was discovered (live site, source code, or guess). Use the user-resolution paths instead (drop the rule, upstream a new claim into design.md, recompile).

#### Source-aware selector derivation (when source is accessible)

When the Compiler has access to app source code, selectors come from the implementation rather than being guessed-then-validated. This shifts compilation from heuristic to deterministic for the cases source covers.

What source provides for selector derivation:

| Source artifact | What it tells the Compiler |
|---|---|
| Component file (e.g. `Button.tsx`, `SearchOrb.vue`) | The actual class/data-attribute the component renders. Use it directly as the selector. |
| Theme/token file (`theme.ts`, `tokens.json`, `tailwind.config.js`) | Token-to-value mapping. Confirms (or contradicts) design.md's token values. |
| Global CSS / utility classes | Class patterns the component uses. Use as fallback selector when component file isn't directly source-attributable. |
| Route definitions (`App.tsx`, `pages/`, `app/` for Next.js) | Real route paths — informs scope detection and `route=<glob>` patterns. |
| Storybook stories or component variants | Variant prop values — informs `## Scope:` and component-rules categorization. |

The agent reads selectively. Don't load the entire src tree; read theme/token files first (they're small and high-signal), then component files for components named in design.md. Don't try to grep through all source — let design.md's named components drive which files to open.

When source contradicts design.md (e.g. design.md says `colors.primary: #1a73e8` but `theme.ts` exports `--brand-blue: #4285F4`), surface the contradiction to the user as a sync violation. This is a different kind of drift than verification-time drift: it's spec-vs-implementation, and probably wants the user's attention before the live site is even checked.

When source is NOT accessible (no `package.json`, or external-site verification), fall back to the heuristic § Selector Derivation algorithm below — design.md's claim text guides the selector, verify_* validates against the DOM.

**Important:** Compilation requires a live browser session (for the *Validate via verify_** sub-step above). The decision flow in `verification.md` opens the session at step 3 before compilation at step 4 — if you arrived here via a different path and have no session, open one with `start_browse(url=<target>, browser_mode="local")` before running compilation.

**Browser-loss STOP rule.** If the session disconnects mid-compile or `verify_*` calls start failing with connection/MCP errors, STOP. Do NOT edit category files based on guesses. Try ONE reconnect via `start_browse` with the same URL; if reconnect fails, save the partial state, report to the user "M rules compiled, N rules unvalidated due to browser disconnect — rerun when MCP is healthy", and exit. Same rule applies in spec generation — see `references/spec_generation.md` § Browser-loss STOP rule.

#### Scope Detection

When compiling design.md, infer scope from prose structure:

| design.md hint | Inferred scope |
|---|---|
| Heading like `## Landing page`, `## Home`, `## /` (with no subroute hint) | `route=/` |
| Heading like `## App`, `## Application` describing the post-login experience | `route=/app/*` |
| Heading naming a specific route — `## Admin dashboard`, `## /posts` | `route=/admin/*`, `route=/posts/**` |
| Heading describing a UI surface that overlays any page — `## Modals`, `## Drawer`, `## Tooltips` | `any` (rules use `[role=dialog]`-style selectors that simply don't match when the surface isn't open) |
| Heading describing a system aspect — `## Color Palette`, `## Typography`, `## Spacing system` | `any` |
| No section structure (flat prose) | `any` |

If the heading is ambiguous, ask the user: "I see a `## <heading>` section — should rules from this section apply on every page (`any`), or only on a specific route?" Don't guess silently.

When the user later clarifies that an `any`-scoped rule should be route-specific (or vice versa), the Compiler moves the rule between scope sections in the category file. Rule identity (Name field) stays the same.

#### Partial Compilation (Subset of Source Spec)

When the user selects part of a source spec (IDE highlight, pasted excerpt, or "verify the typography section"), the Compiler runs on just that subset:

1. **Scope the input.** The input is the selected text, not the full source spec. Token resolution still uses the full spec's frontmatter.
2. **Extract claims from selection.** Each line or group that asserts a testable CSS property becomes one claim. Skip non-testable prose.
3. **Check existing category files.** For each claim, look for a semantically equivalent rule (same element + property + expected value). If found → skip derivation.
4. **Compile only the gaps.** For claims with no matching rule: resolve tokens → classify → derive selector → validate → write to category file.
5. **Return the rule set.** Existing matches + newly compiled rules. Only these are verified.

### Selector Derivation

Translate the spec claim text into a CSS selector. The claim's description tells you what element it's about — use general web knowledge to write the selector. The verify_* tool validates the result.

**Algorithm:**

1. **Read the claim.** The Name field describes the element: "search button in header," "footer column headings," "card photo corners," "page background." This text is the selector source.

2. **Translate description to selector.** Use the claim's element/component description and general knowledge of web structure:

   | Claim describes... | Selector pattern |
   |---|---|
   | Page-level property | `body` |
   | Landmark | `header`, `main`, `footer`, `nav` |
   | Role-based element | `[role=search]`, `[role=tab]`, `[role=tablist]` |
   | Element within a landmark | `header button`, `footer h3`, `main h2` |
   | Active/selected state | `[aria-selected=true]`, `[aria-current=page]` |
   | Component by function | `button`, `a`, `img`, `input` |
   | Component by variant | `button[class*=primary]`, `[class*=card]` |
   | Inline icons (heart, star, arrow, etc.) | `[class*=icon]`, `svg` scoped, or pattern-class matches |
   | Multiple variants | `main h2` vs `footer h2` (scoped to avoid collision) |

3. **Choose stable selectors.** Prefer selectors that survive redesigns. General preference (not exhaustive):
   - Semantic HTML + ARIA first: `header`, `[role=search]`, `button[type=submit]`, `[aria-label="Search"]`
   - Data attributes when available: `[data-testid="cta"]`, `[data-variant="primary"]`
   - Meaningful classes scoped to landmarks: `header .search-btn`, `footer .nav-links`
   - Structural paths from landmarks as fallback: `header > div > form > button:last-of-type`

   **Scope to a semantic ancestor** when the element lacks unique attributes. Use the nearest landmark (`header`, `main`, `footer`, `nav`, `[role=...]`) as the scoping root.

   Additional rules:
   - **Use comma-separated alternatives** when multiple patterns could match: `header img, header svg, header [class*=logo]`.
   - **Never use:** generated hash classes (`css-1a2b3c`, `sc-bdfBwQ`), bare `*`, or bare tags that match hundreds of elements.
   - Any valid CSS selector that reliably targets the intended element is acceptable — the above are examples, not constraints.

4. **Validate via verify_*, then write.** Call the appropriate verify_* tool with the rule. The result determines what to do:
   - **Pass** → selector resolves and site matches spec. Write the rule to the category file.
   - **Fail (constraint mismatch)** → selector resolved but the value differs. Write the rule anyway with the **constraint from design.md**. The mismatch is a finding the next verification run will surface — not a reason to change the constraint.
   - **Fail (selector not found)** → selector is wrong. Try a different pattern and re-validate. If 2-3 attempts fail, use the DOM Inspection fallback below.
   - **Heterogeneous at compile time** (some pass, some fail) → predicate is broader than design intent. Multiple visually-distinct variants share one selector. Scope further (add landmark parent, attribute filter) so the predicate matches one homogeneous group.

   **Constraint comes from design.md, never from the live site.** When the spec says `colors.primary: #ff385c` and the site renders `rgb(224,11,65)`, the rule's constraint is `~rgb(255,56,92)` — not `~rgb(224,11,65)`. The rule will fail verification, and that's correct: it tells the user "site differs from intent." Writing a rule whose constraint matches the divergent live-site value silently encodes the bug as truth and the divergence becomes invisible forever. Never do this.

   In short: a rule is valid for writing as soon as its selector resolves to at least one element. The constraint always reflects design.md intent. (Verification time is different — see verification.md step 7c on heterogeneous failures.)

---

#### Fallback: DOM Inspection

When selector translation fails after 2-3 attempts (verify_* returns "selector not found"), inspect the live DOM:

```js
(() => {
  const els = document.querySelectorAll('header button, header [role=button], header a[class*=search]');
  return [...els].slice(0, 5).map(el => ({
    tag: el.tagName.toLowerCase(),
    id: el.id || null,
    classes: [...el.classList].filter(c => !c.match(/^(css-|sc-|_)/)),
    role: el.getAttribute('role'),
    ariaLabel: el.getAttribute('aria-label'),
    textContent: el.textContent.trim().slice(0, 30)
  }));
})()
```

From the results, pick the element that matches the claim's intent. Build a selector from its attributes. Validate again.

#### Shortcuts — Skip Full Derivation

- Claim references `body` → selector is `body`
- Claim references a unique landmark → `header`, `main`, `footer`, `[role=search]`, `[role=tablist]`
- Claim provides an explicit selector → use as-is
- Claim references a unique ARIA label → `[aria-label="exact text"]`

#### "Never" / Negative Rules

For rules like "no uppercase on prose text":
- Use general web knowledge to select elements where violations are most likely (text elements, headings, links)
- Scope broadly: `h1,h2,h3,h4,p,span,a,button` for "no uppercase anywhere"
- Let verify_* find actual violations. Do not use evaluate_js to pre-discover which elements might violate.

### Auditor

Detects drift across the four artifacts (chat ↔ design.md ↔ category files ↔ live site) and surfaces it. Each pair has its own tripwire.

**Trigger:** Any of:
- User expresses intent in chat (Scribe runs first; Auditor checks for conflict)
- User edits design.md (Auditor runs as part of the next "design.md changed" Compiler trigger)
- A verification run completes (verify_* failures are themselves drift findings)

**Drift cases and detection:**

| Drift | When detected | Action |
|---|---|---|
| Chat says X, design.md says Y (same element/property) | Scribe step, before write | Surface conflict to user; user decides; Scribe writes the winner to design.md |
| design.md says X, category file says Y (same element/property) — **chat agrees with design.md** | Layer 1 hash mismatch on next verify run; or explicitly when user says "recompile" | Recompile affected category file scopes from design.md — design.md is the source of truth (Compiler trigger) |
| design.md has a claim, NO category file has a corresponding rule (claim never compiled) | Compiler comparison during compile pass: parse design.md claims, check each has a category-file rule | **Sync violation.** Surface: "Claim `<text>` in design.md has no rule in any category file — recompile." Then compile it. |
| Category file has a rule with no claim in design.md (orphan rule) | Compiler comparison during compile pass | **Sync violation.** Surface: "Rule `<name>` in `<category>.md` has no source in design.md. Either (a) add the claim to design.md, or (b) drop the rule." Never leave orphans. |
| Live site differs from category file (verify_* failure) | Verification run, step 6/7 | Report as a finding (`verification.md` step 7 a/b/c). User decides: fix site, accept variant, or update design.md. NEVER silently rewrite the spec. |
| Live site agrees with chat, but design.md and category files are stale | Verification run reports failure → user says "intent changed" → Scribe updates design.md → Compiler recompiles → next run passes | Caught by the verify_* failure path; resolution is user-driven via design.md update. |

**Resolution:** Always surface to user. Never silently overwrite. Orphaned rules and missing rules must be either upstreamed/compiled or explicitly dropped — they cannot persist quietly.

**Quiet design.md edits.** If the user edits design.md outside chat (e.g. in their editor), the agent doesn't know until the next verify run. That run's Layer 1 hash compare catches the change and triggers recompile. This is the intended behavior — design.md is the authoritative input; the Layer 1 check is the tripwire.

## Category File Format

Each category file is a markdown file with one or more `## Scope:` sections, each containing a structured table of rules. Rules in a scope section apply only when the current URL matches that scope.

### Flat (no route-specific rules)

When all rules apply to every page, the file can omit scope headings entirely — equivalent to a single `## Scope: any`. Category files are clean markdown — no frontmatter; integrity is tracked in `.integrity.json`.

```markdown
# Visual Style

| Name | Selector | Property | Constraint |
|---|---|---|---|
| colors.canvas-deep: #0a0e1a | body | background-color | ~rgb(10,14,26) |
| colors.ink: #f8fafc | body | color | ~rgb(248,250,252) |
| colors.primary: #06b6d4 | button[class*=primary] | background-color | ~rgb(6,182,212) |
| rounded.base: 8px | button | border-radius | >=8px |
| typography.body: 16px/400 | body | font-size | =16px |
```

### Scoped (some rules are route-specific)

When the design intent differs by route, split into sections:

```markdown
# Visual Style

## Scope: any

| Name | Selector | Property | Constraint |
|---|---|---|---|
| typography.body: 16px/400 | body | font-size | =16px |
| Modal surface elevated white | [role=dialog] | background-color | white |
| rounded.base: 8px | button | border-radius | >=8px |

## Scope: route=/

| Name | Selector | Property | Constraint |
|---|---|---|---|
| Landing canvas dark | body | background-color | ~rgb(10,14,26) |

## Scope: route=/app/**

| Name | Selector | Property | Constraint |
|---|---|---|---|
| App canvas white | body | background-color | white |
```

The `Name` column is derived from the source spec — see verification.md § Categories, Tools, and Translation Tables for the canonical naming rule. Property must be kebab-case (`background-color`, not `backgroundColor`); constraint syntax lives in `references/constraint_reference.md`.

### Scope syntax

| Scope heading | Matches |
|---|---|
| `## Scope: any` | every URL visited (the default) |
| `## Scope: route=/` | exactly the root path |
| `## Scope: route=/app/*` | any path one segment under `/app/` (e.g. `/app/dashboard`) |
| `## Scope: route=/app/**` | any path under `/app/` at any depth |
| `## Scope: route=/posts/**` | every post page |

A file with no `## Scope:` headings is interpreted as a single `## Scope: any`. Equivalent and preferred when there are no route-specific rules.

A rule must appear under exactly one scope section. If the same rule conceptually applies to multiple routes, either (a) widen the scope to a glob that covers them all, or (b) duplicate the rule under each scope. The Compiler does the latter when design.md expresses the rule once but lists multiple route sections.

## Precedence

Chat (user authority) > design.md > category files > assertion JSON > live site. When surfaces conflict:
- Chat vs design.md → surface conflict, user decides, Scribe updates design.md.
- design.md vs category file → Compiler re-emits category file from design.md.
- Category file vs verification result → that's a finding (expected ≠ actual). Report; never silently rewrite.

Selector-drift handling (verify_* returns "selector not found") is verification.md step 7a, not a separate procedure here.
