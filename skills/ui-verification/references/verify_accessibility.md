# Verify Accessibility

Deep-dive for the `accessibility` category: ARIA roles, landmarks, heading hierarchy, accessibility attributes. Complements `references/verification.md` — does not replace it. The full workflow lives there.

**Tool:** `verify_accessibility(session_id, rules, output_dir)` — always pass `output_dir` (absolute path to project root)
**Spec file:** `<output_dir>/.ui-verification/specs/accessibility.md`
**Source of truth upstream:** `design.md` (intentional layer; the category file is compiled from it — see `references/spec_sync.md`)
**Artifact:** `<output_dir>/.ui-verification/sessions/<session_id>/accessibility_assertions.json`

## What This Covers

- **Landmarks:** header, main, nav, aside, footer, form, region
- **ARIA roles:** alert, alertdialog, dialog, tablist, tab, tabpanel, menu, menuitem, tree, treeitem, search, status, log, timer, navigation
- **Heading hierarchy:** h1-h6 presence and ordering
- **Required attributes:** aria-label, aria-labelledby, aria-describedby, aria-expanded, aria-selected, aria-controls

## Translation Table

How to translate spec claims (from design.md → compiled into `accessibility.md`) into rules.

| Spec text (copy VERBATIM as `name`) | selector | property | constraint |
|---|---|---|---|
| "navigation \| Primary nav landmark wrapper" | `[role=navigation], nav` | `display` | `!=none` |
| "search \| Search-bar landmark wrapper" | `[role=search]` | `display` | `!=none` |
| "main \| Primary page content" | `main` | `display` | `!=none` |
| "header \| Contains logo, primary nav" | `header` | `display` | `!=none` |
| "alert \| Inline status / error messages" | `[role=alert]` | `display` | `!=none` |

## Scope

A rule's scope comes from the `## Scope:` section it lives under in `accessibility.md`. App-wide landmarks (`header`, `main`, `footer`) belong under `## Scope: any`. Route-specific landmarks — e.g. a `[role=tablist]` that only appears on a settings page — belong under `## Scope: route=/settings/**`. See `references/spec_authoring.md` § Route-Scoped Rules.

## Common Patterns

### Landmark presence
```json
{"name": "main | Primary page content", "selector": "main", "property": "display", "constraint": "!=none"}
```

`display: !=none` is the canonical "this landmark is on the page and not hidden" check. Elements hidden via `display: none` are not in the accessibility tree.

### Heading hierarchy
For "single h1 per page":
```json
{"name": "Single h1 per page", "selector": "h1", "property": "display", "constraint": "!=none"}
```
This only verifies presence. Uniqueness ("exactly one h1") needs `evaluate_js`:
```
evaluate_js(session_id, "document.querySelectorAll('h1').length === 1")
```

### Tab counts
For "tablist has at least 5 tabs", presence goes through `verify_accessibility`; count goes through `evaluate_js`:
```
evaluate_js(session_id, "document.querySelectorAll('[role=tablist] [role=tab]').length >= 5")
```

### Attribute-value presence (the `[attr=value]` pattern)

`verify_accessibility` runs `getComputedStyle` checks — it does NOT introspect HTML attributes directly. A naive rule like `{selector: "html", property: "lang", constraint: "=en"}` will fail with `actual: "no value"` because `lang` is an HTML attribute, not a CSS property.

The workaround: use the attribute-value as a **CSS attribute selector** and check `display: !=none`. The selector matches only elements whose attribute equals the expected value, and `display: !=none` confirms that element is on the page.

```json
{"name": "Document declares language: en", "selector": "html[lang=en]", "property": "display", "constraint": "!=none"}
{"name": "Header has search role", "selector": "header [role=search]", "property": "display", "constraint": "!=none"}
{"name": "Logo button is labelled", "selector": "button[aria-label='Home']", "property": "display", "constraint": "!=none"}
{"name": "Cards expose card role", "selector": "[role=group][aria-roledescription='card']", "property": "display", "constraint": "!=none"}
```

This works for any attribute (`lang`, `role`, `aria-*`, `data-*`, `alt`, etc.) where the expected value is known and finite. For "attribute exists with any value" use `[attr]` without the equals; for "attribute is non-empty" use `[attr]:not([attr=''])`.

For attributes whose expected value is open-ended or computed (e.g. "every image has SOME alt, not just empty string"), drop to `evaluate_js` — the attribute selector pattern only works when you're matching against a specific expected value.

## When to Use evaluate_js

`verify_accessibility` is for presence, basic property checks, and the `[attr=value]` selector pattern (above). Reach for `evaluate_js` for:
- **Counts** — "page has at least 3 headings", "tablist has 5+ tabs"
- **Open-ended attribute presence** — "all images have NON-EMPTY alt" (not a fixed expected value)
- **Contrast ratios** — text/background contrast > 4.5:1 (compute from `getComputedStyle`)
- **Focus order** — focusable elements follow logical tab order
- **ARIA relationships** — every `aria-labelledby` references an existing element id
- **Heading order validation** — h1 → h2 → h3 (no skipping)

## Rules

- `name` MUST be copied verbatim from the source spec text.
- Use `display: !=none` for landmark/role presence checks. Hidden landmarks aren't accessible.
- Distinguish "role exists somewhere on page" (`[role=X]`) from "specific element has role" (use a more targeted selector like `header [role=search]`).
- If the spec mixes presence + count (e.g. "tablist with 5 tabs"), split: presence via `verify_accessibility`, count via `evaluate_js`. One claim per rule.

## Example Call

```
verify_accessibility(
  session_id="bd89560b-8745-4a34-a513-05f763614870",
  rules="[{\"name\": \"main | Primary page content\", \"selector\": \"main\", \"property\": \"display\", \"constraint\": \"!=none\"}]",
  output_dir="/Users/you/my-project"
)
```
