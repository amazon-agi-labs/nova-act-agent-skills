# Workflow Refinement

Use the browser CLI to improve automation workflows by running them multiple times, analyzing failures, and revising prompts until stable.

## Entry Points

**Existing prompts** — you have agent code (Python `nova.act()` calls) or CLI commands to test. Start at "Testing Prompts with the CLI" below.

**No existing prompts** — you need to author the workflow first. Explore the target site(s) with `execute` and `ask` to discover the flow, write your prompts, then come back here to refine them. See `flow_discovery.md` for structured exploration techniques.

## Workflow

```
1. Define the workflow prompt(s) to test
2. Run multiple times in separate browser sessions (see `parallel_sessions.md` for parallization guidance)
3. Analyze results (stdout transitions, verify output, steps.yaml)
4. Classify and fix failures
5. Rerun — both failed and previously passing sites to check for regressions
6. Repeat until stable
```

## Testing Prompts with the CLI

When the workflow under test lives in Python agent code, translate each `nova.act()` call to an equivalent CLI command to test the prompts in isolation:

```python
# Agent code:
#   nova.act("Click the checkout button and proceed to payment", max_steps=5)
# Becomes:
act browser execute "Click the checkout button and proceed to payment" \
  --session-id test-1 --starting-page "$URL" --headless \
  --nova-arg max_steps=5
```

Keep the prompts identical — the goal is to validate the same prompts the agent uses.

CLI testing isolates prompts from your runtime environment (containers, AgentCore, DynamoDB, etc.) for fast iteration. Once prompts are stable, validate with your actual agent code — how you run that is implementation-dependent.

## Automated Pass/Fail

End each test run with `act browser verify` to get a machine-readable result instead of manually inspecting output:

```bash
act browser verify "A confirmation message is visible on the current page" \
  --session-id test-1 --headless
```

The output includes `passed: true/false`, `actual:`, and `evidence:` fields. Grep for `passed: true` to determine overall result. This turns N×M test matrices into something you can script and summarize in a table.

## Failure Analysis

Most failures are diagnosable from command stdout alone:

- `status: success/error` — did the command succeed?
- `transition:` — what changed on the page (elements appeared/removed, navigation)
- `passed: true/false` — from `verify` commands

When stdout isn't enough, escalate:

1. **`steps.yaml`** (in `log_dir`) — step-by-step actions with chain-of-thought reasoning. Read this when you need to understand *why* the model did something. See the Observability section in `browser_cli.md`.
2. **Screenshots** (`screenshot.png`, `failure.png` in `log_dir`) — visual state. See `visual_reporting.md` for building reports with embedded screenshots.

## Failure Classification

Classify before acting — not all issues warrant the same response:

| Category | Signal | Action |
|----------|--------|--------|
| **Transient browser crash** | `BROWSER_ERROR`, "process is no longer running" | Retry — don't change prompts |
| **Wrong action** | Model clicked the wrong element or navigated to an unrelated page | Tighten the prompt with more specific instructions |
| **Missed element** | "No visible changes detected", model scrolled past the target | Add specificity (e.g. "including small text links and underlined text") |
| **Overshot** | Model completed the goal but kept going (clicked past confirmation) | Add explicit halt condition ("Stop immediately when you see X") |
| **Inefficient path** | Model succeeded but took many steps, clicked wrong things first, or explored before finding the right element | Add ordering hints to the prompt (e.g. "scroll down first to see all options before clicking") |
| **Non-deterministic path** | Same prompt takes 2 steps on one run and 8 on another | Make the prompt more specific about which element to target or what order to try things |

## Faster Iteration with Mocks

Iterating against real sites is slow (API calls, page loads, anti-bot) and non-deterministic (content changes, A/B tests). Generate static HTML mocks from real site trajectories and iterate against those with `file://` URLs. See `mock_generation.md`.

## Tips

- **Run multiple times on the same page** — catches non-deterministic behavior where the model takes different paths each run
- **Run across different pages** — catches prompts that only work on one layout and fail on others
- **Use `--nova-arg max_steps=N`** — limit steps to catch runaway prompts early
- **Headless for bulk, headed for debugging** — offer the user a headed session to visually inspect a specific failure
- **Script it** — wrap the steps in a shell script that accepts site name and run number, logs per-step status, and produces a result file for deterministic re-runs
- For parallel runs, see `parallel_sessions.md`

## Related Files
- `mock_generation.md` — generate static HTML mocks from trajectories for fast iteration
- `parallel_sessions.md` — run multiple sessions concurrently with staggered launches
- `visual_reporting.md` — build markdown reports with screenshots from session artifacts
- `browser_cli.md` — full CLI command reference, session log artifacts (`steps.yaml`, `snapshot.yaml`, screenshots)
