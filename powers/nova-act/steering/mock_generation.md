# Mock Site Generation

Generate static HTML mock sites from Nova Act trajectories captured against real websites for fast, deterministic, offline iteration on automation prompts.

## Use Cases

- **Workflow refinement** — iterate on prompts with `file://` URLs, no rate limits, no anti-bot, deterministic. See `workflow_refinement.md`.
- **Demos** — reproduce a flow without credentials or network access

## Pipeline

```
1. Run workflow against real site → capture trajectory
2. Extract page structure from trajectory (screenshots, DOM snapshots, URLs visited)
3. Generate static HTML pages that replicate the flow-relevant elements
4. Validate mock by running the same prompts against it
```

## Step 1: Capture Trajectory

Run the workflow against the real site with the CLI. Each command writes artifacts to its `log_dir`:

```bash
act browser execute "Navigate to the checkout page" --session-id capture --headless
act browser execute "Fill in shipping details and proceed to payment" --session-id capture --headless
act browser execute "Complete the order" --session-id capture --headless
```

Collect the `log_dir` paths from each command's output.

## Step 2: Extract Page Structure

From each command's `log_dir`, use:

| Artifact | What It Tells You |
|----------|-------------------|
| `screenshot.png` / `before.png` | Visual layout — what the page looks like at each step |
| `snapshot.yaml` | Accessibility tree — the elements the model can see and interact with |
| `steps.yaml` | What the model clicked, typed, scrolled — which elements matter for the flow |

Focus on flow-relevant elements: the buttons clicked, forms filled, modals triggered, navigation links used.

## Step 3: Generate Mock HTML

Build static HTML pages that replicate what the real site does. The mock should look and behave like the real page from the model's perspective — same styling, same labels, same interactive behavior. Examples of things to replicate:

- Page layout, colors, fonts
- Buttons, links, forms, modals the workflow interacts with
- Page transitions (JS show/hide, navigation between pages)
- Loading spinners and delayed state changes
- Cookie consent banners
- Confirmation banners and success messages
- Retention offers and multi-step dialogs

Mock interactions that would normally require a backend — authentication should accept any credentials, forms should accept any input, OTP fields should accept any code. Skip real API calls, dynamic content loading, analytics, and third-party scripts.

Each mock site should be self-contained in a directory with an entry point HTML file, `styles.css`, and any additional pages.

## Step 4: Validate

Run the same prompts against the mock using `file://` URLs:

```bash
act browser execute "Navigate to the checkout page" \
  --session-id validate --starting-page "file:///path/to/mock/index.html" \
  --headless
```

If the prompts work on the mock, they should work on the real site. If they fail on the mock, the mock is missing flow-relevant elements — check `steps.yaml` from the real-site run to see what the model interacted with.

## Tips

- **Replicate, don't invent** — only include elements that exist on the real site. The trajectory tells you exactly what's there.

## Related Files
- `workflow_refinement.md` — iterate on prompts using mocks for fast feedback
- `browser_cli.md` — CLI commands, session log artifacts (`steps.yaml`, `snapshot.yaml`, screenshots)
- `visual_reporting.md` — build reports from session artifacts
