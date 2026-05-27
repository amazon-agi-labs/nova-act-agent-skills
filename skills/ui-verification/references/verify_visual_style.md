# Verify Visual Style

Deep-dive for the `visual_style` category: colors, typography, spacing, border radii, shadows. Complements `references/verification.md` — does not replace it. The full workflow (open session → compile → verify → annotate → report) lives there.

**Tool:** `verify_visual_style(session_id, rules, output_dir)` — always pass `output_dir` (absolute path to project root)
**Spec file:** `<output_dir>/.ui-verification/specs/visual-style.md`
**Source of truth upstream:** `design.md` (intentional layer; the category file is compiled from it — see `references/spec_sync.md`)
**Artifact:** `<output_dir>/.ui-verification/sessions/<session_id>/visual_style_assertions.json`

## What This Covers

- **Colors:** background-color, color, border-color, outline-color
- **Typography:** font-size, font-weight, font-family, line-height, letter-spacing, text-transform, text-decoration
- **Spacing:** margin, padding (all sides), gap
- **Radii:** border-radius (all corners)
- **Shadows:** box-shadow (use `contains:` constraint for partial matching)

## Translation Table

How to translate spec claims (from design.md → compiled into `visual-style.md`) into rules. The `name` field is copied verbatim from the source spec text — do NOT paraphrase.

| Spec text (copy VERBATIM as `name`) | selector | property | constraint |
|---|---|---|---|
| "Brand Cyan \| #06b6d4 \| rgb(6, 182, 212) \| Primary CTA, active link" | `[class*=primary],[class*=cta]` | `color` | `~rgb(6,182,212)` |
| "Ink \| #f8fafc \| rgb(248, 250, 252) \| Primary text, headings" | `body` | `color` | `~rgb(248,250,252)` |
| "Canvas Deep \| #0a0e1a \| rgb(10, 14, 26) \| Page background" | `body` | `background-color` | `~rgb(10,14,26)` |
| "Body / UI text \| 16px \| 400 \| 24px \| normal" | `body` | `font-size` | `=16px` |
| "No uppercase text-transform anywhere" | `h1,h2,h3,h4,p,span,a,button` | `text-transform` | `!=uppercase` |
| "8px \| The base interactive radius" | `button` | `border-radius` | `>=8px` |

## Scope

A rule's scope (`any` or `route=<glob>`) comes from the `## Scope:` section it lives under in `visual-style.md`. The MCP server doesn't see scope — the agent filters rules by current URL before calling `verify_visual_style`. Assertion JSON returned by the MCP server is write-once; scope is joined back in at report-time from the category file (see `references/verification_report.md`).

A rule that conceptually applies app-wide goes under `## Scope: any` (or a flat file with no scope sections). A rule that's route-specific (e.g. landing-only canvas color) goes under `## Scope: route=/`. See `references/spec_authoring.md` § Route-Scoped Rules.

## Constraint Choice

| Spec says | Use |
|---|---|
| Hex color (`#0a0e1a`) | `~rgb(10,14,26)` (hex → rgb with ±10 tolerance) |
| Exact size (`14px`) | `=14px` |
| At-least size or weight (`>= 600`) | `>=600` |
| Negative ("no uppercase") | `!=uppercase` |
| Font family (with fallbacks) | `contains:Inter` |
| Percentage (`50%`) | `>=50%` |
| Semantic color | `white`, `dark`, `light`, `transparent` |

Full table: `references/constraint_reference.md`. Constraints like `starts:`, `A|B|C`, and `regex:` are not supported — use `evaluate_js` for those.

## Rules

- `name` MUST be copied verbatim from the source spec text. Names are the warm-start diff key — paraphrasing breaks change detection.
- Extract EVERY verifiable claim from the matching `## Scope:` section. Do not skip claims that seem obvious.
- Use specific selectors. Never use `*`. Prefer `h1,h2,h3,p,span,a,button` for text checks.
- For "never" rules, scope broadly from general web knowledge — let `verify_*` find actual violations. Do not pre-discover with `evaluate_js`.
- When a spec defines scoped variants (e.g., content H2 vs footer H2), use scoped CSS selectors: `main h2` vs `footer h2`. CSS scoping is independent from route scope.

## Example Call

```
verify_visual_style(
  session_id="bd89560b-8745-4a34-a513-05f763614870",
  rules="[{\"name\": \"Body / UI text | 16px | 400 | 24px | normal\", \"selector\": \"body\", \"property\": \"font-size\", \"constraint\": \"=16px\"}, {\"name\": \"Canvas Deep | #0a0e1a | rgb(10, 14, 26) | Page background\", \"selector\": \"body\", \"property\": \"background-color\", \"constraint\": \"~rgb(10,14,26)\"}]",
  output_dir="/Users/you/my-project"
)
```

## Reporting Failures

For each failure, state:
- What the spec says (the `name` verbatim)
- What the page actually has (from `failures[].actual`)
- Which elements are affected (from `failures[].element`)
- If a single component fix would resolve multiple failures, call that out

Annotation + screenshot generation is handled by the report step — see `references/verification_report.md` and `references/annotate_failures.md`.
