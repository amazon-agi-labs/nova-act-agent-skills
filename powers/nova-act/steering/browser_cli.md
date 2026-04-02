# Nova Act Browser CLI

> **READ THIS ENTIRE FILE** — it contains command hierarchy, prompting patterns, and example transcripts that are all essential for effective CLI usage.

## ⚠️ CRITICAL INSTRUCTIONS

### Mission-First Philosophy
**Always prefer giving Nova Act a browser mission over issuing low-level commands.** The smart-path commands are your DEFAULT operating mode:

| Default Commands (Smart Path) | Purpose |
|-------------------------------|---------|
| `execute` | Multi-step browser plan delegation — your primary tool for actions |
| `extract` | AI-powered data extraction — your primary tool for getting information |
| `ask` | Read-only question about the current page |
| `fill-form` | Natural language form filling (requires JSON input) |
| `verify` | Assert a condition on the page (exit 0 = pass, exit 1 = fail) |
| `scroll-to` | Iterative scroll+verify to reach a named section |
| `wait-for` | Poll until a condition is met |
| `click` | Click a target (NL description, CSS selector, or snapshot ref like `e12`) |
| `type` | Type text into an element or the focused element |

**Fast-path commands are fallbacks only** — use them when a broader mission isn't possible (e.g., literally just navigating to a URL, going back/forward, or refreshing):

| Fallback Commands (Fast Path) | Purpose |
|-------------------------------|---------|
| `goto` | Raw Playwright navigation to a known URL |
| `back` / `forward` | Browser history navigation |
| `refresh` | Reload page |
| `page` | Playwright page API passthrough (`page --signatures` to discover methods) |
| `evaluate` | Run JavaScript — ONLY for precise scrolling (`window.scrollTo`) or known-property reads |

### Session Rules
- **NEVER close a session** unless the user explicitly asks you to. Sessions are expensive to create and the user may want to return to them.
- **NEVER close all sessions** unless the user explicitly asks you to.
- **NEVER kill Chrome or Chromium processes** (e.g., `pkill chrome`, `kill -9 $(pgrep chrome)`, `killall Google Chrome`). Nova Act manages its own browser lifecycle. Killing browser processes externally will corrupt session state and break automation. If a browser appears stuck, use `act browser sessions` to check status, or start a new session.

The browser CLI (`act browser`) is the preferred way for coding agents to interact with web browsers. It provides persistent sessions, structured output, and composable commands that work naturally in tool-use workflows.

## Setup

```bash
pip install 'nova-act[cli]'
act browser setup                        # Store API key in ~/.nova-act-cli/config
act browser setup --api-key <your-key>   # Non-interactive
# OR set env: export NOVA_ACT_API_KEY="your_key"
```

When running from a virtual environment, always activate and set credentials in the same command chain:

```bash
# API key mode
source <venv>/bin/activate && export NOVA_ACT_API_KEY=<key> && act browser <command>

# AWS auth mode
source <venv>/bin/activate && export AWS_PROFILE=<profile> && act browser <command>
```

## Session Logs Directory

Every command writes artifacts to `~/.act_cli/browser/session_logs/<session>/<timestamp>_<command>/`:

| File | Present When | Use For |
|------|-------------|---------|
| `log.txt` | Always | Full command execution log |
| `snapshot.yaml` | AI commands | Accessibility tree with element refs (e1, e2...) |
| `screenshot.png` | AI commands | Post-command screenshot |
| `before.png` | AI commands with transitions | Pre-command screenshot |
| `steps.yaml` | Multi-step AI commands | Step-by-step execution trace |
| `failure.png` | Command failed | Screenshot at failure point |
| `content.txt` | get-content | Extracted page content |
| `page.pdf` | pdf | Generated PDF |

**Observability options** (in priority order):
1. **`steps.yaml`** — Understand what happened during multi-step commands. Usually sufficient.
2. **`snapshot.yaml`** — Element refs for targeted follow-up (grep for keywords to find refs like `e14`).
3. **Full logs** (`log.txt`, screenshots) — Rarely needed. Use when steps.yaml doesn't explain a failure.

