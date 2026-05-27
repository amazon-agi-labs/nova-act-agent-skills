# UI Verification Skill

Generation is nearly instant. Validation is still manual and slow. You get a full application in 60 seconds and spend the next three hours checking if it actually matches what you intended.

The UI Verification skill collapses this gap. It lets the agent check its own work against what was designed, running deterministic CSS checks against the live DOM for visual accuracy, and executing user flows end-to-end for functional correctness. Generation and validation become one continuous loop without requiring repeated manual intervention.

The skill spins up the rendered application and runs verification automatically. Deterministic checks read computed CSS directly from the DOM and catch visual deviations immediately without AI involvement. Behavioral checks follow, the agent walks user flows via [Nova Act](https://aws.amazon.com/nova/act/), interacting with the application the way a human tester would to catch functional regressions.

## What's Included

```
skills/ui-verification/
├── SKILL.md              # Main skill definition
├── references/           # Detailed reference documents
│   ├── verification.md       # Visual verification workflow
│   ├── flow_verification.md  # Flow verification workflow
│   ├── setup.md              # MCP server + browser setup
│   ├── spec_generation.md    # Generate visual specs from a live site
│   ├── flow_generation.md    # Generate flows from a live site
│   ├── spec_sync.md          # Compile design.md → category files
│   ├── flow_sync.md          # Sync chat → .feature files
│   ├── spec_authoring.md     # How to write design specs
│   ├── flow_authoring.md     # How to write .feature files
│   ├── constraint_reference.md   # Constraint syntax (visual)
│   ├── warm_start.md            # Incremental verification (deferred)
│   ├── verification_report.md   # Combined visual + flow report format
│   ├── annotate_failures.md     # Annotate visual failures on the page
│   ├── verify_visual_style.md   # Deep-dive: colors, typography, spacing
│   ├── verify_components.md     # Deep-dive: component presence/variants
│   ├── verify_accessibility.md  # Deep-dive: roles, landmarks, headings
│   ├── verify_project_rules.md  # Deep-dive: layout, conventions
│   └── verify_platform_conventions.md  # Deep-dive: nav, page structure
└── README.md
```

## Prerequisites

- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/) — install with `curl -LsSf https://astral.sh/uv/install.sh | sh`
- A Nova Act API key ([get one here](https://nova.amazon.com/act)) **or** [AWS IAM credentials](https://docs.aws.amazon.com/nova-act/latest/userguide/step-2-develop-locally.html)

## Installation

### 1. Install the MCP server

The skill requires the [amazon-nova-act-mcp](https://github.com/amazon-agi-labs/amazon-nova-act-mcp) server. The recommended way to run it is with `uvx`, which downloads and runs the server from PyPI without a separate install step:

```bash
uvx amazon-nova-act-mcp --configure
```

This launches the setup wizard which prompts for credentials and writes the MCP client config automatically.

For AWS/IAM auth with AgentCore cloud browsers:

```bash
uvx amazon-nova-act-mcp --configure-aws
```

Alternatively, install via pip in a virtual environment:

```bash
pip install amazon-nova-act-mcp
amazon-nova-act-mcp --configure
```

### 2. Install the skill

**Option A — Copy from this repo:**

```bash
# Kiro (global)
cp -r skills/ui-verification/ ~/.kiro/skills/ui-verification/

# Kiro (project-level)
cp -r skills/ui-verification/ /path/to/your-project/.kiro/skills/ui-verification/

# Claude Code
cp -r skills/ui-verification/ /path/to/your-project/.claude/skills/ui-verification/
```

**Option B — From the published repo:**

```bash
git clone https://github.com/amazon-agi-labs/nova-act-agent-skills.git
cp -r nova-act-agent-skills/skills/ui-verification/ ~/.kiro/skills/ui-verification/
```

### 3. Configure the MCP server

If you ran `--configure` or `--configure-aws` above and selected Kiro or Claude as your client, you're already set. You still need to enable the verification toolset — the `verify_*` tools are opt-in and not enabled by default.

To enable, add `--toolsets ui-verification` when starting the server:

```bash
amazon-nova-act-mcp --toolsets ui-verification
```

**Kiro** — `~/.kiro/settings/mcp.json` (global) or `.kiro/settings/mcp.json` (project):

```json
{
  "mcpServers": {
    "nova-act-mcp": {
      "command": "uvx",
      "args": ["amazon-nova-act-mcp", "--toolsets", "ui-verification"],
      "env": {
        "NOVA_ACT_API_KEY": "${NOVA_ACT_API_KEY}"
      }
    }
  }
}
```

**Claude Code** — `~/.claude.json` (user scope) or `.mcp.json` (project scope):

```json
{
  "mcpServers": {
    "nova-act-mcp": {
      "command": "uvx",
      "args": ["amazon-nova-act-mcp", "--toolsets", "ui-verification"],
      "env": {
        "NOVA_ACT_API_KEY": "${NOVA_ACT_API_KEY}"
      }
    }
  }
}
```

### 4. Authentication

| Mode | Env Vars | Use Case |
|------|----------|----------|
| API Key | `NOVA_ACT_API_KEY` | Development/testing — get a key at [nova.amazon.com/act](https://nova.amazon.com/act) |
| IAM / AWS | `AWS_PROFILE` + `AWS_REGION` + `NOVA_ACT_WORKFLOW_DEFINITION_NAME` | Production, AWS account |

API key takes priority if both are set.

## Usage

Once installed, ask your agent to verify a site against its design spec or its user flows.

### Visual Verification

> "Verify https://my-site.com matches the design spec"

The agent will:
1. Open a browser session against your site
2. Read spec files from `.ui-verification/specs/` (or generate them if none exist)
3. Translate each spec claim into a CSS rule check
4. Run deterministic `getComputedStyle()` checks against the live DOM
5. Report pass/fail per rule, with structured artifact output

### Flow Verification

> "Run flows on https://my-site.com"

The agent will:
1. Open a browser session against your site
2. Read `.feature` files from `.ui-verification/flows/` (or generate baseline flows if none exist)
3. Execute each scenario step-by-step via Nova Act's `act()` (actions) and `act_get()` (assertions)
4. Run cleanup if declared, regardless of pass/fail
5. Write a per-flow report and roll results into the combined verification report

### Combined

> "Verify https://my-site.com"

If the user gives a URL with no further qualifier, both modes run. Visual first, then flow, into one combined `report.md` under `reports/<run-timestamp>/`.

## Inputs and Outputs

**Visual inputs:**
- `design.md` — your hand-authored design spec (prose + YAML tokens)
- `.ui-verification/specs/` — five compiled category files derived from `design.md` (skill writes these)

**Flow inputs:**
- `.ui-verification/flows/<flow-name>.feature` — Gherkin scenarios with metadata header

**Outputs (per run):**
- `.ui-verification/reports/<run-timestamp>/report.md` — combined visual + flow report
- `.ui-verification/reports/<run-timestamp>/flow-reports/<flow-name>.report.md` — per-flow detail
- `.ui-verification/reports/<run-timestamp>/screenshots/<category>.png` — annotated visual failures
- `.ui-verification/reports/<run-timestamp>/sessions.json` — manifest of session IDs

```
<project_root>/
  visual/design.md                         ← visual source spec (you author)
  .ui-verification/
    specs/                                 ← compiled visual rules (skill writes)
      visual-style.md
      component-rules.md
      accessibility.md
      project-rules.md
      platform-conventions.md
    flows/                                 ← flow scenarios (authored or generated)
      <flow-name>.feature
    sessions/                              ← per-session output (MCP-owned)
      <session_id>/
    reports/                               ← per-run output (skill-owned)
      <run-timestamp>/
        report.md
        flow-reports/<flow-name>.report.md
        screenshots/
        sessions.json
```

If no `design.md` exists, the skill can generate one by observing the live site. If no `.feature` files exist, the skill can generate baseline flows from a one-level-deep crawl.

## MCP Tools Available

The skill uses these tools from the `nova-act-mcp` server:

| Tool | Purpose |
|------|---------|
| `start_browse` | Entry point — fast HTTP fetch first, opens browser if needed |
| `act` | Execute browser actions via natural language |
| `act_get` | Execute + extract data (text or structured JSON) |
| `go_to_url` | Navigate directly to a URL |
| `get_page_content` | Get page content as text or HTML |
| `screenshot` | Capture screenshot |
| `session_close` | Terminate browser session |
| `verify_visual_style` | Run visual style CSS checks |
| `verify_components` | Run component presence/variant checks |
| `verify_accessibility` | Run accessibility checks |
| `verify_project_rules` | Run project convention checks |
| `verify_platform_conventions` | Run platform pattern checks |

## Links

- **MCP Server:** [amazon-agi-labs/amazon-nova-act-mcp](https://github.com/amazon-agi-labs/amazon-nova-act-mcp)
- **Skills Repo:** [amazon-agi-labs/nova-act-agent-skills](https://github.com/amazon-agi-labs/nova-act-agent-skills/tree/main/skills)
- **Nova Act:** [aws.amazon.com/nova/act](https://aws.amazon.com/nova/act/)
- **API Key:** [nova.amazon.com/act](https://nova.amazon.com/act)
