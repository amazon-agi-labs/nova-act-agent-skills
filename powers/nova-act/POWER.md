---
name: "nova-act"
displayName: "Amazon Nova Act Browser Automation"
description: "AI-powered browser automation SDK for web scraping, testing, and workflow automation. Use when automating web browsers, extracting data from websites, testing web applications, or building web automation workflows. Supports both API key and AWS credential authentication."
author: "Amazon"
keywords: ["browser", "automation", "web", "scraping", "testing", "playwright", "selenium", "nova", "act", "aws", "amazon", "workflow", "bot"]
---

# Onboarding

**Official Documentation:** [Nova Act GitHub README](https://github.com/aws/nova-act/blob/main/README.md) is the source of truth.

## Step 1: Authentication Setup

Nova Act supports two authentication methods. **You MUST prompt the user for which method they want to use!**

- **API Key (Quick Start)** — Best for development/testing. Generate at https://nova.amazon.com/act?tab=dev_tools, then `export NOVA_ACT_API_KEY="your_key"`. No decorator needed.
- **AWS Credentials + Workflow Definition (Production)** — Best for IAM-based access, S3 export. Requires AWS creds + `@workflow` decorator. See `steering/workflow_definitions.md`.

Full setup details: `steering/authentication.md`

## Step 2: Start Using Nova Act

**Route to the right mode:**

| User wants to... | Route to |
|-------------------|----------|
| Explore a website interactively | `steering/browser_cli.md` (Option A) |
| Build a coding agent with browser | `steering/browser_cli.md` (Option A) |
| Write a repeatable test script | `steering/qa_tests.md` (Option B) |
| Write a Python automation script | `steering/qa_tests.md` (Option B) + `steering/data_extraction.md` |
| Convert manual tests to automated | `steering/gherkin_testing.md` |
| Understand a codebase via its UI | `steering/flow_discovery.md` |
| Reproduce a bug | `steering/bug_reproduction.md` |
| Deploy to production | `steering/deployment_cli.md` |

**Option A: Browser CLI (recommended for exploration and agent tool-use)**
```bash
pip install 'nova-act[cli]'
act browser execute "Go to https://example.com, find the pricing page, and extract plan names and prices" --session-id work
# If you need to observe current state:
act browser ask "What page am I on?" --session-id work
# If you need a zero-inference jump:
act browser goto https://example.com/specific-page --session-id work
```
Default to `execute` with a detailed plan. Use individual commands (`goto`, `ask`, etc.) for recovery, observation, or zero-inference actions. Pass NovaAct constructor or method args with `--nova-arg`: e.g. `--nova-arg max_steps=5 --nova-arg headless=true`. Run any command with `--help` for all available options.

> **IMPORTANT**: Before running any browser command, ask the user whether they want headed (visible browser) or headless mode, unless they have already specified. Use `--headed` or `--headless` accordingly.

> ⚠️ **CRITICAL: NEVER kill Chrome or Chromium processes** (e.g., `pkill chrome`, `kill -9 $(pgrep chrome)`, `killall Google Chrome`). Nova Act manages its own browser lifecycle. Killing browser processes externally will corrupt session state and break automation. If a browser appears stuck, use `act browser sessions` to check status, or start a new session.

> 💡 **Localhost HTTPS Testing**: When testing against a local HTTPS server (e.g., `https://localhost:8443`), Chrome will reject self-signed certificates by default. Add `--launch-arg=--ignore-certificate-errors --ignore-https-errors` to bypass this:
> ```bash
> act browser goto https://localhost:8443 --session-id dev --launch-arg=--ignore-certificate-errors --ignore-https-errors
> ```
> ⚠️ Only use `--ignore-certificate-errors` for **localhost** development servers. For non-local URLs, valid certificates should be used unless you have a specific reason to bypass validation.

Full command reference: `steering/browser_cli.md`

**Option B: Python Script (recommended for repeatable automation)**
```python
from nova_act import NovaAct

with NovaAct(starting_page="https://example.com") as nova:
    nova.act("click the first link on the page")
    result = nova.act_get("What is the page title?")
    print(f"Page title: {result.response}")
```
Full testing guide: `steering/qa_tests.md`

## Step 3: Validate Installation
- **Python 3.10+**: `python --version`
- **Nova Act SDK**: `pip install 'nova-act[cli]'` / `pip show nova-act`
- **Google Chrome (Optional)**: `playwright install chrome`

# Steering Files

**Quickstart:** When given a URL to explore or automate, start with `steering/browser_cli.md`.

| File | What It Covers |
|------|---------------|
| `steering/browser_cli.md` | **Browser CLI** — commands, sessions, config, page exploration. Default for interactive work and agent tool-use. **You MUST read the ENTIRE file** — it contains critical CLI best practices, command decision guides, and example transcripts that are essential for correct usage |
| `steering/qa_tests.md` | **Script writing** — QA testing with pytest/unittest, act() vs act_get(), schemas, assertion patterns |
| `steering/deployment_cli.md` | **Deployment CLI** — deploy workflows to AgentCore Runtime on AWS |
| `steering/authentication.md` | API key vs IAM, session management |
| `steering/workflow_definitions.md` | Workflow definitions with AWS CLI |
| `steering/data_extraction.md` | Structured extraction with Pydantic |
| `steering/hitl.md` | Human approval and UI takeover patterns |
| `steering/tool_use.md` | External tools (@tool decorator, MCP servers) |
| `steering/agentcore_browser.md` | Remote browser via AgentCore |
| `steering/playwright_interop.md` | Direct Playwright page access, sensitive input, file downloads |
| `steering/session_logs.md` | Logs, screenshots, and video recordings |
| `steering/trajectory_analysis.md` | Understanding Nova Act trajectories |
| `steering/visual_reporting.md` | Visual reporting — post-session markdown reports from steps.yaml, snapshots, and screenshots |
| `steering/gherkin_testing.md` | **Gherkin testing** — `.feature` file writing, `qa-plan` compilation, session export → Gherkin conversion |
| `steering/flow_discovery.md` | **Flow discovery** — live app exploration → codebase mapping, developer onboarding docs |
| `steering/bug_reproduction.md` | **Bug reproduction** — reproduce → capture evidence → export → regression test |

This power uses the Nova Act SDK which is licensed under the Apache-2.0 license.
