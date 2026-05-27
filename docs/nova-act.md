# Nova Act Skill

Browser automation skill for [Amazon Nova Act](https://github.com/aws/nova-act). Covers interactive browsing, data extraction, QA testing, workflow automation, and more.

## Prerequisites

- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/) or `pip`
- A Nova Act API key ([get one here](https://nova.amazon.com/act)) **or** [AWS IAM credentials](https://docs.aws.amazon.com/nova-act/latest/userguide/step-2-develop-locally.html)

## Installation

Install with the [skills CLI](https://github.com/vercel-labs/skills):

```bash
npx skills@latest add amazon-agi-labs/nova-act-agent-skills
```

Or copy `skills/nova-act/` into your agent's skills directory:

```bash
# Kiro (global)
cp -r skills/nova-act/ ~/.kiro/skills/nova-act/

# Kiro (project-level)
cp -r skills/nova-act/ .kiro/skills/nova-act/

# Claude Code
cp -r skills/nova-act/ .claude/skills/nova-act/
```

## Authentication

Nova Act supports two authentication methods:

| Mode | Env Vars | Use Case |
|------|----------|----------|
| API Key | `NOVA_ACT_API_KEY` | Development and testing. Get a key at [nova.amazon.com/act](https://nova.amazon.com/act) |
| AWS IAM | `AWS_PROFILE` + `AWS_REGION` + `NOVA_ACT_WORKFLOW_DEFINITION_NAME` | Production, IAM-based access, S3 export |

API key takes priority if both are set.

## Usage Modes

### Interactive Browsing (Browser CLI)

Best for exploration, agent tool-use, and ad-hoc automation:

```bash
pip install 'nova-act[cli]'
act browser execute "Go to https://example.com and extract the page title" --session-id work
```

Use `--headed` for a visible browser window or `--headless` (default) for background execution.

### QA Testing

Write repeatable test scripts using Nova Act's Python SDK:

```python
from nova_act import NovaAct

with NovaAct(starting_url="https://example.com") as nova:
    nova.act("Click the login button")
    nova.act("Enter 'test@example.com' in the email field")
    result = nova.act("What is the page title?", schema={"title": str})
    assert result.parsed_response["title"] == "Dashboard"
```

### Data Extraction

Extract structured data from websites:

```python
from nova_act import NovaAct

with NovaAct(starting_url="https://example.com/products") as nova:
    result = nova.act(
        "Extract all product names and prices from this page",
        schema={"products": [{"name": str, "price": str}]}
    )
    products = result.parsed_response["products"]
```

### Gherkin Test Conversion

Convert manual test cases written in Gherkin into automated Nova Act scripts. The skill translates Given/When/Then steps into browser actions.

## Capabilities

The skill includes reference documents covering:

| Topic | Reference File |
|-------|---------------|
| Authentication setup | `references/authentication.md` |
| Browser CLI commands | `references/browser_cli.md` |
| Data extraction patterns | `references/data_extraction.md` |
| QA test patterns | `references/qa_tests.md` |
| Gherkin test conversion | `references/gherkin_testing.md` |
| Flow discovery | `references/flow_discovery.md` |
| Bug reproduction | `references/bug_reproduction.md` |
| Workflow refinement | `references/workflow_refinement.md` |
| Mock generation | `references/mock_generation.md` |
| Parallel sessions | `references/parallel_sessions.md` |
| Playwright interop | `references/playwright_interop.md` |
| Session logs and observability | `references/session_logs.md` |
| Trajectory analysis | `references/trajectory_analysis.md` |
| Deployment | `references/deployment_cli.md` |
| AgentCore cloud browsers | `references/agentcore_browser.md` |
| Human-in-the-loop patterns | `references/hitl.md` |
| Workflow definitions | `references/workflow_definitions.md` |

## MCP Server

The skill works with the [amazon-nova-act-mcp](https://github.com/amazon-agi-labs/amazon-nova-act-mcp) server, which exposes Nova Act as MCP tools (`start_browse`, `act`, `act_get`, `go_to_url`, `screenshot`, etc.).

Configure in your MCP settings:

```json
{
  "mcpServers": {
    "nova-act-mcp": {
      "command": "uvx",
      "args": ["amazon-nova-act-mcp"],
      "env": {
        "NOVA_ACT_API_KEY": "${NOVA_ACT_API_KEY}"
      }
    }
  }
}
```

## Links

- [Nova Act SDK](https://github.com/aws/nova-act)
- [Nova Act Documentation](https://docs.aws.amazon.com/nova-act/latest/userguide/what-is-nova-act.html)
- [Nova Act MCP Server](https://github.com/amazon-agi-labs/amazon-nova-act-mcp)
- [API Key](https://nova.amazon.com/act)
