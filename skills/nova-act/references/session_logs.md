# Session Logs, Screenshots & Recordings

## logs_directory

Controls where session artifacts are written. Defaults to a temp dir if not set.

```python
with NovaAct(
    starting_page="https://example.com",
    logs_directory="./my_logs",
    record_video=True,  # default: False
) as nova:
    nova.act("perform actions")
# Artifacts written to ./my_logs after context exits
```

## What Gets Written

Per `act()`/`act_get()` call:
- `act_<id>_<prompt>.html` — HTML report with embedded screenshots per step
- `act_<id>_<prompt>.json` — trajectory JSON (steps, metadata, timing)
- `act_<id>_<prompt>_traces.json` — trace data

Per session (if `record_video=True`):
- Playwright video recording of the browser

## Manual Screenshots

Access the Playwright page directly for on-demand screenshots:

```python
with NovaAct(starting_page="https://example.com") as nova:
    nova.act("navigate to dashboard")
    nova.page.screenshot(path="dashboard.png")
```

`nova.page` returns a Playwright `Page` object — all Playwright page methods are available.

## Constraints

- `logs_directory` always gets written to (temp dir if not specified)
- `record_video=True` requires `logs_directory` to be set (video is skipped if logs_directory is None and no temp dir fallback)
- HTML reports include base64-encoded screenshots — no separate image files
- `nova.page` is only available with Playwright-based actuators (not CDP-only connections)
