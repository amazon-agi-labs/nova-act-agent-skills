# Warm Start (deferred)

**Cross-session warm-start is out of scope right now.** Every verification run is independent: opens its own browser session, compiles fresh (or skips compile if `design.md` and category files match the integrity ledger from a prior compile), verifies, writes its own report.

The mechanism for re-compile skipping lives in `verification.md` step 4:

- If `<output_dir>/.ui-verification/.integrity.json` exists and its `design.md` hash + category file hashes all match current files, skip recompilation and proceed to verify with the existing rules.
- Otherwise, recompile only the affected category file scopes; on hash mismatch of a category file, the audit runs first to reconcile.

That's enough for the working case: agent runs verification, comes back later in the same project, doesn't have to recompile if `design.md` hasn't changed.

## Why cross-session result-carryover is deferred

A robust cross-session warm-start needs answers to questions we haven't validated:

- **Concurrent runs.** What if two agent sessions run verification on the same project at the same time? They'd race on any shared pointer; one would see the other's stale results.
- **Failed runs.** A session that crashed mid-run leaves orphaned assertion JSON. How does the next run know to ignore it?
- **Result staleness.** Carrying over a prior pass/fail when the live site might have drifted is unsafe without a freshness check the agent can't perform automatically.
- **Deletion / cleanup.** Sessions accumulate. Without a retention policy, the artifact dir grows unboundedly.

Until those are resolved, every visual run does its own compile (skip if hash matches) and its own verify. Reports are the durable output the user consumes.

## Flow verification doesn't warm-start either — for a different reason

Flow runs are inherently non-deterministic. Nova Act re-interprets each step using its current model state; network timing varies; the live UI shifts between runs. Carrying forward "passed" verdicts from a prior flow run would mask real flakiness or environmental drift — a flow that passed last run because the network was fast could legitimately fail this run, and the user needs to see that.

Every flow runs every time. There's no integrity ledger for `.feature` files (they're already the source layer; nothing compiles to them) and no per-flow assertion cache. Flow-side regressions surface via the per-flow status table in `reports/<run-timestamp>/report.md` — comparing two consecutive runs' reports shows what changed.

This is intentional: flow verification optimizes for honest signal over speed. Every run is fresh.

## What's still tracked per run

Every successful verification produces:

```
<output_dir>/.ui-verification/.integrity.json                                            ← compile-state ledger (design.md + category file hashes)
<output_dir>/.ui-verification/specs/<category>.md                                        ← compiled rules (clean markdown)
<output_dir>/.ui-verification/sessions/<session_id>/<category>_assertions.json           ← per-element verdicts (MCP-owned)
<output_dir>/.ui-verification/reports/<run-timestamp>/report.md                          ← human-readable report
<output_dir>/.ui-verification/reports/<run-timestamp>/screenshots/<category>.png         ← annotated failures
<output_dir>/.ui-verification/reports/<run-timestamp>/sessions.json                      ← manifest of session IDs in this run
```

The reports directory is the durable record. Old assertion JSON is left in place; future runs don't rely on it.
