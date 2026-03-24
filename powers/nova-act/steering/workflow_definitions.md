# Workflow Definitions

## Overview
Workflow Definitions enable Nova Act scripts to run with AWS IAM authentication, track execution via workflow runs, and export data to S3. They are required when using IAM credentials (not needed for API key auth).

See `authentication.md` for full API key vs IAM details.

## Creating Workflow Definitions

### Using Nova Act CLI
```bash
act workflow create --name my-workflow
```
Automatically creates a workflow definition with the default S3 bucket (`nova-act-{account-id}-{region}`).

### Using AWS CLI
```bash
aws nova-act create-workflow-definition \
  --name my-workflow \
  --export-config '{
    "s3BucketName": "my-bucket",
    "s3KeyPrefix": "nova-act-workflows"
  }' \
  --region us-east-1
```

### Using boto3
```python
import boto3

client = boto3.client("nova-act")
response = client.create_workflow_definition(
    name="my-workflow",
    exportConfig={
        "s3BucketName": "my-bucket",
        "s3KeyPrefix": "nova-act-workflows",
    },
)
```

## Using Workflows in Code

### Context Manager (primary)

The `Workflow` class calls `CreateWorkflowRun` on enter and `UpdateWorkflowRun` (SUCCEEDED/FAILED) on exit. Pass it to `NovaAct` via the `workflow` argument:

```python
from nova_act import NovaAct, Workflow

with Workflow(
    workflow_definition_name="my-workflow",
    model_id="nova-act-latest",
) as workflow:
    with NovaAct(
        starting_page="https://example.com",
        workflow=workflow,
    ) as nova:
        nova.act("perform automation")
```

### Decorator (convenience)

The `@workflow` decorator injects the workflow via ContextVars — no need to pass `workflow=` to `NovaAct`:

```python
from nova_act import NovaAct, workflow

@workflow(
    workflow_definition_name="my-workflow",
    model_id="nova-act-latest",
)
def main():
    with NovaAct(starting_page="https://example.com") as nova:
        nova.act("perform automation")

main()
```

### Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `model_id` | Yes | Model to use (e.g., `"nova-act-latest"`) |
| `workflow_definition_name` | Yes (IAM) | Must match created definition name |
| `boto_session_kwargs` | No | Dict passed to `boto3.Session()` — defaults to `{"region_name": "us-east-1"}` |
| `boto_config` | No | `botocore.config.Config` for retries and timeouts |
| `log_group_name` | No | CloudWatch log group name (IAM only) |
| `nova_act_api_key` | No | API key auth — cannot combine with `boto_session_kwargs` |

### Configuring AWS Credentials

```python
with Workflow(
    workflow_definition_name="my-workflow",
    model_id="nova-act-latest",
    boto_session_kwargs={
        "profile_name": "my-aws-profile",
        "region_name": "us-east-1",
    },
) as workflow:
    ...
```

If `boto_session_kwargs` is not provided and no API key is set, the workflow automatically loads AWS credentials via boto3 defaults.

## Retry Handling

Override default retry behavior (1 retry) and read timeout (60s) via `boto_config`:

```python
from botocore.config import Config

boto_config = Config(retries={"total_max_attempts": 5, "mode": "standard"}, read_timeout=90)
with Workflow(
    workflow_definition_name="my-workflow",
    model_id="nova-act-latest",
    boto_config=boto_config,
) as workflow:
    ...
```

Note: retrying may result in increased cost if the request executes multiple times.

## Multi-threading

The `Workflow` context manager works directly with threads — pass the workflow object:

```python
from threading import Thread
from nova_act import NovaAct, Workflow

def worker(workflow):
    with NovaAct(starting_page="https://example.com", workflow=workflow) as nova:
        nova.act("do task")

with Workflow(workflow_definition_name="my-workflow", model_id="nova-act-latest") as workflow:
    t = Thread(target=worker, args=(workflow,))
    t.start()
    t.join()
```

With the `@workflow` decorator, use `copy_context()` or pass the workflow explicitly via `get_current_workflow()`:

```python
from contextvars import copy_context
from nova_act import NovaAct, workflow, get_current_workflow

@workflow(workflow_definition_name="my-workflow", model_id="nova-act-latest")
def main():
    ctx = copy_context()
    t = Thread(target=ctx.run, worker_fn)
    t.start()
    t.join()
```

Multi-processing is not currently supported (`Workflow` holds non-picklable boto3 objects).

## IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "nova-act:CreateWorkflowDefinition",
        "nova-act:GetWorkflowDefinition",
        "nova-act:ListWorkflowDefinitions",
        "nova-act:DeleteWorkflowDefinition",
        "nova-act:CreateWorkflowRun",
        "nova-act:GetWorkflowRun"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl"
      ],
      "Resource": "arn:aws:s3:::your-bucket-name/*"
    }
  ]
}
```

## Related Files
- `authentication.md` — API key vs IAM setup, session management
- `session_logs.md` — Logs, screenshots, and video recordings
- `deployment_cli.md` — Deploying workflows to AWS AgentCore
