# Verify Project Rules

Deep-dive for the `project_rules` category: layout structure, spacing system, project-specific conventions. Complements `references/verification.md` — does not replace it. The full workflow lives there.

**Tool:** `verify_project_rules(session_id, rules, output_dir)` — always pass `output_dir` (absolute path to project root)
**Spec file:** `<output_dir>/.ui-verification/specs/project-rules.md`
**Source of truth upstream:** `design.md` (intentional layer; the category file is compiled from it — see `references/spec_sync.md`)
**Artifact:** `<output_dir>/.ui-verification/sessions/<session_id>/project_rules_assertions.json`

## What This Covers

- **Layout positions:** position (static, relative, fixed, sticky, absolute)
- **Dimensions:** width, height, min-width, max-width, min-height, max-height
- **Display modes:** display (flex, grid, block, none)
- **Flex / Grid properties:** flex-direction, justify-content, align-items, grid-template-columns
- **Overflow:** overflow, overflow-x, overflow-y
- **Z-index:** stacking order
- **Spacing system:** consistent use of spacing tokens (margin, padding, gap)

## Translation Table

How to translate spec claims (from design.md → compiled into `project-rules.md`) into rules.

| Spec text (copy VERBATIM as `name`) | selector | property | constraint |
|---|---|---|---|
| "Header position \| static \| Not fixed or sticky" | `header` | `position` | `=static` |
| "Header height \| 80px \| Consistent across pages" | `header` | `height` | `=80px` |
| "Page background \| Canvas Deep \| #0a0e1a" | `body` | `background-color` | `~rgb(10,14,26)` |
| "Container max-width \| 1280px \| Centered content area" | `[class*=container]` | `max-width` | `<=1280px` |
| "Card border-radius \| 14px (rounded.md)" | `[data-testid=card-container], [class*=card]` | `border-radius` | `>=12px` |

## Scope

A rule's scope comes from the `## Scope:` section it lives under in `project-rules.md`. Layout structure that's app-wide (header height, container max-width) goes under `## Scope: any`. Layout that differs per route (e.g. `body` background that's dark on landing and white in the app) goes under route-specific scopes — see `references/spec_authoring.md` § Route-Scoped Rules for the canonical example.

## Common Patterns

### Static vs scrolling positioning
```json
{"name": "Header scrolls with page", "selector": "header", "property": "position", "constraint": "=static"}
```

### Container max-width
```json
{"name": "Content max-width 1280px", "selector": ".container, [class*=container]", "property": "max-width", "constraint": "<=1280px"}
```

### Flex layout direction
```json
{"name": "Nav is horizontal", "selector": "nav", "property": "flex-direction", "constraint": "=row"}
```

### Z-index stacking
```json
{"name": "Sticky header above content", "selector": "header[class*=sticky]", "property": "z-index", "constraint": ">=10"}
```

## Rules

- `name` MUST be copied verbatim from the source spec text.
- Project rules often describe structural conventions that apply across all pages — use `## Scope: any` unless the rule is genuinely route-specific.
- For spacing-system checks, target the elements where the spec explicitly defines spacing values (e.g. `[class*=container]`), not arbitrary elements.
- If the spec defines breakpoint-specific behavior, verify at the current viewport. Note viewport assumptions in the report — verify_* doesn't change viewport size.
- Avoid redundancy: if a property is in `visual-style.md` (e.g. body color), don't duplicate it here. Keep `project-rules.md` for structural/layout properties.

## Example Call

```
verify_project_rules(
  session_id="bd89560b-8745-4a34-a513-05f763614870",
  rules="[{\"name\": \"Header height | 80px | Consistent across pages\", \"selector\": \"header\", \"property\": \"height\", \"constraint\": \"=80px\"}]",
  output_dir="/Users/you/my-project"
)
```
