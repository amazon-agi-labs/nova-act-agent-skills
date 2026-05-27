# Constraint Reference

The `constraint` field in each rule defines how the actual computed CSS value is evaluated. All constraints operate on the string returned by `getComputedStyle()`.

## Constraint Syntax

| Constraint | Meaning | Example |
|---|---|---|
| `=value` | Exact match (case-sensitive) | `=14px` |
| `!=value` | Must not equal | `!=rgb(0,0,0)` |
| `>=N` | Greater or equal (numeric, strips units) | `>=600` |
| `<=N` | Less or equal | `<=16px` |
| `>N` | Greater than | `>0px` |
| `<N` | Less than | `<100px` |
| `~rgb(R,G,B)` | Color within ±10 per channel | `~rgb(34,34,34)` |
| `red-spectrum` | R>180, G<120, B<120 | |
| `red` | Alias for `red-spectrum` | |
| `blue-spectrum` | B>180, R<120, G<120 | |
| `blue` | Alias for `blue-spectrum` | |
| `green-spectrum` | G>180, R<120, B<120 | |
| `green` | Alias for `green-spectrum` | |
| `dark` | Average RGB < 80 | |
| `light` | Average RGB > 200 | |
| `white` | All channels > 240 | |
| `transparent` | rgba(0,0,0,0) or "transparent" | |
| `contains:X` | Value contains substring (case-insensitive) | `contains:Inter` |
| `!contains:X` | Value does NOT contain substring | `!contains:serif` |

## Numeric Constraints

Numeric constraints strip units before comparing. `>=600` matches `600`, `700`, `14px`, `16rem` (all parsed as their numeric portion).

**Negative numbers are supported.** `<=-1px` matches `-1.28px` (because `-1.28 <= -1`). The minus sign is preserved through unit-stripping. `>=-2em` matches `-1px`, `0px`, `2em` (anything `>= -2`).

**Decimals are supported.** `<=16.5px` matches `16.4px` and below. Numeric parsing uses standard floating-point comparison, not integer truncation.

Works with: font-weight, font-size, line-height, letter-spacing (including negative values for tightened tracking), margin, padding, width, height, border-radius, gap, z-index, opacity.

## Color Constraints

### Tolerance matching: `~rgb(R,G,B)` — and the rgba trap

**One rule for all colors, regardless of alpha.** Use `~rgb(R,G,B)` whether the DOM ships the color as `rgb(...)` or `rgba(...)`. The engine has different parsers on the two sides of the comparison:

| Side | Regex | What it accepts |
|---|---|---|
| Constraint (what you write) | `/rgb\((\d+),\s*(\d+),\s*(\d+)\)/` | ONLY `rgb(R,G,B)` — no `a`, requires closing `)` |
| Actual (what `getComputedStyle` returns) | `/rgba?\((\d+),\s*(\d+),\s*(\d+)/` | Both `rgb(...)` and `rgba(...)` — the `a?` is optional, no closing `)` required |

Because the actual-side regex stops parsing after the third channel, alpha (if present) is read past and ignored. The engine then compares the three RGB integers within ±10 tolerance. Alpha is never compared.

So this all works:

```
constraint: ~rgb(R, G, B)
actual:     rgb(R, G, B)             → PASS  (channels match)
actual:     rgba(R, G, B, 1)         → PASS  (channels match, alpha ignored)
actual:     rgba(R, G, B, 0.6)       → PASS  (channels match, alpha ignored)
actual:     rgba(R, G, B, 0)         → PASS  (channels match, alpha ignored)
actual:     rgb(R±10, G±10, B±10)    → PASS  (within tolerance)
actual:     rgb(R±50, G, B)          → FAIL  (channel out of tolerance)
```

**The rgba trap** — `~rgba(R,G,B,A)` is **NOT supported and ALWAYS fails.** Why this trips agents up:

1. The constraint's startsWith check is `"~rgb("` — and `"~rgba(..."` also starts with `"~rgb"`, so the engine enters the `~rgb` branch.
2. The expected-side regex then requires `rgb(...)` with a closing `)` immediately after the B channel. `~rgba(R,G,B,A)` has `,A)` after B, not `)` — regex fails to match.
3. Engine short-circuits to `{pass: false}`. Rule fails.
4. The failure detail still reports the actual value back, e.g. `{actual: "rgba(R, G, B, 0.95)"}`. **This is the trap.** The agent sees actual=`rgba(...)` and constraint=`~rgba(...)` and thinks "the alpha doesn't match" or "the engine doesn't quite handle alpha" — and starts editing the rule or chasing the cascade. The real problem is that the constraint syntax is rejected upstream of any value comparison; the actual value is irrelevant to the failure.

