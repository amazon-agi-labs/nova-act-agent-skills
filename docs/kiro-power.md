# Nova Act Kiro Power

A [Kiro power](https://kiro.dev/docs/powers/) that brings Nova Act browser automation directly into the Kiro IDE. Tests your application like a human would, then turns your testing into natural language QA workflows.

## Prerequisites

- [Kiro IDE](https://kiro.dev)
- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/) (recommended) or `pip`
- A Nova Act API key ([get one here](https://nova.amazon.com/act)) **or** [AWS IAM credentials](https://docs.aws.amazon.com/nova-act/latest/userguide/step-2-develop-locally.html)

## Installation

1. Open [Kiro](https://kiro.dev)
2. Click the lightning bolt icon in the sidebar
3. Select **Add Custom Power**
4. Point to the `powers/nova-act/` directory in this repository
5. The power will appear in your powers list

## Authentication

Nova Act supports two authentication methods:

| Mode | Env Vars | Use Case |
|------|----------|----------|
| API Key | `NOVA_ACT_API_KEY` | Development and testing. Get a key at [nova.amazon.com/act](https://nova.amazon.com/act) |
| AWS IAM | `AWS_PROFILE` + `AWS_REGION` + `NOVA_ACT_WORKFLOW_DEFINITION_NAME` | Production, IAM-based access, S3 export |

API key takes priority if both are set.

## Usage Modes

The power routes you to the right workflow based on what you're trying to do:

| You want to... | Steering file |
|----------------|---------------|
| Explore a website interactively | `steering/browser_cli.md` |
| Build a coding agent with browser access | `steering/browser_cli.md` |
| Write a repeatable test script | `steering/qa_tests.md` |
| Write a Python automation script | `steering/qa_tests.md` + `steering/data_extraction.md` |
| Convert manual tests to automated | `steering/gherkin_testing.md` |
| Understand a codebase via its UI | `steering/flow_discovery.md` |
| Reproduce a bug | `steering/bug_reproduction.md` |
| Iterate on automation prompts | `steering/workflow_refinement.md` |
| Generate mock sites from recordings | `steering/mock_generation.md` |
| Deploy to production | `steering/deployment_cli.md` |

## Browser CLI

The power uses Nova Act's CLI for browser interaction:

```bash
pip install 'nova-act[cli]'

# Execute a task
act browser execute "Go to https://example.com and find the pricing page" --session-id work

# Ask about current state
act browser ask "What page am I on?" --session-id work

# Navigate directly
act browser goto https://example.com/specific-page --session-id work
```

Use `--headed` for a visible browser window. Use `--headless` (default) for background execution.

## MCP Server Integration

The power works alongside the [amazon-nova-act-mcp](https://github.com/amazon-agi-labs/amazon-nova-act-mcp) server, which exposes Nova Act as MCP tools within Kiro:

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

## Steering Documents

The power includes steering files that provide detailed guidance for specific workflows:

| Topic | File |
|-------|------|
| Authentication setup | `steering/authentication.md` |
| Browser CLI reference | `steering/browser_cli.md` |
| Data extraction patterns | `steering/data_extraction.md` |
| QA test patterns | `steering/qa_tests.md` |
| Gherkin test conversion | `steering/gherkin_testing.md` |
| Flow discovery | `steering/flow_discovery.md` |
| Bug reproduction | `steering/bug_reproduction.md` |
| Workflow refinement | `steering/workflow_refinement.md` |
| Mock generation | `steering/mock_generation.md` |
| Parallel sessions | `steering/parallel_sessions.md` |
| Playwright interop | `steering/playwright_interop.md` |
| Session logs | `steering/session_logs.md` |
| Trajectory analysis | `steering/trajectory_analysis.md` |
| Deployment | `steering/deployment_cli.md` |
| AgentCore cloud browsers | `steering/agentcore_browser.md` |
| Human-in-the-loop | `steering/hitl.md` |
| Workflow definitions | `steering/workflow_definitions.md` |
| Visual reporting | `steering/visual_reporting.md` |
| Tool use patterns | `steering/tool_use.md` |

## Difference from the Agent Skill

The Kiro Power and the Agent Skill (`skills/nova-act/`) contain the same core content. The difference is packaging:

- **Power** (`powers/nova-act/`): Uses `POWER.md` + `steering/` directory. Designed for Kiro's power system.
- **Skill** (`skills/nova-act/`): Uses `SKILL.md` + `references/` directory. Follows the [Agent Skills](https://agentskills.io) specification for broader client compatibility.

Choose the power if you're using Kiro. Choose the skill if you're using Claude Code, Codex, or another agent that supports the agentskills.io format.

## Links

- [Kiro IDE](https://kiro.dev)
- [Kiro Powers Documentation](https://kiro.dev/docs/powers/)
- [Nova Act SDK](https://github.com/aws/nova-act)
- [Nova Act MCP Server](https://github.com/amazon-agi-labs/amazon-nova-act-mcp)
- [API Key](https://nova.amazon.com/act)
