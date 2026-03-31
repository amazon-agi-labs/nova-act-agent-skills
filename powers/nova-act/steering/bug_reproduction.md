# Bug Reproduction with Nova Act

Use the browser CLI to reproduce reported bugs, capture evidence, and generate regression tests.

## Reproduction Workflow

```
Bug report → reproduce with browser CLI → capture evidence → export session → convert to Gherkin → verify fix
```

## Step 1: Reproduce

Follow the bug report steps using the CLI:

```bash
act browser goto https://app.example.com/checkout --session-id bug-123
act browser execute "1. Add item X to cart 2. Apply promo code SAVE20 3. Click checkout" --session-id bug-123
```

## Step 2: Capture Evidence

| Tool | What It Reveals | Example |
|------|----------------|---------|
| `screenshot` | Visual state at failure | `act browser screenshot -o bug-123.png --session-id bug-123` |
| `console-log` | JS errors, uncaught exceptions | `act browser console-log --errors-only --session-id bug-123` |
| `network-log` | Failed API calls, CORS errors | `act browser network-log --status ">=400" --session-id bug-123` |
| `snapshot` | Missing/hidden elements | `act browser snapshot -o bug-state.yaml --session-id bug-123` |
| `ask` | Describe current page state | `act browser ask "Is there an error message?" --session-id bug-123` |
| `diff` | What changed (or didn't) after action | `act browser diff "Click submit" --focus "error area" --session-id bug-123` |
| `perf` | Performance regressions | `act browser perf --metrics vitals --session-id bug-123` |
| `evaluate` | Custom JS state inspection | `act browser evaluate "document.querySelector('.error')?.textContent" --session-id bug-123` |

## Step 3: Export & Convert

```bash
act browser session export --session-id bug-123 -o bug-123-repro.yaml
```

Convert to Gherkin (see `gherkin_testing.md`). The resulting `.feature` file IS the regression test.

## Step 4: Verify Fix

After fix is deployed, replay the scenario:

```bash
# Compile the regression test
act browser qa-plan bug-123.feature --output plan.json

# Agent executes the plan commands from plan.json
# Final step should pass where it previously failed
act browser verify "checkout completed successfully" --session-id bug-123-verify
```

## Related Files
- `gherkin_testing.md` — Gherkin pipeline and session export conversion
- `browser_cli.md` — Full CLI command reference
- `flow_discovery.md` — Live app exploration → codebase mapping
