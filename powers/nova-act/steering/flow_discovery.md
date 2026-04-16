# Flow Discovery with Nova Act

Use the browser CLI to explore a live application, capture user flows, and map them to codebase structure.

## Discovery Workflow

```
Step 1: Navigate live app → capture flows with session recording
Step 2: Export session → convert to Gherkin scenarios
Step 3: Map Gherkin steps to codebase (routes, components, API calls)
Step 4: Generate flow documentation
```

## Step 1: Capture Flows

```bash
# Start session and explore the main user journey
act browser goto https://app.example.com --session-id discover
act browser execute "1. Click 'Products' nav link 2. Click first product 3. Click 'Add to Cart' 4. Click cart icon 5. Click 'Checkout'" --session-id discover

# Capture evidence at key points
act browser screenshot -o checkout_flow.png --session-id discover
act browser snapshot -o checkout_tree.yaml --session-id discover
act browser get-content --format markdown -o checkout_page.md --session-id discover

# Capture network traffic for API mapping
act browser network-log --filter "*api*" --session-id discover

# Export the full session
act browser session export --session-id discover -o product_purchase_flow.yaml
```

## Step 2: Gherkin Translation

Convert the exported session to `.feature` files using the mapping in `gherkin_testing.md`. Each scenario = one user flow.

## Step 3: Codebase Mapping

For each Gherkin step, search the codebase for:

| What to Find | Where to Look |
|--------------|---------------|
| Route definitions | URLs visited during flow |
| Component files | UI elements interacted with (from snapshot) |
| API endpoints | Network requests captured by `network-log` |
| State management | Data flow between components |

Output: a mapping table of `Flow Step → URL → Component → API Endpoint`

## Step 4: Documentation Output

Generate from the mapping:
- Flow diagram (mermaid) showing user journey through the app
- Developer onboarding doc linking visual flows to code locations

Example output:
```
User clicks "Checkout" → /checkout → CheckoutPage.tsx → POST /api/checkout → CheckoutController
```

## Use Case: Developer Onboarding

1. Agent explores the live app, captures 5-10 main user flows
2. Maps each flow to codebase locations via routes, components, APIs
3. Produces a "Visual Flow → Code Map" document
4. New developer sees: "when user clicks Checkout, it hits `/api/checkout` handled by `CheckoutController` in `src/controllers/checkout.ts`"

## Related Files
- `workflow_refinement.md` — after discovering flows, write and refine automation prompts
- `gherkin_testing.md` — Gherkin pipeline and session export conversion
- `browser_cli.md` — Full CLI command reference
- `bug_reproduction.md` — Reproduce → evidence → regression test
