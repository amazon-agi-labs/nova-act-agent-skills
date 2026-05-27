# Flow Generation

Reverse-engineer baseline `.feature` files from a live web app when no flows exist. Entry point is `flow_verification.md` step 2 (URL given, no flows defined, user confirms generation). Output goes to `<project_root>/.ui-verification/flows/<flow-name>.feature`.

## When to Use

- The user has a URL but no `.feature` files at `.ui-verification/flows/`.
- The user wants a verification baseline before adding their own scenarios.
- You're onboarding a new app and want to capture the obvious user journeys before deeper testing.

Do NOT use this when:
- The user has provided their own freeform flow descriptions — run the Scribe (see `references/flow_sync.md`) instead.
- `.feature` files already exist — run them as-is unless the user explicitly asks to regenerate.

## Conservative over Comprehensive

Better to ship 5 honest flows than 20 hallucinated ones. If a journey isn't observable from a one-level-deep crawl, skip it. The user will add deeper flows during review.

Side-effecting flows (creating, editing, deleting) MUST include `# cleanup:` metadata that undoes the side effect. If a side effect can't be cleaned up reliably, skip the flow rather than ship one that pollutes the app's state.

## Phases

### Phase 1: Surface crawl

Open a session and visit each top-level navigation route exactly once. Use `start_browse(url, intent="generate flow baseline", browser_mode="local")` to open the session. **Pass `browser_mode="local"`.**

What "one level deep" means:
- Click each link in the primary navigation bar, exactly once.
- Read each resulting page with `get_page_content`.
- Catalog interactive elements found (forms, buttons, links, cards) without using them.
- Note the URL structure for each route visited.

What you do NOT do during the crawl:
- Interact with forms (no typing, no selecting, no submitting).
- Advance multi-step flows.
- Follow CTAs or action buttons (e.g., "Book Now", "Sign Up").
- Click anything that isn't a top-level navigation link.

The crawl ends when every top-level nav link has been visited once. Stop there.

### Phase 2: Journey identification

Categorize what you observed into journey types:

| Category | What it looks like | Generates which flow type |
|---|---|---|
| Navigation | "From dashboard, click 'Projects' to see project list" | `happy_path` |
| Read-only | "On the dashboard, I see N active projects with status badges" | `state_completeness` |
| Auth-gated | "Clicking 'Settings' redirects to login if not authenticated" | `error_path` (if you can verify the redirect without logging in) |
| Side-effecting | "Click 'Create' to make a new board" | `happy_path` ONLY if cleanup is feasible; else skip |

Skip side-effecting journeys you can't reliably reverse. A flow that creates a record but can't delete it pollutes future runs. Either declare a `# cleanup:` step that the verifier can execute, or don't generate the flow.

### Phase 3: Build `.feature` files incrementally

Don't wait until all phases are done. As soon as you've identified a journey in Phase 2, write the corresponding `.feature` file. This way if generation gets interrupted, you have partial output rather than nothing.

For each journey:
1. Pick a flow ID (typically `<app-prefix>-<seq>`, e.g. `mailg-1`, `mira-2`, `zend-001`).
2. Create `<output_dir>/.ui-verification/flows/<flow-id>.feature`.
3. Write the metadata header.
4. Write the Gherkin Feature + Scenario block.

### Phase 4: Convert observations to Gherkin steps

Translate raw observations into atomic Given/When/Then steps. Reference exact UI text from `get_page_content`. See `references/flow_authoring.md` for the writing conventions.

| Observation | Gherkin step |
|---|---|
| "User starts on the dashboard" | `Given I am on the "Dashboard" page` |
| "Click 'Projects' in nav" | `When I click "Projects" in the primary navigation` |
| "URL changes to /projects" | `Then the URL should be "/projects"` |
| "Page heading reads 'Your Projects'" | `And the heading "Your Projects" should be visible` |
| "Project list shows N items" | `And at least 1 project card should be visible` |

Use exact UI text in quotes. If the heading reads "Your Projects" verbatim, the step says `"Your Projects"`, not `"projects page heading"` or `"the project list title"`.

### Phase 5: Write metadata headers

Every generated `.feature` file gets a complete metadata block:

```gherkin
# flow: <flow-id>
# type: happy_path | error_path | state_completeness
# app: <URL the scenario starts at>
# user: <credentials> (<role>)   ← only if auth was required to reach this state
# cleanup: <what to undo>         ← only for side-effecting flows
```

If the journey is auth-gated and you don't have credentials, skip the flow rather than write a metadata block with placeholder credentials. Surface the gap to the user during the summary step.

### Phase 6: Tell the user what you built, then run flow verification once

After all `.feature` files are written, present a summary AND immediately run flow verification on the generated flows.

**Step 1 — present the summary:**

