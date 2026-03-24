# Tool Use Beyond the Browser (Preview)

Integrate external tools (API calls, database queries, MCP servers) into Nova Act workflows via `act()` execution.

> **Preview feature** — API may change.

## Pattern 1: Python Function Tools

Decorate Python functions with `@tool`. Pass as list to `tools` constructor arg.

```python
from nova_act import NovaAct, tool

@tool
def lookup_booking(booking_id: str) -> str:
    # Query database, call API, etc.
    return f"Booking {booking_id}: confirmed"

with NovaAct(
    starting_page="https://example.com",
    tools=[lookup_booking],
) as nova:
    nova.act("Look up booking #12345 using the tool and verify it matches the page")
```

## Pattern 2: MCP Server Tools

Use Strands `MCPClient` to connect MCP servers. Pass `list_tools_sync()` output to `tools`.

```python
from mcp import StdioServerParameters, stdio_client
from nova_act import NovaAct
from strands.tools.mcp import MCPClient

with MCPClient(
    lambda: stdio_client(
        StdioServerParameters(command="uvx", args=["awslabs.aws-documentation-mcp-server@latest"])
    )
) as mcp_client:
    with NovaAct(
        starting_page="https://aws.amazon.com/",
        tools=mcp_client.list_tools_sync(),
    ) as nova:
        nova.act_get(
            "Use the 'search_documentation' tool to tell me about Amazon Bedrock. "
            "Ignore the web browser; do not click, scroll, type, etc."
        )
```

## Constraints

- `@tool` functions must have type hints and docstrings
- MCP tools require `strands-agents` and `mcp` packages
- Tools work alongside browser actions or independently (tell agent to ignore browser if tool-only)
