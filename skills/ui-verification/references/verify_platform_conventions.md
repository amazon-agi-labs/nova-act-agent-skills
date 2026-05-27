# Verify Platform Conventions

Deep-dive for the `platform_conventions` category: navigation patterns, page structure, content patterns. Complements `references/verification.md` — does not replace it. The full workflow lives there.

**Tool:** `verify_platform_conventions(session_id, rules, output_dir)` — always pass `output_dir` (absolute path to project root)
**Spec file:** `<output_dir>/.ui-verification/specs/platform-conventions.md`
**Source of truth upstream:** `design.md` (intentional layer; the category file is compiled from it — see `references/spec_sync.md`)
**Artifact:** `<output_dir>/.ui-verification/sessions/<session_id>/platform_conventions_assertions.json`

## What This Covers

- **Navigation patterns:** presence and structure of navbars, tab bars, breadcrumbs, sidebars
- **Page structure:** header / content / footer arrangement, expected sections
- **Content patterns:** expected element groupings (card grids, list layouts, hero sections)
- **Interactive patterns:** search bars, filter controls, pagination

## Translation Table

How to translate spec claims (from design.md → compiled into `platform-conventions.md`) into rules.

| Spec text (copy VERBATIM as `name`) | selector | property | constraint |
|---|---|---|---|
| "Top nav: role=tablist with 3-7 role=tab children" | `[role=tablist]` | `display` | `!=none` |
| "Search bar: visible in header on every page" | `header [role=search], header [class*=search]` | `display` | `!=none` |
| "Footer: 3-column link grid (Support · Resources · About)" | `footer` | `display` | `!=none` |
| "Logo: left-aligned in header" | `header img, header svg, header [class*=logo]` | `display` | `!=none` |
| "Hero section present on landing" | `[class*=hero], section:first-of-type` | `display` | `!=none` |

## Scope

A rule's scope comes from the `## Scope:` section it lives under in `platform-conventions.md`. App-wide navigation (header, search bar, footer) goes under `## Scope: any`. Page-specific patterns (the hero section, a landing-only banner) go under `## Scope: route=/` or similar. See `references/spec_authoring.md` § Route-Scoped Rules.

## Common Patterns (use evaluate_js for relationships and counts)

### Element count
For "tablist has 3-7 tabs":
```
evaluate_js(session_id, "(() => { const n = document.querySelectorAll('[role=tablist] [role=tab]').length; return {count: n, pass: n >= 3 && n <= 7}; })()")
```

### Element ordering
For "logo appears before search in header":
```
evaluate_js(session_id, "(() => { const h = document.querySelector('header'); if (!h) return {pass: false, reason: 'no header'}; const l = h.querySelector('img, svg, [class*=logo]'); const s = h.querySelector('[role=search], [class*=search]'); if (!l || !s) return {pass: false, reason: 'missing logo or search'}; return {pass: l.getBoundingClientRect().left < s.getBoundingClientRect().left}; })()")
```

### Section presence
```json
{"name": "Hero section present", "selector": "[class*=hero], section:first-of-type", "property": "display", "constraint": "!=none"}
```

## Rules

- `name` MUST be copied verbatim from the source spec text.
- Platform conventions mix presence checks (element exists) with structural checks (element has N children, element ordering). Use `verify_platform_conventions` for presence; use `evaluate_js` for counts and relationships.
- For claims that span multiple pages ("search bar on every page"), put the rule under `## Scope: any` — the agent runs it on every URL it visits during verification.
- For multi-page verification, see `references/verification.md` § Multi-Page Verification — the agent navigates to each scoped URL and runs the applicable rules.

## Example Call

```
verify_platform_conventions(
  session_id="bd89560b-8745-4a34-a513-05f763614870",
  rules="[{\"name\": \"Search bar: visible in header on every page\", \"selector\": \"header [role=search], header [class*=search]\", \"property\": \"display\", \"constraint\": \"!=none\"}]",
  output_dir="/Users/you/my-project"
)
```