```
Generated flows from https://your-app.com:

flows/
  app-1.feature — happy_path — "Navigate to projects page"
  app-2.feature — happy_path — "Open a project's details"
  app-3.feature — state_completeness — "Empty dashboard renders all states"
  app-4.feature — happy_path — "Create a new board (cleanup: delete board)"

Skipped (could not generate reliable flows):
  - Sign-up flow: cannot generate reliably without credentials
  - Delete account: side-effect with no easy cleanup
  - Payment flow: requires real payment data; out of scope for generation

These represent the OBSERVED journeys on the site. Running verification now to validate.
```

**Step 2 — run flow verification:**

Hand off to the flow verifier (`references/flow_verification.md`) and run all generated flows. The verifier handles its own session management and reporting.

**Step 3 — interpret the results:**

When the verification report comes back, classify each result against generation:

| Result | Meaning |
|---|---|
| Flow passed | Generated flow is correct against the live site. Use as baseline. |
| Flow failed, scenario was generated this run | Generation problem — the flow you wrote doesn't match what the live site actually does. Surface as `generation issue: <flow-id>` so the user knows the flow needs fixing, not the site. |
| Flow failed, scenario was hand-authored or imported | Real failure — the live site doesn't match the user's intent. Treat as a verification finding. (Should not happen during generation, but flag if it does.) |

In the user-facing summary that wraps generation, call out which flows passed and which failed-as-generated:

```
Verification complete:
  ✅ app-1.feature — passed
  ✅ app-2.feature — passed
  ❌ app-3.feature — failed (generation issue — empty state assertion didn't match)
  ✅ app-4.feature — passed (cleanup ran successfully)

3 of 4 flows pass on first run. app-3 needs a fix to its assertion text;
review and edit before treating these as a stable baseline.
```

**Step 4 — ask the user how to proceed:**

If there are generation issues, ask: "Want me to retry generating app-3 with different assertions, or would you rather review and edit it yourself?"

If all flows passed, ask: "All flows pass. Want to keep them as the verification baseline, or review and edit any first?"

The user is the final authority on whether generated flows ship. Don't auto-promote a baseline.

## Generated Flows Are a Starting Point

Generation captures what's observable from a one-level-deep crawl. It does NOT capture:

- **Multi-step flows** — anything that requires advancing through forms or wizards.
- **Auth-gated journeys** unless credentials were provided in chat.
- **Edge cases** — invalid input, error responses, network failures.
- **Data-dependent flows** — flows that require specific test data to produce meaningful assertions.
- **Hidden screens** — anything not reachable from the primary navigation.
- **State variants** — empty, loading, populated, error states unless they were observable during the crawl.

Tell the user about these gaps in the summary. They fill them in during review.

## Tool Roles

| Tool | When to use |
|---|---|
| `start_browse(url, intent, browser_mode="local")` | Open the session at the start of generation |
| `get_page_content(session_id, format="text")` | Read each crawled route's content |
| `act(session_id, "navigate to <link>")` | Click each top-level nav link during crawl |
| `evaluate_js(session_id, "<script>")` | Confirm URL or DOM state deterministically when needed |
| `session_close(session_id)` | Close at the end of Phase 6 |

Use `screenshot` + `get_page_content` for your own reasoning about page structure. The agent (you) interprets the screenshot and HTML — `act_get` is for structured extraction with a schema, not for "describe the page."

## Anti-Patterns

Don't do these:

```
# Wrong: generates aspirational steps the agent never observed
When I complete the multi-step onboarding wizard
Then onboarding should be complete

# Wrong: side effect with no cleanup
When I delete my account
Then the account should be gone

# Wrong: relies on test data the verifier doesn't have
Given my account has 47 projects
When I filter by "Active"
Then I should see exactly 23 projects

# Wrong: assertion is too vague to verify
Then the page should feel polished and on-brand
```

Each of these would produce unreliable flows. Skip the journey instead of fabricating steps.

## Difference from Visual Spec Generation

Flow generation produces only `.feature` files — there's no `design.md` to seed, no 5 category files, no `.integrity.json` to write. Generation runs once, produces the files, you confirm with the user, done. No compile step, no audit step, no integrity ledger.

| Visual spec generation | Flow generation |
|---|---|
| Phase 0: detect source code | (no equivalent — flows are behavioral, not implementation-derived) |
| Phase 1: visual exploration | Phase 1: surface crawl (one level deep) |
| Phase 2: targeted extraction via `evaluate_js` | Phase 2: journey identification |
| Phase 3-4: build category files, convert to constraints | Phase 3-4: build `.feature` files, convert to Gherkin |
| Phase 5: write 6 files (design.md + 5 categories) + ledger | Phase 5: write metadata headers |
| Phase 6: sanity-check via `verify_*` | (no equivalent — flows are non-deterministic; running them as a "self-check" against the same session would be misleading) |
| (no equivalent) | Phase 6: confirm with user |

## Return to Verification

After generation completes, the agent returns to `flow_verification.md` step 3 (parse metadata) — the same browser session can continue, or a fresh session per flow can be opened (the default).