## Commands

### Browsing Commands (19)

| Command | Purpose |
|---------|---------|
| `execute` | Multi-step browser plan delegation (AI) |
| `goto` | Raw Playwright navigation |
| `ask` | Read-only question about page (AI) |
| `click` | Click target (NL, CSS, or snapshot ref e.g. `e12`) (AI) |
| `type` | Type text into element or focused element (AI) |
| `fill-form` | Natural language form filling (AI) |
| `scroll-to` | Iterative scroll+verify to reach section (AI) |
| `wait-for` | Poll until condition met (AI) |
| `verify` | Assert condition, exit 0 (pass) / 1 (fail) (AI) |
| `back` | Browser history back |
| `forward` | Browser history forward |
| `refresh` | Reload page |
| `page` | Playwright page API passthrough (`page --signatures` to discover methods) |
| `console-log` | Browser console messages |
| `network-log` | Network requests/responses |
| `tab-new` | Open new tab |
| `tab-close` | Close tab (by index or active) |
| `tab-list` | List open tabs |
| `tab-select` | Switch to tab by index |

### Extraction Commands (10)

| Command | Purpose |
|---------|---------|
| `extract` | AI-powered data extraction |
| `get-content` | Dump page content to file |
| `screenshot` | Capture screenshot |
| `snapshot` | Accessibility tree as YAML with refs (e1, e2...) |
| `diff` | Before/after comparison of an action (3 AI calls) |
| `query` | CSS selector → JSON |
| `style` | Computed CSS properties |
| `evaluate` | Run JavaScript in page context |
| `perf` | Performance metrics (Navigation, Vitals, Memory) |
| `pdf` | Export page as PDF (requires headless) |

### Session Commands (9)

| Command | Purpose |
|---------|---------|
| `session list` | List active sessions |
| `session create` | Create named session at URL |
| `session close` | Close specific session |
| `session close-all` | Close all sessions |
| `session prune` | Clean up stale sessions (24h+) |
| `session export` | Export history (JSON/YAML) or `--report` for markdown report with resources |
| `session record-show` | Display recording manifest |
| `session trace-start` | Start Playwright tracing |
| `session trace-stop` | Stop tracing, save .zip |

### Setup Commands (3)

| Command | Purpose |
|---------|---------|
| `setup` | Store API key / AWS config |
| `doctor` | Environment health checks |
| `qa-plan` | Compile Gherkin `.feature` → CLI plans |

## Command Hierarchy

**Decision: Can I describe this as a browser task?**

- **YES** → Use a smart-path command with a mission description:
  - Multi-step action → `execute` with a numbered plan
  - Get data from the page → `extract` with a description of what to retrieve
  - Ask a question about the page → `ask`
  - Fill out a form → `fill-form` with JSON field-value pairs
  - Check a condition → `verify`
- **NO** (literally just one trivial action) → Use a fast-path fallback:
  - Navigate to a known URL → `goto`
  - Click one known button/ref → `click`
  - Go back/forward/refresh → `back`, `forward`, `refresh`
  - Precise JS scroll position → `evaluate` with `window.scrollTo(...)`
- **Need to check page state between missions?** → `snapshot` (structured) or `screenshot` (visual)

**If you're about to chain 2+ fast-path commands, stop and use `execute` instead.**

### Prompting Best Practices

1. **Numbered steps, not sentences.** `"1. Go to URL 2. Click X 3. Extract Y"` — not `"Go to the site and find the pricing"`.
2. **Pass key details explicitly.** Include URLs, field names, expected values, selectors when known.
3. **One `execute` per logical task.** Don't split a coherent flow into many small calls. Don't cram unrelated tasks into one call.
4. **Less ambiguity = fewer retries.** Specific prompts reduce exploration and inference cost.

### Extract vs Execute

- **`extract`** — Returns data. Use when the goal is getting information from a page.
- **`execute`** — Performs actions. Does NOT return content. Use for clicking, form filling, navigation.

### fill-form Requires JSON Input

