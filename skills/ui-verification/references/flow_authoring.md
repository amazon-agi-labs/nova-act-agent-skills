# Flow Authoring

`.feature` files describe user journeys against your live web app. The flow verifier reads each file, parses the metadata and Gherkin steps, and executes them via `act()` (actions) and `act_get()` (assertions).

This file describes the schema and writing conventions. For the execution model, see `references/flow_verification.md`. For cold-start generation when no flows exist, see `references/flow_generation.md`.

## File Location

Each flow is one `.feature` file at:

```
<project_root>/.ui-verification/flows/<flow-name>.feature
```

The filename (without extension) MUST match the `# flow:` metadata field. One scenario per file.

## Flow Types

Three types map to common verification intents:

| Type | What it tests | Example |
|---|---|---|
| `happy_path` | The intended user journey completes successfully | "Create a new board and add tickets" |
| `error_path` | Invalid input or edge cases produce the correct error response | "Submit empty form should show 'required field' errors" |
| `state_completeness` | Each screen renders its defined states correctly | "Empty state, loading state, populated state, error state on the dashboard" |

Pick the type that matches the user's intent. A flow that mixes happy-path actions with error-path assertions should be split into two flows.

## File Schema

```gherkin
# flow: mira-2
# type: happy_path
# app: https://aws-mira-prod.turing.com
# user: member
# cleanup: delete column "Design" from board

Feature: MIRA-2 - Create board column and move tickets
  Scenario: Create a new "Design" column and move tickets into it
    Given I am on the "Mira Project Management" project board
    When I create a new column named "Design" with color "pink"
    Then the board should contain a column named "Design" with pink color
    When I move the ticket "Login page design" from "ToDo" to "Design"
    And I move the ticket "Design OTP screen" from "ToDo" to "Design"
    Then the "Design" column should contain "Login page design"
    And the "Design" column should contain "Design OTP screen"
```

The metadata block comes first (one `#`-prefixed line per field), followed by a single `Feature:` block with exactly one `Scenario:` inside.

## Metadata Fields

| Field | Required | Purpose |
|---|---|---|
| `# flow:` | Yes | Unique identifier. MUST match the filename (without `.feature`). The verifier validates this at parse time and skips the flow on mismatch. |
| `# type:` | Yes | `happy_path` \| `error_path` \| `state_completeness` |
| `# app:` | Yes | Target URL (the page where the scenario starts) |
| `# user:` | If auth required | Role identifier for an auth-gated journey. The runtime resolves the credential at execution time. Example: `admin`, `member`. |
| `# cleanup:` | No | Best-effort teardown after execution. Runs regardless of pass/fail. |

Missing required fields are a parse error. The verifier surfaces it and skips the flow with reason `metadata incomplete: <field>`.

**Flows are standalone.** Each flow declares its own preconditions in `Given` steps; flows do not order across each other. If two journeys share setup, duplicate the `Given` steps in both — don't try to chain flows. The verifier does not order flows by dependency.

## Step Structure

Steps are atomic. One action or one assertion per line. Compound steps ("create a board AND open it") are split into two steps.

| Keyword | Type | Tool used at run time |
|---|---|---|
| `Given` | Precondition (hard — failure aborts the rest of the flow) | `act()` |
| `When` | Action (soft — failure recorded, run continues) | `act()` |
| `Then` | Assertion (soft — failure recorded, run continues) | `act_get()` |
| `And` after `Given` | Another precondition | `act()` |
| `And` after `When` | Another action | `act()` |
| `And` after `Then` | Another assertion | `act_get()` |
| `But` after `Then` | Negative assertion ("but it should NOT show...") | `act_get()` |

`Given` is the only step type that aborts the flow on failure. The rest are soft — record the failure, continue with the next step.

## Writing Verifiable Steps

### Good steps (directly executable)

```gherkin
Given I am on the "Mira Project Management" project board
When I click the "Create Column" button in the toolbar
And I type "Design" into the column name field
And I click "Save"
Then the board should contain a column named "Design"
```

Each step is atomic, references exact UI text in quotes, and describes one action or one observable state.

### Weak steps (hard to execute deterministically)

```gherkin
When I do the column creation thing
Then it should look right
And the page should feel responsive
```

Weak steps cause `act()` to thrash through interpretations and `act_get()` to return ambiguous answers. Rewrite with exact UI text.

## Conventions

