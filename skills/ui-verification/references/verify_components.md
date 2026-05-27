# Verify Components

Deep-dive for the `component_rules` category: component presence, variants, and props. Complements `references/verification.md` — does not replace it. The full workflow (open session → compile → verify → annotate → report) lives there.

**Tool:** `verify_components(session_id, rules, output_dir)` — always pass `output_dir` (absolute path to project root)
**Spec file:** `<output_dir>/.ui-verification/specs/component-rules.md`
**Source of truth upstream:** `design.md` (intentional layer; the category file is compiled from it — see `references/spec_sync.md`)
**Artifact:** `<output_dir>/.ui-verification/sessions/<session_id>/component_rules_assertions.json`

## What This Covers

- **Component presence:** does the correct component exist on the page
- **Variants:** is the right variant used (ghost, outlined, filled, primary, secondary, etc.)
- **Props:** correct radius, colors, font-weight per variant
- **States:** default, hover, active, disabled, selected (use `hover()` to trigger before checking)

## Translation Table

How to translate spec claims (from design.md → compiled into `component-rules.md`) into rules.

| Spec text (copy VERBATIM as `name`) | selector | property | constraint |
|---|---|---|---|
| "Primary button \| brand cyan fill \| 8px radius \| weight 600" | `button[class*=primary], [class*=btn-primary]` | `background-color` | `~rgb(6,182,212)` |
| "Ghost / Tab \| transparent fill \| 8px radius \| weight 500" | `[role=tab]` | `background-color` | `transparent` |
| "Icon button (circular) \| 50% radius \| neutral fill" | `button[class*=icon],button[aria-label]:not([class*=primary])` | `border-radius` | `>=50%` |
| "Card \| 14px radius (rounded.md) \| canvas surface" | `[data-testid=card], [class*=card-container]` | `border-radius` | `>=12px` |

## Scope

A rule's scope comes from the `## Scope:` section it lives under in `component-rules.md`. Component variants that only render on certain routes (e.g. an admin-only delete button) belong under `## Scope: route=/admin/**`. App-wide buttons live under `## Scope: any`. See `references/spec_authoring.md` § Route-Scoped Rules.

## Component Variants Often Share Selectors

When variants share a base selector, differentiate with class patterns or attribute selectors:

```
button[class*=primary]   ← primary CTA variant
button[class*=secondary] ← secondary outline variant
button[class*=ghost]     ← ghost/text-only variant
[role=tab]               ← tab-style buttons (any visual variant)
```

Group related component rules in a single `verify_components` call — the MCP server merges per-call into the same assertion JSON.

## Checking Hover/Active States

For state-dependent styles:

1. Call `verify_components(session_id, rules, output_dir)` for default-state rules
2. Call `hover(session_id, selector)` to trigger hover state on a specific element
3. Call `verify_components(session_id, rules, output_dir)` again with hover-specific rules — use a distinguishing `name` prefix (e.g. `"Primary button (hover) | ..."`) so warm-start can diff hover and default rules separately.

## Rules

- `name` MUST be copied verbatim from the source spec text — paraphrasing breaks warm-start diffing.
- Component variants often share a base selector — use class patterns or `data-*` attributes to differentiate.
- Verify the default state first, then hover/active separately if specified.
- If a component is conditionally rendered (modal-only, route-only), its rule's selector won't match when the component isn't visible. That's expected — under route-scoped rules, the agent only runs the rule on URLs where the component is meant to appear.

## Example Call

```
verify_components(
  session_id="bd89560b-8745-4a34-a513-05f763614870",
  rules="[{\"name\": \"Primary button | brand cyan fill | 8px radius | weight 600\", \"selector\": \"button[class*=primary]\", \"property\": \"background-color\", \"constraint\": \"~rgb(6,182,212)\"}]",
  output_dir="/Users/you/my-project"
)
```