`fill-form` **MUST** receive a JSON object mapping field names to values. Plain text descriptions will fail or produce unpredictable results.

```bash
# ✅ Correct — JSON object with field-value pairs
act browser fill-form '{"username": "test@example.com", "password": "secret"}' --session-id work
act browser fill-form '{"First Name": "Jane", "Last Name": "Doe", "Plan": "Enterprise"}' --session-id work

# ❌ Wrong — plain text description
act browser fill-form "Fill name 'Jane Doe', email 'jane@example.com'" --session-id work
```

### Snapshot YAML Grep Technique

After any command, use the `log_dir` from output to grep the snapshot YAML before making another inference call:

```bash
# After any command, use the log_dir from output:
grep -i "keyword" <log_dir>/snapshot.yaml
```

## Examples & Anti-Patterns

### Good: Execute-First Research Flow

```
# Agent decision: Multi-step objective (navigate + extract + scroll + summarize) → execute
$ act browser execute "1. Go to https://example.com/product/12345 2. Extract specs 3. Scroll to reviews 4. Summarize top 3 reviews" --session-id research --nova-arg max_steps=30
status: success
reached: false
transition: Navigated to product page, extracted specs. Could not find reviews section.
log_dir: ~/.act_cli/browser/session_logs/research/20260330_155318_execute/

# Agent decision: Need to check page state after partial failure → snapshot (via log_dir grep)
$ grep -i "review" ~/.act_cli/browser/session_logs/research/20260330_155318_execute/snapshot.yaml
# e31: button "Load Reviews"

# Agent decision: Single simple action (click a known button ref) → fast-path click
$ act browser click "e31" --session-id research
status: success
clicked: true
transition: Reviews section loaded with 47 reviews.
log_dir: ~/.act_cli/browser/session_logs/research/20260330_155322_click/

# Agent decision: Need page understanding (summarize reviews) → extract
$ act browser extract "Summarize the top 3 customer reviews" --schema string --session-id research --nova-arg max_steps=30
status: success
result: "1. Great quality... 2. Fast shipping... 3. Good value..."
log_dir: ~/.act_cli/browser/session_logs/research/20260330_155325_extract/
```

### Bad: Same Task Done Wrong (Many Small Calls)

```
# ❌ Agent splits a coherent flow into many separate calls, losing context between each
$ act browser goto https://example.com/product/12345 --session-id research
$ act browser execute "Extract the product specs" --session-id research --nova-arg max_steps=30
$ act browser execute "Scroll to the reviews section" --session-id research --nova-arg max_steps=30
$ act browser execute "Summarize the top 3 reviews" --session-id research --nova-arg max_steps=30
# 4 calls instead of 1. Context lost between each. Slower and more expensive.
```

### Good: Execute-First Form Flow

```
# Agent decision: Multi-step objective (fill form + submit + verify) → execute
$ act browser execute "1. Fill the registration form with name 'Jane Doe', email 'jane@example.com', plan 'Enterprise' 2. Submit the form 3. Wait for confirmation page" --session-id apply --nova-arg max_steps=30
status: success
reached: true
transition: Form filled, submitted, confirmation page displayed.
log_dir: ~/.act_cli/browser/session_logs/apply/20260330_160012_execute/

# Agent decision: Need to check page state → snapshot
$ act browser snapshot --session-id apply
# ... accessibility tree with confirmation details ...

# Agent decision: Single simple action (verify a condition) → fast-path verify
$ act browser verify "registration confirmation is displayed" --session-id apply
status: success
passed: true
log_dir: ~/.act_cli/browser/session_logs/apply/20260330_160020_verify/
```

### Bad: Same Task Done Wrong (Raw Playwright)

```
# ❌ Agent uses page fill/click for a login flow instead of delegating
$ act browser page fill --kwargs '{"selector": "#username", "value": "testuser"}'
$ act browser page fill --kwargs '{"selector": "#password", "value": "secret"}'
$ act browser page click --kwargs '{"selector": "#submit"}'
# 3 fragile calls that break if selectors change. execute handles this in one call.
```

