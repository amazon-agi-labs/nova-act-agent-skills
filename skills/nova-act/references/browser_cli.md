# Nova Act Browser CLI

The browser CLI (`act browser`) is the preferred way for coding agents to interact with web browsers. It provides persistent sessions, structured output, and composable commands that work naturally in tool-use workflows.

## Setup

```bash
pip install 'nova-act[cli]'
act browser setup                        # Store API key in ~/.nova-act-cli/config
act browser setup --api-key <your-key>   # Non-interactive
# OR set env: export NOVA_ACT_API_KEY="your_key"
```

## Commands

### Browsing Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `execute` | General browser automation via natural language | `act browser execute "Click the login button"` |
| `navigate` | Go to URL with verification (retries up to 3x) | `act browser navigate https://example.com` |
| `goto` | Raw Playwright navigation (no inference) | `act browser goto https://example.com` |
| `explore` | Multi-step structured page investigation | `act browser explore --focus "pricing"` |
| `ask` | Read-only question about the page (no interaction) | `act browser ask "What is the main heading?"` |
| `search` | Find content using site search or page scanning | `act browser search "return policy"` |
| `fill-form` | Natural language form filling | `act browser fill-form "name: John, email: j@test.com" --submit` |
| `verify` | Assert a condition on the page | `act browser verify "the user is logged in"` |
| `wait-for` | Poll until a condition is met | `act browser wait-for "results are visible" --timeout 60` |

### Extraction Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `extract` | Extract structured data with optional schema | `act browser extract "Get all prices" --schema bool` |
| `get-content` | Dump page content to file | `act browser get-content --format markdown -o page.md` |
| `screenshot` | Capture screenshot | `act browser screenshot --full-page -o page.png` |
| `diff` | Before/after comparison of an action | `act browser diff "Click submit" --focus "the cart"` |
| `query` | CSS selector query → JSON | `act browser query "a[href]" --properties tag,text` |
| `style` | Computed CSS properties | `act browser style "div.header" color font-size` |
| `evaluate` | Run JavaScript in page context | `act browser evaluate "document.title"` |

### Session Commands

```bash
act browser session list                    # List active sessions
act browser session create <url>            # Create named session
act browser session close --session-id ID   # Close specific session
act browser session close-all               # Close all sessions
act browser session prune [--dry-run]       # Clean up stale sessions (24h+ inactive)
```

## Command Decision Guide

- Known URL → `goto`
- Describe where to go → `navigate`
- Page overview → `explore`
- Read-only question → `ask`
- Structured data → `extract --schema`
- Fill a form → `fill-form`
- Assert condition → `verify`
- Wait for state → `wait-for`
- Any other action → `execute`

## Common Options

Most commands share these options:

- `--session-id ID` — Target session (default: `default`)
- `--starting-page URL` — Starting URL for new sessions
- `--headed` / `--headless` — Browser visibility (default: headed)
- `--timeout N` — Timeout in seconds
- `--nova-arg KEY=VALUE` — Pass NovaAct constructor or method arguments (repeatable). Supports constructor args (`headless`, `screen_width`, `screen_height`) and method args (`max_steps`, `model_temperature`, `observation_delay_ms`).
- `--json` — JSON output mode
- `--focus "area"` — Focus command on a specific page area

### `--nova-arg` Examples

```bash
# Limit steps for a complex action
act browser execute "Fill out the entire form" --nova-arg max_steps=15

# Run headless with custom screen size
act browser navigate https://example.com --nova-arg headless=true --nova-arg screen_width=1920

# Pass API key explicitly
act browser execute "Click login" --nova-arg nova_act_api_key=your_key

# Ignore HTTPS certificate errors (e.g. self-signed certs in dev/staging)
act browser navigate https://staging.internal.example.com --nova-arg ignore_https_errors=true
```

### Discovering Options

Run any command with `--help` to see all available flags and arguments:

```bash
act browser --help              # List all browser subcommands
act browser execute --help      # Options for execute command
act browser session --help      # Session management subcommands
```

## Session Management

Sessions persist across CLI invocations via Chrome DevTools Protocol (CDP). Max 5 concurrent sessions (override with `--max-sessions N`).

```bash
# Typical workflow
act browser navigate https://example.com --session-id work
act browser execute "Click the login button" --session-id work
act browser screenshot --session-id work -o login.png
act browser session close --session-id work
```

Sessions auto-create on first use. No need to explicitly create unless you want to set specific options upfront.

## Configuration

Configuration sources (highest to lowest precedence):

1. CLI flags (`--headed`, `--executable-path`)
2. Environment variables (`NOVA_ACT_HEADLESS=1`, `NOVA_ACT_EXECUTABLE_PATH`)
3. Project config (`./.nova-act.json`)
4. User config (`~/.nova-act/config.json`)
5. Defaults

```json
// ~/.nova-act/config.json
{
  "executable_path": "/path/to/chrome",
  "headless": false
}
```

Supported browsers: Chrome, Chromium, Edge, Brave, any Chromium-based browser.

## Browser Profiles

Use existing Chrome profiles to maintain cookies, extensions, and login state:

```bash
act browser navigate https://example.com --profile ~/Library/Application\ Support/Google/Chrome/Default
```

Profile must exist, contain a `Preferences` file, and not be locked by another Chrome instance.

## CDP Connection

Connect to an already-running Chrome instance:

```bash
# By port
act browser navigate https://example.com --cdp 9222

# By WebSocket URL
act browser navigate https://example.com --cdp ws://localhost:9222

# Auto-discover running Chrome
act browser navigate https://example.com --auto-connect
```

Start Chrome with remote debugging: `google-chrome --remote-debugging-port=9222`

## Page Exploration Workflow

When given a URL to explore with no other context, follow this workflow:

### 1. Navigate and discover
```bash
act browser navigate <URL> --session-id explore --headed
act browser explore --session-id explore
```

### 2. Drill into specific areas
```bash
act browser explore --focus "navigation menu" --session-id explore
act browser ask "What workflows can a user perform on this page?" --session-id explore
act browser extract "What are the main sections and their purposes?" --session-id explore
```

### 3. Follow interesting paths
```bash
act browser execute "Click on the [section name] tab" --session-id explore
act browser explore --session-id explore
act browser screenshot --session-id explore -o section.png
```

### 4. Ask the user for direction
After each discovery phase:
- "I found [X sections]. Which should I explore first?"
- "Breadth (check all tabs) or depth (follow this workflow end-to-end)?"

### 5. Clean up
```bash
act browser session close --session-id explore
```

## Related Files
- `authentication.md` — API key vs IAM setup
- `data_extraction.md` — Structured extraction with Pydantic schemas
- `qa_tests.md` — Writing Nova Act tests with pytest
- `deployment_cli.md` — Deploy workflows to AgentCore Runtime
