# Spec Authoring

Design specs are markdown files that define the visual contract for your application. The verification skill reads these specs and translates each claim into a testable rule.

## Spec File Structure

Each project has up to 5 spec files, one per category:

| File | Category | What to document |
|---|---|---|
| `visual-style.md` | Visual Style | Colors, typography, spacing, radii, shadows |
| `component-rules.md` | Components | Button variants, card styles, form elements |
| `accessibility.md` | Accessibility | Required roles, landmarks, aria attributes |
| `project-rules.md` | Project Rules | Layout conventions, spacing system, positioning |
| `platform-conventions.md` | Platform Conventions | Navigation structure, page sections, content patterns |

## Writing Verifiable Claims

Each claim in your spec should be a single, testable assertion. The skill copies the claim text verbatim as the rule `name`, so write claims as self-contained descriptions.

### Good claims (directly testable)

```markdown
| Brand Cyan | #06b6d4 | rgb(6, 182, 212) | Primary CTA, active link |
| Body / UI text | 16px | 400 | 24px | normal |
| Header position | static | Not fixed or sticky — scrolls with page content |
```

### Weak claims (hard to test deterministically)

```markdown
- The page should feel spacious
- Colors should be on-brand
- Layout should be responsive
```

Weak claims can't be converted to CSS checks. Rewrite them with specific values.

## Format Options

### Table format (recommended)

Tables work best for dense specs with repeated structure:

```markdown
## Color Palette

| Token | Hex | RGB | Usage |
|---|---|---|---|
| Brand Cyan | #06b6d4 | rgb(6, 182, 212) | Primary CTA, active link, accent |
| Ink | #f8fafc | rgb(248, 250, 252) | Primary text, headings, button labels |
| Canvas Deep | #0a0e1a | rgb(10, 14, 26) | Page background, card surfaces |
```

### Bullet format

For one-off rules or constraints:

```markdown
## Typography Rules

- No uppercase text-transform anywhere in the system
- Body text is always 16px, weight 400
- Headings use font-weight 600 or higher
```

### Prose with values

For narrative specs that embed testable values:

```markdown
The header is 80px tall and uses static positioning (scrolls with the page).
The page canvas uses Canvas Deep (#0a0e1a / rgb(10, 14, 26)) on the landing page.
```

## Tips for Maximum Coverage

1. **Include both hex and RGB** for colors — the skill uses RGB since that's what `getComputedStyle()` returns
2. **Specify units** — "16px" not "16". The browser computes in px.
3. **Name your variants** — "Ghost / Tab" is better than "tab button" for disambiguation
4. **One assertion per row/bullet** — compound claims ("16px bold centered") should be split into three rows
5. **Scope elements** — "header h1" not just "h1" when the rule only applies in a specific context

## Scoping (three dimensions)

Design intent can be scoped at three different levels — same chat or design.md statement applies in different ways depending on what the user means:

| Dimension | What it scopes | How it's expressed | Example user intent |
|---|---|---|---|
| **Site** | Which app/site is being verified | The URL passed to `start_browse` | "verify https://example.com/app" |
| **Route** | Which URL paths within the site | `## Scope: route=<glob>` section in a category file | "landing has a dark canvas, app has a white canvas" |
| **Page section / region** | Which part of a page (header, footer, modal, sidebar) | A scoped CSS selector inside the rule itself: `header [role=search] button` instead of bare `button` | "header search button is cyan", "footer links are 14px" |

The first two are explicit (URL + glob heading). The third is implicit in the selector — a selector like `footer h2` is a section-scoped rule by virtue of including the landmark in its CSS path. Prefer landmark-scoped selectors (`header h2`, `footer .links`, `[role=dialog] button`) over bare tag/class selectors when the user's intent is region-specific.

## Route-Scoped Rules

Some design intent applies to specific routes only — the landing page has a dark canvas, the app has a white canvas, modals have an elevated surface. The same `body` element shows up on every page, so a single rule with selector `body` and constraint `white` would contradict the landing page rule on `/landing`.

Category files express this with **scope sections**. Each category file can have one default `## Scope: any` section plus any number of `## Scope: route=<glob>` sections. Rules under a route scope only run when the current URL matches the glob.

```markdown
# Visual Style

## Scope: any (default — applies to all pages)

| Name | Selector | Property | Constraint |
|---|---|---|---|
| Body font: Inter | body | font-family | contains:Inter |
| Modal surface | [role=dialog] | background-color | white |

## Scope: route=/

| Name | Selector | Property | Constraint |
|---|---|---|---|
| Landing canvas | body | background-color | ~rgb(10,14,26) |

## Scope: route=/app/*

| Name | Selector | Property | Constraint |
|---|---|---|---|
| App canvas | body | background-color | white |
```

**Supported scope syntax:**

| Scope | Matches | Example |
|---|---|---|
| `any` | every URL visited (the default — same as no section heading at all) | font-family on `body`, modal styles |
| `route=<glob>` | URL path matches glob (`*` matches one segment, `**` matches across segments) | `route=/app/*`, `route=/posts/**` |

**When to use scope vs more specific selectors:**

- Prefer a **discriminating selector** when the DOM provides one (`body[data-route=landing]`, `.app-shell`). It's stable across navigation and doesn't require the verifier to track URLs.
- Use a **route scope** when no DOM discriminator exists, or when the same rule applies app-wide except on specific routes (e.g. landing overrides the global canvas).

The empty/default case stays simple: a category file with no `## Scope:` headings is treated as `## Scope: any` — exactly today's flat behavior. You only adopt scope sections when route-specific rules actually exist.

## File Locations

**Source spec (`design.md`)** — human-authored, required:
- `<project_root>/visual/design.md` (default)
- `<project_root>/.ui-verification/design.md` (alternative — keeps everything under the dot-directory)
- Or any path the user names explicitly

**Compiled category files** (output of the Compiler — do not hand-edit):
```
<project_root>/.ui-verification/specs/
  visual-style.md
  component-rules.md
  accessibility.md
  project-rules.md
  platform-conventions.md
```

The Compiler writes these from `design.md`. Category files are clean markdown (no frontmatter); compile-state integrity is tracked separately in `<output_dir>/.ui-verification/.integrity.json`. See `references/spec_sync.md` § Integrity Ledger.

## Iterating on Specs

After a verification run:
1. Review failures — some may indicate spec claims that need updating (design changed since spec was written)
2. Review "selector not found" errors — the CSS selector in the rule doesn't match any visible elements. Update the selector.
3. Add missing claims — the tool only checks what's in the spec. If a visual aspect isn't specified, it won't be verified.

When `design.md` hasn't changed since the last compile, the agent reuses the existing category files (per `verification.md` step 4) — no re-compilation needed.

## Generating Specs Automatically

If you don't have specs yet, the skill can generate them by observing the live site. See `references/spec_generation.md` for the full workflow. Generated specs capture the current state — edit them to reflect your intended design.