### Good: Extract-First Data Retrieval

```
# Agent decision: Single simple action (navigate to known URL) → fast-path goto
$ act browser goto https://example.com/pricing --session-id pricing

# Agent decision: Need page understanding (extract structured data) → extract
$ act browser extract "For each pricing tier, get the name, monthly price, and included features" --schema list --session-id pricing --nova-arg max_steps=30
status: success
result: [{"name": "Starter", "price": "$9/mo", "features": ["5 users", "10GB"]}, ...]
log_dir: ~/.act_cli/browser/session_logs/pricing/20260330_161005_extract/

# Agent decision: Need precise JS scroll position → evaluate with window.scrollTo
$ act browser evaluate "window.scrollTo(0, document.body.scrollHeight)" --session-id pricing

# Agent decision: Need page understanding (extract more data from bottom) → extract
$ act browser extract "What enterprise contact options are shown?" --schema string --session-id pricing --nova-arg max_steps=30
status: success
result: "Sales email: sales@example.com, Phone: 1-800-EXAMPLE, Live chat available"
log_dir: ~/.act_cli/browser/session_logs/pricing/20260330_161012_extract/
```

### Good: Localhost HTTPS Server Testing

```
# Agent decision: User has a local dev server on https://localhost:8443 with self-signed cert → need SSL bypass flags
$ act browser goto https://localhost:8443 --session-id dev --launch-arg=--ignore-certificate-errors --ignore-https-errors
status: success
transition: Navigated to localhost:8443.
log_dir: ~/.act_cli/browser/session_logs/dev/20260402_110000_goto/

# Agent decision: Multi-step objective on the local app → execute
$ act browser execute "1. Click the login button 2. Fill username 'admin' and password 'test' 3. Submit the form" --session-id dev --nova-arg max_steps=15
status: success
reached: true
transition: Logged in successfully, dashboard displayed.
log_dir: ~/.act_cli/browser/session_logs/dev/20260402_110015_execute/

# Agent decision: Need structured data from the local app → extract
$ act browser extract "List all items in the dashboard table" --schema list --session-id dev --nova-arg max_steps=15
status: success
result: [{"name": "Item 1", "status": "Active"}, ...]
log_dir: ~/.act_cli/browser/session_logs/dev/20260402_110030_extract/
```

**Key**: The `--launch-arg=--ignore-certificate-errors` and `--ignore-https-errors` flags are only needed on the **first command** that creates the session (here, `goto`). Subsequent commands in the same session inherit the browser settings. Only use these flags for **localhost** — production URLs should use valid certificates.

### Anti-Pattern: Slow-Scrolling Prompts

```bash
# ❌ Wastes inference calls — each scroll is a separate AI call
act browser execute "Scroll down slowly through the entire page to see all sections" --session-id work
act browser execute "Scroll back to the very top of the page then slowly scroll down section by section through the entire page" --session-id work
# ✅ get-content for full page text (zero inference, instant)
act browser get-content --session-id work
# ✅ scroll-to for jumping to a specific section (one targeted call)
act browser scroll-to "pricing section" --session-id work
# ✅ extract for answering a specific question about the page
act browser extract "What are the three pricing tiers and their costs?" --schema string --session-id work --nova-arg max_steps=30
# ✅ evaluate for precise scroll control via JavaScript (zero inference)
act browser evaluate "window.scrollTo(0, document.body.scrollHeight * 0.5)" --session-id work   # 50% of page
act browser evaluate "window.scrollTo(0, 0)" --session-id work                                  # top
act browser evaluate "window.scrollTo(0, document.body.scrollHeight)" --session-id work          # bottom
```
**Why this is bad**: Each scroll step is a separate inference call. Scrolling through an entire page takes minutes, costs dozens of calls, and may miss content or get stuck in infinite scroll. The agent already has faster tools for every use case that motivates slow scrolling. Use `evaluate` with `window.scrollTo()` when `scroll-to` isn't applicable (e.g., scrolling to a percentage position rather than a named section).

### Anti-Pattern: get-content for Page Observation

