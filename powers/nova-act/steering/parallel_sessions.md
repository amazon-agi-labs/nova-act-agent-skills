# Parallel Browser Sessions

When you need to run the same workflow against multiple pages or sites — scraping, data extraction, workflow validation, prompt testing — parallelize sessions on subagents or background processes instead of running them one at a time.

Limit to 3 concurrent sessions to avoid API rate limits and disk pressure. For more than 3 sessions, batch them.

**Stagger session launches** — starting multiple headless browsers at the exact same moment causes resource contention that crashes browser processes (`BROWSER_ERROR: A runtime error occurred during command execution`). Add 10–15 second delays between session starts within a batch (e.g. `sleep 15` between launches). This applies to both subagent parallelism and shell background processes.

## Reading Results

After parallel runs complete, compare results across sessions. See the observability section in `browser_cli.md` for how to read stdout and `steps.yaml`. Look for inconsistencies — if the same prompt takes 2 steps in one session and 8 on another, something's off.

## Tips

- **Unique session IDs** — use the site name or a prefix to avoid collisions
- **Headless for bulk, headed for debugging** — switch to headed when you need the user to visually inspect a specific page
- **Clean up between batches** — `act browser session close-all --force` to avoid hitting session limits
- **Watch disk space** — session logs accumulate fast. Use `act browser session prune` to clean up.

## Related Files
- `workflow_refinement.md` — analyze and improve workflows using parallel session results
- `visual_reporting.md` — build markdown reports from session artifacts
- `browser_cli.md` — full CLI command reference and session management
