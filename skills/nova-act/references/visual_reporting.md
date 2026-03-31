# Visual Reporting

Build structured markdown reports from browser CLI session artifacts. After a session completes, use the recorded `steps.yaml`, `snapshot.yaml`, `screenshot.png`, and `log.txt` files to construct a narrative report that catalogs the key flows traversed.

## Session Artifacts Used

Each browser CLI command writes artifacts to its `log_dir`. The report draws from:

| Artifact | Content | Report Use |
|----------|---------|------------|
| `steps.yaml` | Step-by-step execution trace (multi-step AI commands) | Flow narrative, step summaries |
| `screenshot.png` | Post-command viewport capture | Embedded visual evidence |
| `before.png` | Pre-command viewport (transition commands) | Before/after comparisons |
| `failure.png` | Viewport at failure point | Error documentation |
| `snapshot.yaml` | Accessibility tree with element refs | Page state at each step |
| `log.txt` | Full command execution log | Timing, error details |

## Report Construction Process

1. **Collect log directories** — gather all `log_dir` paths from the session (printed after each command)
2. **Parse `steps.yaml`** — extract step descriptions, actions taken, and outcomes for each multi-step command
3. **Map screenshots to steps** — each `log_dir` contains `screenshot.png` (and optionally `before.png`) corresponding to that command
4. **Build narrative** — summarize what happened at each step using `steps.yaml` content, embed screenshots by relative path
5. **Assemble report** — combine into markdown with metadata header, flow sections, and artifact index

## Report Template

```markdown
# Session Report: <objective>

**Date:** <date>
**Starting URL:** <url>
**Commands executed:** <count>

## Flow Summary

<1-2 paragraph narrative of what the session accomplished, key pages visited, actions taken>

## Step-by-Step Detail

### Step 1: <action summary from steps.yaml>

![Step 1 result](./logs/<command_log_dir>/screenshot.png)

**Command:** `<command that was run>`
**Outcome:** <success/failure + brief description from steps.yaml>

### Step 2: <action summary>

![Step 2 result](./logs/<command_log_dir>/screenshot.png)

...

## Errors & Recovery

<Any failed commands, what went wrong (from failure.png + log.txt), how recovery was handled>

## Artifacts Index

| Step | Command | Screenshot | Log Dir |
|------|---------|------------|---------|
| 1 | `execute "..."` | [view](./logs/<dir>/screenshot.png) | `<dir>` |
| 2 | `goto <url>` | [view](./logs/<dir>/screenshot.png) | `<dir>` |
```

## Parsing steps.yaml

`steps.yaml` contains the execution trace for multi-step AI commands. Each entry has the action taken and its result:

```python
import yaml
from pathlib import Path

def summarize_steps(log_dir: str) -> list[dict]:
    """Extract step summaries from a command's steps.yaml."""
    steps_path = Path(log_dir) / "steps.yaml"
    if not steps_path.exists():
        return []
    with open(steps_path) as f:
        steps = yaml.safe_load(f)
    return [
        {"action": step.get("action", ""), "result": step.get("result", "")}
        for step in steps
    ]
```

## Screenshot Embedding

Reference screenshots by relative path so reports are portable:

```markdown
<!-- Relative to report file location -->
![Login page](./logs/cmd_001/screenshot.png)

<!-- Before/after for transition commands -->
| Before | After |
|--------|-------|
| ![before](./logs/cmd_003/before.png) | ![after](./logs/cmd_003/screenshot.png) |
```

Keep screenshots alongside the report in a predictable directory structure. Copy or symlink the `log_dir` outputs into a `logs/` folder next to the report.

## Tips

- **Parse `steps.yaml` first** — it provides the narrative backbone. Screenshots are supporting evidence.
- **Use relative paths** — `./logs/<dir>/screenshot.png` keeps reports portable across machines.
- **Include `failure.png` for errors** — documents what the page looked like when something went wrong.
- **One report per session** — group all commands from a single session into one report for coherent narrative.
- **Link to log dirs** — let readers drill into `log.txt` or `snapshot.yaml` for details beyond the summary.