**If you find yourself writing `~rgba(...)`, two options based on what you actually want to assert:**

| You want to check | Use |
|---|---|
| "this element renders the brand color" — alpha doesn't matter | `~rgb(R,G,B)` constraint. Channels ±10, alpha ignored. The most common case. |
| "this element renders the brand color at exactly alpha 0.95" — alpha is a meaningful part of the design constraint | `evaluate_js` — read the value, parse alpha, compare. The constraint engine has no alpha syntax. |

The first case is what most rules want. A token like `colors.brand-primary` defined once means the same color regardless of whether it's applied at full opacity in a button or 60% in an overlay panel — so checking R, G, B and ignoring alpha matches design intent. The second case is rarer (the design specifies "this overlay must be at exactly 95% opacity") and warrants the more expensive `evaluate_js` path.

**Don't reach for `evaluate_js` for the first case** just because you noticed `rgba()` in the actual value. The `~rgb(R,G,B)` constraint handles `rgba(...)` actuals natively (the actual-side regex parses past the third channel and the engine ignores the alpha). Native constraint > JS for color-identity checks: faster, deterministic, less surface for `evaluate_js` syntax bugs.

Example: a token defined as `#222222` (or `rgba(34,34,34,0.6)` in some component's use) → constraint `~rgb(34,34,34)` matches both `rgb(34, 34, 34)` and `rgba(34, 34, 34, 0.6)` in the DOM.

### Spectrum constraints
For loose color category checks when exact values aren't specified:
- `red-spectrum` (or `red`) — the color is predominantly red
- `blue-spectrum` (or `blue`) — predominantly blue
- `green-spectrum` (or `green`) — predominantly green
- `dark` — very dark (near black)
- `light` — very light (near white)
- `white` — effectively white (all channels > 240)
- `transparent` — fully transparent

Note: spectrum constraints only work when the actual value is in `rgb(R, G, B)` format (which `getComputedStyle()` always returns for color properties).

## String Constraints

### Substring: `contains:X`
Case-insensitive substring match. Good for font-family checks where the computed value includes fallbacks.

Example: `contains:Inter` matches `"Inter", -apple-system, sans-serif`

### Not contains: `!contains:X`
Verify a value does NOT include a substring.

Example: `!contains:serif` ensures no serif fonts are used.

## Default Matching

If no constraint prefix is recognized, the constraint is compared as an exact case-sensitive string match against the actual value.

## Unsupported Constraints

The constraint engine does NOT support these — using them produces unexpected behavior (silent fallback to exact-string comparison, which always fails for non-trivial values):

- `starts:X` — substring at start (use `contains:X` and rely on the position pattern of the value, or use `evaluate_js`)
- `A|B|C` — pipe-separated alternatives (write one rule per alternative, or use `evaluate_js`)
- `regex:pattern` — regex match (use `evaluate_js` with `String.prototype.match()`)

For checks beyond the supported set, drop down to `evaluate_js(session_id, script)` and run the comparison in the page context. **This file is the authoritative agent-facing list of what's supported.** Do NOT `find` the MCP server source to confirm engine behavior — the table above is the contract. If the table is wrong or incomplete for what you observe in practice, surface to the user as a doc bug rather than spelunking the engine implementation.

## Choosing the Right Constraint

| Spec says | Use |
|---|---|
| "color is #ff385c" | `~rgb(255,56,92)` (hex → rgb with tolerance) |
| "font-size is 14px" | `=14px` (exact) |
| "font-weight at least 600" | `>=600` (numeric) |
| "no uppercase anywhere" | `!=uppercase` (not equal) |
| "uses Inter font" | `contains:Inter` (substring, handles fallbacks) |
| "border-radius 50%" | `>=50%` (numeric, handles `50%` vs `50.00%`) |
| "background is white" | `white` (semantic color) |
| "background is transparent" | `transparent` (semantic) |
| "text is dark colored" | `dark` (spectrum) |

## For Checks Beyond Constraints

If the constraint engine can't express what you need, use `evaluate_js(session_id, script)` to run arbitrary JavaScript. Common cases:
- Element counting
- Cross-element comparisons
- Computed values requiring math (contrast ratios)
- Attribute presence checks (alt text, aria attributes)
- Structural ordering checks
