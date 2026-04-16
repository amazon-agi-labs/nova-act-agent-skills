## Trajectory Analysis

When asked to analyze a trajectory, request the JSON file from the user.

### What is a trajectory?

A trajectory is a Nova Act execution recording containing the original prompt, action sequence (clicks, types, scrolls), screenshots at each step, and the final result.

Trajectories are only generated when `replayable=True` is set on the `NovaAct` constructor. After an `act()` call, the file path is available via `result.trajectory_file_path` (returns `None` if `replayable` was not enabled).

Local trajectory files follow the naming pattern: `act_{act_id}_{prompt_snippet}_trajectory.json`

### Trajectory JSON Formats

Two formats exist:

#### Format 1: Local trajectory file (multi-step)

Single JSON file with all steps in a `steps` array:

```json
{
  "sdk_version": "string",
  "prompt": "string",
  "steps": [
    {
      "active_url": "string",
      "image": "string (base64 screenshot — SKIP on initial read)",
      "simplified_dom": "string (HTML DOM — SKIP on initial read)",
      "program": {
        "calls": [
          {
            "name": "string (e.g. think, agentClick, agentType, wait, return, waitForPageToSettle, takeObservation)",
            "kwargs": {"value": "string", "box": "string", "seconds": "number"},
            "id": "string",
            "is_tool": "boolean"
          }
        ]
      }
    }
  ],
  "metadata": {
    "session_id": "string",
    "act_id": "string",
    "num_steps_executed": "integer",
    "start_time": "number",
    "end_time": "number",
    "prompt": "string",
    "step_server_times_s": ["number"],
    "time_worked_s": "number",
    "human_wait_time_s": "number",
    "workflow_definition_name": "string | null",
    "workflow_run_id": "string | null"
  }
}
```

#### Format 2: S3 trace file (single step per file)

One step per JSON file. Multiple files in the same S3 prefix form the full trajectory. Group by `metadata.sessionId` + `metadata.actId`, sort by `metadata.stepCount`.

```json
{
  "metadata": {
    "sessionId": "string",
    "actId": "string",
    "stepId": "string",
    "stepCount": "integer",
    "startTime": "string"
  },
  "orchestrationTrace": {
    "input": {
      "screenshot": {"source": "string (base64 — SKIP)", "sourceType": "string"},
      "activeURL": "string",
      "prompt": "string"
    },
    "output": {
      "rawResponse": "string (verbose model output — SKIP)"
    }
  },
  "failureTrace": "null | {\"type\": \"ERROR_CODE\", \"message\": \"string\"}"
}
```

Error codes for `failureTrace.type`: `INVALID_INPUT`, `MODEL_ERROR`, `INTERNAL_ERROR`, `GUARDRAILS_ERROR`, `UNAUTHORIZED_ERROR`, `TOO_MANY_REQUESTS`, `DAILY_QUOTA_LIMIT_ERROR`, `SESSION_EXPIRED_ERROR`.

### How to analyze

1. **Locate trajectory files**: Get a JSON file, folder, or S3 URI from the user.

2. **Read selectively** — trajectory files can be 10MB+ due to base64 screenshots. Extract only lightweight fields using a script:

```python
import json, glob, os, sys

path = sys.argv[1] if len(sys.argv) > 1 else "trajectory.json"

def extract_local(data):
    meta = data.get("metadata", {})
    return {
        "format": "local",
        "sdk_version": data.get("sdk_version"),
        "prompt": data.get("prompt") or meta.get("prompt"),
        "session_id": meta.get("session_id"),
        "act_id": meta.get("act_id"),
        "num_steps": meta.get("num_steps_executed"),
        "time_worked_s": meta.get("time_worked_s"),
        "steps": [{
            "step": i,
            "active_url": s.get("active_url"),
            "actions": [{
                "name": c.get("name"),
                "kwargs": {k: (v[:200] + "..." if isinstance(v, str) and len(v) > 200 else v)
                           for k, v in c.get("kwargs", {}).items()},
            } for c in s.get("program", {}).get("calls", [])]
        } for i, s in enumerate(data.get("steps", []))]
    }

def extract_s3(data):
    meta = data.get("metadata", {})
    inp = data.get("orchestrationTrace", {}).get("input", {})
    return {
        "stepCount": meta.get("stepCount"),
        "sessionId": meta.get("sessionId"),
        "actId": meta.get("actId"),
        "activeURL": inp.get("activeURL"),
        "prompt": inp.get("prompt"),
        "failed": data.get("failureTrace") is not None,
    }

if os.path.isdir(path):
    files = sorted(glob.glob(os.path.join(path, "*.json")))
    steps = sorted([extract_s3(json.load(open(f))) for f in files], key=lambda s: s.get("stepCount", 0))
    summary = {"format": "s3_directory", "num_steps": len(steps), "steps": steps}
else:
    with open(path) as f:
        data = json.load(f)
    summary = extract_local(data) if "steps" in data else {"format": "s3_single", "steps": [extract_s3(data)]}

print(json.dumps(summary, indent=2))
```

3. **For multiple trajectories in a folder**: Identify and group them first (local format: each `.json` with `steps` array is one trajectory; S3 format: group by sessionId + actId). Analyze each independently to avoid context window exhaustion.

4. **Report findings**: Total action count, step-by-step action breakdown, anomalies, and prompt improvement suggestions.

5. **Drill into specific steps on demand**: Only extract screenshots or DOM snapshots for a specific step when asked.

## Related Files
- `workflow_refinement.md` — use trajectory analysis to identify failure patterns and improve workflows
- `mock_generation.md` — use trajectory data to generate static HTML mock sites
- `visual_reporting.md` — build markdown reports from session artifacts including trajectories
- `browser_cli.md` — CLI commands that generate trajectory files
- `session_logs.md` — directory structure where trajectory files are stored