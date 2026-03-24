# Nova Act Authentication

## Auth Methods

Two authentication methods, usable standalone or with Workflow constructs:

1. **API Key** — key from nova.amazon.com, for development/testing
2. **IAM** — AWS credentials, for production workflows with CloudTrail audit logging

```
Need S3 export, CloudWatch logs, or CloudTrail auditing?
├─ Yes → IAM + Workflow
└─ No
   └─ Running in AWS with IAM roles available?
      ├─ Yes → IAM + Workflow
      └─ No → API Key (simpler)
```

| Aspect | API Key | IAM |
|--------|---------|-----|
| Use Case | Development/Testing | Production Workflows |
| Credential Source | nova.amazon.com/act?tab=dev_tools | AWS Credentials |
| Audit Logging | Limited | CloudTrail |
| Workflow Support | Yes (`nova_act_api_key` param) | Yes (`boto_session_kwargs` param) |
| Terms of Use | nova.amazon.com ToU | AWS Service Terms |

## API Key Setup

```bash
# Get key from https://nova.amazon.com/act?tab=dev_tools
export NOVA_ACT_API_KEY="your_api_key_here"
```

```python
from nova_act import NovaAct

# Option 1: env var (auto-detected)
with NovaAct(starting_page="https://example.com") as nova:
    nova.act("perform task")

# Option 2: explicit parameter (overrides env var)
with NovaAct(
    starting_page="https://example.com",
    nova_act_api_key="your_api_key_here"
) as nova:
    nova.act("perform task")
```

## IAM Setup

IAM credentials are used when a Workflow construct is active. If no `boto_session_kwargs` or `nova_act_api_key` is provided, the Workflow auto-loads AWS credentials from environment (AWS_PROFILE, AWS_ACCESS_KEY_ID, etc.) or defaults to `us-east-1`.

```python
from nova_act import NovaAct, workflow

@workflow(
    model_id="nova-act-latest",
    workflow_definition_name="production-automation",
    boto_session_kwargs={"region_name": "us-east-1"}  # optional if env creds exist
)
def production_task():
    with NovaAct(starting_page="https://example.com") as nova:
        nova.act("perform production automation")
```

Or with the `Workflow` context manager:

```python
from nova_act import NovaAct, Workflow

with Workflow(
    model_id="nova-act-latest",
    workflow_definition_name="production-automation",
) as wf:
    with NovaAct(starting_page="https://example.com") as nova:
        nova.act("perform production automation")
```

### Required IAM Permissions

The Nova Act service uses its own IAM namespace (`nova-act`). At minimum, the IAM principal running workflows needs:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["nova-act:*"],
      "Resource": ["*"]
    }
  ]
}
```

For production, scope down to specific actions and resources. For deployment workflows using the CLI (`act workflow deploy`), additional permissions are needed for ECR, CodeBuild, CloudWatch Logs, S3, and Bedrock AgentCore — the CLI handles IAM role creation automatically. See `deployment_cli.md` for details.

### Migration Path: API Key → IAM

1. **Develop** with API key (no Workflow needed)
2. **Wrap** in `@workflow` or `Workflow()` when ready for production
3. **Deploy** to AWS — Workflow uses IAM credentials from execution environment

## Browser Session Persistence

Persist login state across runs using `user_data_dir` + `clone_user_data_dir=False`:

```python
import os
from nova_act import NovaAct

user_data_dir = "./browser_sessions/dev"
os.makedirs(user_data_dir, exist_ok=True)

# First run: log in manually
with NovaAct(
    starting_page="https://example.com",
    user_data_dir=user_data_dir,
    clone_user_data_dir=False,
    headless=False
) as nova:
    input("Log in, then press enter...")

# Subsequent runs: session is reused
with NovaAct(
    starting_page="https://example.com",
    user_data_dir=user_data_dir,
    clone_user_data_dir=False,
    headless=True
) as nova:
    nova.act("navigate to dashboard")  # Already authenticated
```

The SDK ships a convenience script: `python -m nova_act.samples.setup_chrome_user_data_dir --user_data_dir <directory>`

When running multiple `NovaAct` instances in parallel, each must have its own `user_data_dir` — either omit it (fresh temp dir per instance) or use `clone_user_data_dir=True`.

### Using Local Default Chrome Browser

To use your installed Chrome with its extensions and saved state (macOS only):

```python
from nova_act import NovaAct, rsync_from_default_user_data

working_dir = "/tmp/chrome-working-dir"
rsync_from_default_user_data(working_dir)

with NovaAct(
    starting_page="https://example.com",
    use_default_chrome_browser=True,
    user_data_dir=working_dir,
    clone_user_data_dir=False
) as nova:
    nova.act("perform task")
```

This quits and restarts your default Chrome with CDP arguments. The original `user_data_dir` cannot be used directly — you must rsync to a working copy first.

## Secure Login

Never pass passwords in `act()` prompts — use Playwright's keyboard API:

```python
import getpass
from nova_act import NovaAct

def secure_login(nova, username):
    nova.act(f"enter username '{username}' in the username field")
    nova.act("click on the password field to focus it")
    password = getpass.getpass("Enter password: ")
    nova.page.keyboard.type(password)
    nova.act("click the login submit button")
    return nova.act_get("Am I logged in?", schema={"type": "boolean"}).parsed_response
```

For 2FA flows, check for the prompt after login and use `input()` to get the code from the user.

## Security Best Practices

- Set `NOVA_ACT_API_KEY` via environment variable or `.env` file (gitignored) — never hardcode in scripts
- Use `user_data_dir` + `clone_user_data_dir=False` for session persistence
- Use Playwright `keyboard.type()` for passwords — never in `act()` prompts
- Use IAM roles in AWS compute environments instead of long-lived access keys
- Screenshots capture visible page content — avoid screenshots on pages showing sensitive data
