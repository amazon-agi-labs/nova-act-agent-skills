# Setup

## MCP Server

The verification tools are provided by the Nova Act MCP server. It must be running and connected to your agent.

### Kiro

Add to `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "nova-act-mcp": {
      "command": "amazon-nova-act-mcp",
      "args": ["--toolsets", "ui-verification"],
      "env": {
        "NOVA_ACT_WORKFLOW_DEFINITION_NAME": "<your-workflow-definition>",
        "AWS_REGION": "us-east-1"
      }
    }
  }
}
```

### Claude Code

Add to `.claude/settings.json` (project-level) or `~/.claude/settings.json` (global):

```json
{
  "mcpServers": {
    "nova-act-mcp": {
      "command": "amazon-nova-act-mcp",
      "args": ["--toolsets", "ui-verification"],
      "env": {
        "NOVA_ACT_WORKFLOW_DEFINITION_NAME": "<your-workflow-definition>",
        "AWS_REGION": "us-east-1"
      }
    }
  }
}
```

> **Important:** The `--toolsets ui-verification` argument is required. Without it, the server starts without the `verify_*` tools and verification calls will fail with "tool not found".

### Authentication

The server supports two auth modes (auto-detected at startup):

| Mode | Env Var | Use Case |
|---|---|---|
| API Key | `NOVA_ACT_API_KEY` | Development/testing |
| IAM / AWS | `AWS_PROFILE` + `AWS_REGION` + `NOVA_ACT_WORKFLOW_DEFINITION_NAME` | Production, AWS account |

API key takes priority if both are set.

## Starting a Browser Session

All verification requires a browser session with a live DOM. **You MUST pass `browser_mode="local"`** — the default `"any"` mode tries HTTP first and may return `session_id=None` (no browser, no DOM, no verification possible).

```
start_browse(url="https://your-site.com", intent="verify visual design", browser_mode="local")
```

**Parameters:**
- `url` — the page to verify
- `intent` — description of what you're doing
- `browser_mode` — **required for verification**. Use one of:
  - `"local"` — local headless browser (**use this for verification**)
  - `"local_headed"` — local browser with visible window (debugging)
  - `"local_system_default"` — local browser with Chrome profile (for authenticated sites)
  - `"agentcore"` — cloud browser with anti-bot bypass
  - `"any"` (default, DO NOT USE for verification) — tries HTTP first, may skip browser entirely

**Returns:**
- `status` — `"ok"` or `"error"`
- `session_id` — use this in all subsequent tool calls. **Will be `None` if no browser was created** (only happens with `browser_mode="any"` when HTTP fetch succeeds).
- `content` — page text content
- `method` — `"http_fetch"` or `"browser"`
- `final_url` — the URL after any redirects

**Important:** Always check that `session_id` is not `None` before calling verify_* tools. If it is, call `start_browse` again with `browser_mode="local"`.

## Session Lifecycle

```
start_browse(url, intent, browser_mode="local")
  → session_id

verify_visual_style(session_id, rules, output_dir)
verify_components(session_id, rules, output_dir)
navigate(session_id, next_url)
verify_accessibility(session_id, rules, output_dir)
...

session_close(session_id)
```

Each run is independent. Always close sessions when done. Sessions auto-expire after 30 minutes of inactivity. Cross-session warm-start is out of scope for now — focus on producing a complete report per run.

## Artifact Output

Verification results are written to:

```
<output_dir>/.ui-verification/sessions/<session_id>/<category>_assertions.json
```

Where:
- `<output_dir>` — **absolute path to the project root** (the directory that contains `.ui-verification/specs/`). Always pass this. If omitted, the server falls back to a `/tmp/ui-verification-*` temp dir and downstream report/annotation steps cannot find the artifacts.
- `<session_id>` — the browser session ID
- `<category>` — one of: `visual_style`, `component_rules`, `accessibility`, `project_rules`, `platform_conventions`

Example call:

```
verify_visual_style(session_id="abc123", rules="[...]", output_dir="/Users/you/my-project")
```

Writes to `/Users/you/my-project/.ui-verification/sessions/abc123/visual_style_assertions.json`.

The same `output_dir` is also used as the base for screenshot destinations and the test report — resolve it once at the start of a verification run and reuse for every artifact-writing call.

## After Setup

Setup ends after `start_browse` returns a `session_id`. The full verification workflow (compile → verify → annotate → report → close) is in `references/verification.md`. Multi-page navigation, scrolling, and per-category guidance are documented there and in the per-category `verify_*.md` deep-dives.
