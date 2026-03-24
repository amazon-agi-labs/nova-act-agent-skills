# AgentCore Browser (Remote Browser Automation)

Run Nova Act against remote browsers via Bedrock AgentCore Browser Tool. No local Chrome needed.

## Install

```bash
pip install nova-act
```

`bedrock-agentcore` is included as a core dependency.

## API

`browser_session(region: str)` → context manager yielding `browser_client`
- `browser_client.generate_ws_headers()` → `(ws_url: str, headers: dict)` — WebSocket URL and auth headers

Pass `cdp_endpoint_url` and `cdp_headers` to `NovaAct` constructor (replaces local browser).

## Example

```python
from bedrock_agentcore.tools.browser_client import browser_session
from nova_act.nova_act import NovaAct

def main() -> None:
    with browser_session(region="us-east-1") as browser_client:
        ws_url, headers = browser_client.generate_ws_headers()

        with NovaAct(
            cdp_endpoint_url=ws_url,
            cdp_headers=headers,
            starting_page="https://example.com",
        ) as nova:
            result = nova.act_get("click the search button and tell me what happened")
            print(result.response)
```

## When to Use

- Production-scale remote browser automation
- Serverless environments (no local Chrome available)
- Deploying workflows to AgentCore Runtime (see `deployment_cli.md`)
- Running multiple concurrent browser sessions

## Constraints

- Requires AWS credentials with Bedrock AgentCore permissions
- `region` must match your AgentCore deployment region
- `starting_page` still required — sets initial navigation target
- `cdp_endpoint_url` + `cdp_headers` replace the local Playwright browser
