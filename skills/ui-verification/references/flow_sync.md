# Flow Sync

Keeps user-flow intent consistent between chat and `.feature` files. The agent acts as scribe, compiler, and auditor across two surfaces: user input (chat or freeform notes) and `.feature` files.

Unlike visual spec sync, flow sync has only two surfaces — the chat input and the `.feature` file. There's no compiled-rules layer below the `.feature` file (the `.feature` IS the compiled rule), no integrity ledger, no audit ORPHAN/DIVERGENT classification. The simpler architecture means fewer drift cases and a simpler routing.

## Artifact Hierarchy

```
<project_root>/
  .ui-verification/
    flows/                             ← .feature files (the only persistent artifact)
      <flow-name>.feature
    reports/<run-timestamp>/flow-reports/   ← per-flow run reports (output, not source)
      <flow-name>.report.md
```

There's no `design.md` equivalent above `flows/`. The `.feature` file is both the human-readable layer and the machine-checkable layer — Gherkin syntax is already user-readable.

## Routing: which role handles which input

User input comes from chat or direct edits to `.feature` files. Routing into the right role:

| User input | First role | Then |
|---|---|---|
| Chats a flow description ("test that login works"), `.feature` file exists | Auditor — surface conflict if the description disagrees with the existing file | Scribe rewrites if user confirms |
| Chats a flow description, no matching `.feature` file | Scribe — propose the `.feature` file content, confirm path, write | (done) |
| Edits `.feature` file directly | (no Scribe — user did the write) | Next run reads the file as-is |
| Says "verify URL", no `.feature` files | Bootstrap → `flow_generation.md` (cold start, observed) | Compiler runs as part of generation; flows land at `.ui-verification/flows/` |
| Says "verify" with `.feature` files present | (no compile-source change) | Verification flow at `flow_verification.md` step 3 |

## Roles

### Scribe

Captures user intent into `.feature` files. The Scribe is the only role that writes new `.feature` files from chat input.

**Trigger:** User describes a flow in chat ("test that login works", "make sure the create-board flow with cleanup", "verify the empty state on the dashboard").

**Behavior:**
1. **Identify the flow's intent.** What journey does the user want verified? What's the start state, the actions, the expected outcomes?
2. **Pick a flow ID.** Use `<app-prefix>-<seq>` format if the user hasn't named it (e.g., `mailg-7`). Confirm with the user before writing.
3. **Compile to Gherkin.** Translate the user's freeform description into atomic Given/When/Then steps. Reference exact UI text where the user gave it; flag ambiguity where they didn't.
4. **Write metadata.** Fill in `# flow:`, `# type:`, `# app:`, and any of `# user:`, `# cleanup:` that the user provided or that the journey requires.
5. **Confirm with user.** Show the generated `.feature` file content. Ask if the steps capture their intent.
6. **Write to `<output_dir>/.ui-verification/flows/<flow-id>.feature`.** Atomic write — temp file then rename.

The Scribe does NOT write to `.feature` files for journeys the user didn't describe. If the user says "test the login flow" and the Scribe also generates a "create-board flow" because it seems related, that's fabrication. Stay literal.

### Compiler

Translates the user's intent (already in chat or already in a partial `.feature` file) into the Given/When/Then structure the verifier can execute.

**Trigger:** Any of:
- The Scribe needs to convert freeform chat into Gherkin steps.
- The user describes a partial flow ("the create-board flow but with cleanup that doesn't work yet") and the Compiler fills in the gaps.
- A step in an existing `.feature` file is too vague (e.g., `When I do the column creation thing`) and `act()` can't resolve it. Use the live DOM to inspect the page and rewrite the step with exact UI text.

**Step authoring algorithm:**

1. **Read the user's description.** What's stated explicitly? What's implied?
2. **Identify preconditions, actions, outcomes.** Map each piece to a step type:
   - Preconditions ("the user is logged in", "the dashboard is open") → `Given`
   - Actions ("click create", "type a name", "submit") → `When`
   - Outcomes ("the new board appears", "the URL changes") → `Then`
3. **Split compound steps.** "Click create and confirm" is two `When` steps. "The dialog closes and the board appears" is two `Then` steps.
4. **Use exact UI text.** Quote button labels, headings, link text verbatim. If the user said "click the button," ask them which button — don't guess.
5. **Map step text to step type by keyword position:**
   - `Given` and `And` after `Given` → `act()`
   - `When` and `And` after `When` → `act()`
   - `Then` and `And` after `Then` → `act_get()`
