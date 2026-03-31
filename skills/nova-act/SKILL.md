---
name: nova-act
description: AI-powered browser automation SDK for web scraping, testing, and workflow automation. Use when automating web browsers, extracting data from websites, testing web applications, or building web automation workflows. Supports both API key and AWS credential authentication.
license: Apache-2.0
metadata:
  displayName: Amazon Nova Act Browser Automation
  keywords: browser, automation, web, scraping, testing, playwright, selenium, nova, act, aws, amazon, workflow, bot
---

# Onboarding

**Official Documentation:** [Nova Act GitHub README](https://github.com/aws/nova-act/blob/main/README.md) is the source of truth.

## Step 1: Authentication Setup

Nova Act supports two authentication methods. **You MUST prompt the user for which method they want to use!**

- **API Key (Quick Start)** — Best for development/testing. Generate at https://nova.amazon.com/act?tab=dev_tools, then `export NOVA_ACT_API_KEY="your_key"`. No decorator needed.
- **AWS Credentials + Workflow Definition (Production)** — Best for IAM-based access, S3 export. Requires AWS creds + `@workflow` decorator. See `references/workflow_definitions.md`.

Full setup details: `references/authentication.md`

## Step 2: Start Using Nova Act

**Route to the right mode:**

| User wants to... | Route to |
|-------------------|----------|
| Explore a website interactively | `references/browser_cli.md` (Option A) |
| Build a coding agent with browser | `references/browser_cli.md` (Option A) |
| Write a repeatable test script | `references/qa_tests.md` (Option B) |
| Write a Python automation script | `references/qa_tests.md` (Option B) + `references/data_extraction.md` |
| Convert manual tests to automated | `references/gherkin_testing.md` |
| Understand a codebase via its UI | `references/flow_discovery.md` |
| Reproduce a bug | `references/bug_reproduction.md` |
| Deploy to production | `references/deployment_cli.md` |

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

Full command reference: `references/browser_cli.md`

**Option B: Python Script (recommended for repeatable automation)**
```python
from nova_act import NovaAct

with NovaAct(starting_page="https://example.com") as nova:
    nova.act("click the first link on the page")
    result = nova.act_get("What is the page title?")
    print(f"Page title: {result.response}")
```
Full testing guide: `references/qa_tests.md`

## Step 3: Validate Installation
- **Python 3.10+**: `python --version`
- **Nova Act SDK**: `pip install 'nova-act[cli]'` / `pip show nova-act`
- **Google Chrome (Optional)**: `playwright install chrome`

# Steering Files

**Quickstart:** When given a URL to explore or automate, start with `references/browser_cli.md`.

| File | What It Covers |
|------|---------------|
| `references/browser_cli.md` | **Browser CLI** — commands, sessions, config, page exploration. Default for interactive work and agent tool-use. **You MUST read the ENTIRE file** — it contains critical CLI best practices, command decision guides, and example transcripts that are essential for correct usage |
| `references/qa_tests.md` | **Script writing** — QA testing with pytest/unittest, act() vs act_get(), schemas, assertion patterns |
| `references/deployment_cli.md` | **Deployment CLI** — deploy workflows to AgentCore Runtime on AWS |
| `references/authentication.md` | API key vs IAM, session management |
| `references/workflow_definitions.md` | Workflow definitions with AWS CLI |
| `references/data_extraction.md` | Structured extraction with Pydantic |
| `references/hitl.md` | Human approval and UI takeover patterns |
| `references/tool_use.md` | External tools (@tool decorator, MCP servers) |
| `references/agentcore_browser.md` | Remote browser via AgentCore |
| `references/playwright_interop.md` | Direct Playwright page access, sensitive input, file downloads |
| `references/session_logs.md` | Logs, screenshots, and video recordings |
| `references/trajectory_analysis.md` | Understanding Nova Act trajectories |
| `references/visual_reporting.md` | Visual reporting — post-session markdown reports from steps.yaml, snapshots, and screenshots |
| `references/gherkin_testing.md` | **Gherkin testing** — `.feature` file writing, `qa-plan` compilation, session export → Gherkin conversion |
| `references/flow_discovery.md` | **Flow discovery** — live app exploration → codebase mapping, developer onboarding docs |
| `references/bug_reproduction.md` | **Bug reproduction** — reproduce → capture evidence → export → regression test |