1. **Quote exact UI text.** Button labels, field placeholders, link text, page titles all go in double quotes. `Click "Save"`, not `click save`.
2. **One action per step.** Combine assertions if they describe the same observable state ("the column 'Design' should contain ticket X and ticket Y" is fine), but split distinct actions.
3. **Reference data placeholders explicitly.** If the scenario uses test data, include the value in the step text: `When I create a board named "Q4 Roadmap"`. Don't rely on test fixtures the verifier doesn't know about.
4. **Use stable identifiers.** Reference UI elements by visible text (button labels, headings, ARIA labels) rather than CSS class names or test IDs unless the spec genuinely needs that level of specificity.
5. **Describe the observable outcome.** `Then` steps describe what the user sees, not what the system does internally. `Then the dashboard should show "5 active boards"`, not `Then the database should contain 5 boards`.
6. **Avoid implementation details.** Don't specify "click the third button in the second row" — describe the button by what it says or does.

## Examples by Flow Type

### Happy path

```gherkin
# flow: mira-2
# type: happy_path
# app: https://aws-mira-prod.turing.com
# user: member
# cleanup: delete column "Design" from board

Feature: MIRA-2 - Create board column and move tickets
  Scenario: Create a new "Design" column and move tickets into it
    Given I am on the "Mira Project Management" project board
    When I create a new column named "Design" with color "pink"
    Then the board should contain a column named "Design" with pink color
    When I move the ticket "Login page design" from "ToDo" to "Design"
    And I move the ticket "Design OTP screen" from "ToDo" to "Design"
    Then the "Design" column should contain "Login page design"
    And the "Design" column should contain "Design OTP screen"
```

### Error path

```gherkin
# flow: zend-006
# type: error_path
# app: https://zendly.example.com
# user: admin

Feature: ZEND-006 - Submit empty board name shows validation error
  Scenario: Empty board name fails validation with "required" message
    Given I am on the "Create Board" dialog
    When I leave the board name field empty
    And I click "Create"
    Then I should see a "Board name is required" error
    And the dialog should remain open
```

### State completeness

```gherkin
# flow: mailg-15
# type: state_completeness
# app: https://mailgrid.example.com
# user: owner

Feature: MAILG-15 - Inbox renders empty, loading, populated, and error states
  Scenario: Each inbox state renders correctly
    Given I am on the "Inbox" page with no messages
    Then the empty state illustration should be visible
    And the text "No messages yet" should be shown
    When I trigger a slow network and reload the page
    Then a loading skeleton should be visible
    When the network resolves and the inbox has 5 messages
    Then 5 message rows should be visible
    When I trigger a server error and reload
    Then an error state with retry button should be visible
```

## Iterating on Flows

After a verification run:

1. **Review failures.** Some failures indicate `.feature` steps that need updating (the UI changed since the flow was authored).
2. **Review ambiguous Then results.** If `act_get()` returned medium-confidence findings often, the assertion text is too vague — rewrite with exact UI text or supplement with `evaluate_js`.
3. **Review session warnings.** A failed cleanup or a Given that failed because of state from a prior flow points at a teardown gap or a missing `Given` step in this flow's own preconditions.
4. **Add missing flows.** The verifier only runs what's in `flows/`. If a journey isn't covered, add it.

When the live UI changes (text, layout, navigation), `.feature` files must be updated to match — they reference exact UI text. The verifier will not auto-rewrite them.

## Generating Flows from a Live Site

If you don't have flows yet, the skill can crawl the app and generate baseline `.feature` files. See `references/flow_generation.md` for the cold-start workflow. Generated flows are a starting point — review and edit them to reflect the journeys you actually want to verify.

## Difference from Visual Spec Authoring

Flow authoring has no equivalent to `design.md` and the 5 compiled category files. The `.feature` file IS the source — there's no upstream layer to compile from, no `.integrity.json` to track, no audit step.

| Layer | Visual verification | Flow verification |
|---|---|---|
| Source of intent | `design.md` (prose + YAML) | `.feature` file (Gherkin) |
| Compiled rules | 5 category `.md` files | (none — `.feature` is the rule) |
| Compile-state ledger | `.integrity.json` | (none) |
| Audit step | ORPHAN / DIVERGENT classification | (none) |
| Per-run output | assertion JSON + report | per-flow report + combined report |

This is intentional — flows are inherently behavioral, the Gherkin syntax is already the user-readable layer, and there's no compilation work that needs caching.
