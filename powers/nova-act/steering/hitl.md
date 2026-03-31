# Human-in-the-Loop (HITL)

Enable human supervision within Nova Act workflows. Implemented in your code via the SDK (not a managed AWS service).

## Patterns

| Pattern | Use Case | Trigger |
|---------|----------|---------|
| `approve(message)` | Binary/multi-choice decisions (e.g., expense reports, purchase approvals) | Agent encounters decision point requiring human judgment |
| `ui_takeover(message)` | Manual browser control via mouse + keyboard (e.g., CAPTCHA, login) | Agent encounters task requiring human interaction |

## API

Extend `HumanInputCallbacksBase`, implement `approve` and `ui_takeover`, pass instance to `human_input_callbacks` constructor arg.

### Imports

```python
from nova_act import NovaAct
from nova_act.tools.human.interface.human_input_callback import (
    ApprovalResponse,
    HumanInputCallbacksBase,
    UiTakeoverResponse,
)
```

### Return Values

- `ApprovalResponse.YES` — human approved the action
- `ApprovalResponse.CANCEL` — human rejected (raises `ApproveCanceledError`)
- `UiTakeoverResponse.COMPLETE` — human finished the takeover
- `UiTakeoverResponse.CANCEL` — human canceled (raises `UiTakeoverCanceledError`)

### Properties on HumanInputCallbacksBase

- `self.most_recent_screenshot` — base64-encoded screenshot of current browser state, updated automatically before each step. Use this to show the human what the browser looks like.
- `self.act_session_id` — session ID for the current Act session
- `self.current_act_id` — current act invocation ID

## Example

```python
class MyHITLCallbacks(HumanInputCallbacksBase):
    def approve(self, message: str) -> ApprovalResponse:
        screenshot = self.most_recent_screenshot  # base64 image
        # Present screenshot + message to reviewer
        approved = show_approval_ui(screenshot, message)
        return ApprovalResponse.YES if approved else ApprovalResponse.CANCEL

    def ui_takeover(self, message: str) -> UiTakeoverResponse:
        screenshot = self.most_recent_screenshot
        # Hand browser control to human operator
        completed = show_takeover_ui(screenshot, message)
        return UiTakeoverResponse.COMPLETE if completed else UiTakeoverResponse.CANCEL

with NovaAct(
    starting_page="https://example.com",
    tty=False,
    human_input_callbacks=MyHITLCallbacks(),
) as nova:
    result = nova.act("complete the checkout process")
```

## Constraints

- `tty=False` recommended when using HITL callbacks
- You implement the UI/notification layer (SDK provides callback hooks)
- See [AWS docs on HITL](https://docs.aws.amazon.com/nova-act/latest/userguide/hitl.html#implementing-hitl) for production implementation patterns