```bash
# ❌ Verbose — returns raw HTML/text, costs many tokens
act browser get-content --session-id kiro-explore
# ✅ Structured — returns accessibility tree summary optimized for agent consumption
act browser snapshot --session-id kiro-explore
```
**Why this is bad**: `get-content` dumps the full page as raw HTML or text — verbose, expensive in tokens, and hard to parse. `snapshot` returns a structured accessibility tree with element refs (e1, e2...), purpose-built for agent consumption. Use `get-content` only when you need the literal text content (e.g., for full-text search or archival).

### Anti-Pattern: Nova Act for Trivial Reads

```bash
# ❌ Inference for a known DOM property
act browser execute "Tell me the page title" --session-id work
# ✅ evaluate for quick known-property reads
act browser evaluate "document.title" --session-id work
```

### The Rule

Default to `execute`/`extract` for any real work. Use fast-path commands only for trivially simple single actions or targeted recovery after `execute` partially fails. Use `evaluate` only for precise scrolling or known-property reads. Use `snapshot` to observe page state between `execute`/`extract` calls.

## Common Options

Most commands share these options:

- `--session-id ID` — Target session (default: `default`)
- `--starting-page URL` — Starting URL for new sessions
- `--headed` / `--headless` — Browser visibility (default: headed). **IMPORTANT**: Always ask the user whether they want headed or headless mode before running browser commands, unless already specified.
- `--timeout N` — Timeout in seconds
- `--nova-arg KEY=VALUE` — Pass NovaAct constructor or method arguments (repeatable). Supports constructor args (`headless`, `screen_width`, `screen_height`) and method args (`max_steps`, `model_temperature`, `observation_delay_ms`).
- `--json` — JSON output mode
- `--focus "area"` — Focus command on a specific page area
- `--observe` — After command completes, describe current page layout (extra inference call)

### `--nova-arg` Examples

```bash
act browser execute "Fill out the form" --session-id myform --nova-arg max_steps=30
act browser goto https://example.com --session-id work --nova-arg headless=true --nova-arg screen_width=1920
```

### Discovering Options

Use `--help` on any command (`act browser --help`, `act browser execute --help`, `act browser session --help`). Use `act browser page --signatures` to list all Playwright page methods.

## Session Management

Sessions persist across CLI invocations via CDP. Max 5 concurrent (override with `--max-sessions N`). Sessions auto-create on first use — no need to explicitly create unless you want specific options upfront.

**Best practice**: Export session history for reproducibility: `act browser session export --session-id work --format yaml -o session_history.yaml`. The export classifies commands as `ai_command` or `playwright_operation` — useful for converting to Gherkin tests (see `gherkin_testing.md`).

### Session Reports

`act browser session export --report --output-dir ./report` — generates markdown report with screenshots, snapshots, steps, and logs.

## Configuration

Configuration precedence (highest first): CLI flags → env vars (`NOVA_ACT_HEADLESS=1`) → project config (`./.nova-act.json`) → user config (`~/.nova-act/config.json`) → defaults.

Supported browsers: Chrome, Chromium, Edge, Brave, any Chromium-based browser.

**Browser profiles**: Use `--profile <path>` to maintain cookies, extensions, and login state. Profile must exist, contain a `Preferences` file, and not be locked by another Chrome instance.

**CDP connection**: Connect to an already-running Chrome instance with `--cdp 9222` (port), `--cdp ws://localhost:9222` (WebSocket), or `--auto-connect` (auto-discover). Start Chrome with: `google-chrome --remote-debugging-port=9222`

## Related Files
- `authentication.md` — API key vs IAM setup
- `data_extraction.md` — Structured extraction with Pydantic schemas
- `qa_tests.md` — Writing Nova Act tests with pytest
- `deployment_cli.md` — Deploy workflows to AgentCore Runtime
- `gherkin_testing.md` — Gherkin-to-CLI pipeline and session export conversion
- `flow_discovery.md` — Live app exploration → codebase mapping
- `bug_reproduction.md` — Reproduce → evidence → regression test