6. **Avoid implementation details.** Don't write `When I click the button at position [3, 4]` — write `When I click "Save"`.

**Live DOM inspection fallback.** When the user's description references UI text the Compiler doesn't know, open a session at the `# app:` URL and use `get_page_content` to read the page. Rewrite the step with the exact text observed in the DOM. Do this only when necessary — `act()` can resolve approximate text most of the time.

**Browser-loss STOP rule.** If a session is open for live DOM inspection and it disconnects, STOP. Don't write `.feature` steps based on guesses. Try ONE reconnect; if reconnect fails, surface to the user and exit. Same rule as visual spec compilation.

### Auditor

Detects contradictions across `.feature` files and surfaces them to the user. Never silently overwrites.

**Trigger:** Any of:
- User describes a flow that conflicts with an existing `.feature` file.
- User says "regenerate flows" — Auditor checks whether existing flows would be lost.
- A verification run reports a step that has been failing consistently for multiple runs (suggests the `.feature` is stale).

**Drift cases:**

| Drift | When detected | Action |
|---|---|---|
| Chat says X, existing `.feature` says Y for the same flow ID | Scribe step, before write | Surface conflict to user; user decides; Scribe writes the winner |
| User describes a "new" flow that overlaps an existing one | Auditor compares against existing `.feature` files in `flows/` | Surface: "This looks similar to flow `<id>`. Add a new flow, replace the existing one, or modify it?" |
| Step references UI text that doesn't appear in the live DOM | Verification run reports persistent step failures | Surface: "Step `<text>` in flow `<id>` has been failing for N runs — UI text may have changed. Update the `.feature` file?" |
| Two flows have the same `# flow:` ID | Parse step | Surface as configuration error; agent never auto-resolves duplicate IDs |

**Resolution:** Always surface to user. Never silently overwrite a `.feature` file. Duplicate IDs and missing dependencies are configuration errors that block the affected flow until resolved.

## Precedence

Chat (user authority) > `.feature` file > verification result. When surfaces conflict:

- Chat vs `.feature` → Surface conflict, user decides, Scribe rewrites the `.feature` file (or leaves it alone).
- `.feature` vs verification result → Verification result is a finding (expected ≠ actual). Report; never silently rewrite the `.feature` file.

The verifier never modifies `.feature` files based on run results. A flow that's been failing for N runs is still the same flow on disk — the agent surfaces the failure trend to the user, not "fixes" the spec.

## Difference from Visual Spec Sync

Flow sync is a simpler version of visual spec sync because flows have one fewer layer:

| Visual spec sync | Flow sync |
|---|---|
| 4 surfaces: chat / `design.md` / 5 category files / live site | 2 surfaces: chat / `.feature` file |
| Compile step (`design.md` → 5 category files) | (none — `.feature` IS the rule) |
| Integrity ledger (`.integrity.json`) tracks compile state | (none) |
| Audit step classifies rules ORPHAN / DIVERGENT | (none) |
| Five distinct drift cases | Two distinct drift cases (chat ↔ `.feature`, `.feature` ↔ live site) |

The simpler architecture is intentional. Gherkin is already a human-readable layer; there's nothing to compile from. Live UI behavior is non-deterministic (Nova Act re-interprets each run), so the integrity-ledger pattern wouldn't help — every flow runs every time anyway. ORPHAN/DIVERGENT classification doesn't apply because there's no upstream layer for `.feature` rules to be orphaned from.

## What's NOT Sync's Job

- **Don't write `.feature` files for journeys the user didn't describe.** That's fabrication. Even if the agent thinks "they're testing login, they probably also want to test logout," ask before writing.
- **Don't auto-modify `.feature` files based on verification failures.** A failing step is a finding, not a signal to rewrite. The user decides whether to fix the site, change the test, or accept the divergence.
- **Don't search the filesystem.** All `.feature` files live at `<output_dir>/.ui-verification/flows/`. Read them with the Read tool. No `find /`, no `find ~`.

## Reference Map

| Topic | Reference |
|---|---|
| `.feature` file schema and writing conventions | `references/flow_authoring.md` |
| Cold-start flow generation | `references/flow_generation.md` |
| Flow execution model | `references/flow_verification.md` |
| Combined report format | `references/verification_report.md` |
| Visual spec sync (the parallel mode) | `references/spec_sync.md` |
