# Deployment CLI

Deploy Nova Act workflows to AgentCore Runtime. Handles containerization, ECR, IAM, S3, and AgentCore automatically.

> **Not for production** — quickstart deployment utility only.

## Install

```bash
pip install nova-act[cli]
```

Requires Docker, Python 3.10+, AWS credentials.

## Quick Start

### Named Workflow (Recommended)

```bash
act workflow create --name my-workflow
act workflow deploy --name my-workflow --source-dir /path/to/project
act workflow run --name my-workflow --payload '{"input": "data"}'
```

### Quick Deploy

```bash
act workflow deploy --source-dir /path/to/project
# Auto-generates name like: workflow-20251130-120945
act workflow run --name workflow-20251130-120945 --payload '{"input": "data"}'
```

## Commands

| Command | Purpose |
|---------|---------|
| `create` | Register workflow |
| `deploy` | Build and deploy to AgentCore |
| `run` | Execute workflow with payload |
| `list` | List workflows |
| `show` | Show workflow details |
| `update` | Modify workflow config |
| `delete` | Remove workflow |

## Entry Point Requirements

- Must be `.py` (defaults to `main.py`)
- Must contain `def main(payload):`
- Specify explicitly: `--entry-point my_script.py`
- Bypass validation: `--skip-entrypoint-validation`

## Key Options

```bash
# Custom execution role
act workflow deploy ... --execution-role-arn "arn:aws:iam::123456789012:role/MyRole"

# Deploy to specific region
act workflow deploy --name my-workflow --region us-west-2

# AWS profile (before subcommand)
act workflow --profile my-profile deploy --name my-workflow --source-dir /path

# Tail logs during execution
act workflow run --name my-workflow --payload '{}' --tail-logs

# Payload from file
act workflow run --name my-workflow --payload-file payload.json

# Skip S3 bucket creation
act workflow deploy ... --skip-s3-creation

# Custom S3 bucket
act workflow deploy ... --s3-bucket-name my-custom-bucket
```

## Environment Variables at Runtime

Inject env vars via `AC_HANDLER_ENV` without redeploying:

```bash
act workflow run --name my-workflow --payload '{
  "AC_HANDLER_ENV": {"NOVA_ACT_API_KEY": "your-key"},
  "input": "data"
}'
```

Access in workflow: `os.environ.get("NOVA_ACT_API_KEY")`

## AWS Resources Created

| Resource | Naming Pattern |
|----------|---------------|
| ECR Repository | `nova-act-cli-default` (shared) |
| IAM Role | `nova-act-{workflow-name}-role` |
| S3 Bucket | `nova-act-{account-id}-{region}` |
| AgentCore Runtime | One per workflow |
| WorkflowDefinition | Via nova-act service |
| CloudWatch Logs | `/aws/bedrock-agentcore/runtimes/{agent-id}-default` |

## Configuration

- State: `~/.act_cli/state/{account_id}/{region}/workflows.json`
- User config: `~/.act_cli/config.yml`
- Build artifacts: `~/.act_cli/builds/{workflow-name}/` (persistent, not auto-cleaned)

## WorkflowDefinition Management

```bash
# Use existing WorkflowDefinition
act workflow create --name my-workflow \
  --workflow-definition-arn arn:aws:nova-act:us-east-1:123456789012:workflow-definition/my-workflow

# Or via AWS CLI
aws nova-act create-workflow-definition --name my-workflow \
  --export-config '{"s3BucketName": "my-bucket", "s3KeyPrefix": "nova-act-workflows"}' \
  --region us-east-1
```

## Remote Build

Build the container image remotely using AWS CodeBuild instead of local Docker. Recommended for non-ARM64 machines (e.g., Intel/AMD laptops).

```bash
act workflow deploy --name my-workflow --source-dir /path/to/project --remote-build
```

Creates a CodeBuild project (`nova-act-*`) that builds the ARM64 image in AWS and pushes to ECR.

## Constraints

- Available in `us-east-1` only
- `--profile` before subcommand
- Quick deploy creates persistent workflows
- Build artifacts not auto-cleaned
- `--remote-build` requires CodeBuild permissions in the IAM role
