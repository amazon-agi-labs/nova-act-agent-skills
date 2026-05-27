# Annotate Failures

Visually annotate failing elements on the page and capture a screenshot. This is a **reporting step** — run it after all verify_* calls are complete.

## How It Works

Injects a transparent overlay div (fixed position, pointer-events: none, max z-index) and draws bounding boxes inside it. Never modifies existing DOM elements or their computed styles — verify_* tools remain accurate if called again.

## Usage

After verify_* tools report failures:
1. Build a failures array where each failure has a `selector` and a `number` (1-indexed, one per rule). The number is the join key between the screenshot and the report's failure table.
2. Call `evaluate_js(session_id, script)` with the annotation script below.
3. Call `screenshot(session_id)` to capture the annotated view.
4. Render the report's failure table with the same numbers — see `references/verification_report.md`.

The screenshot shows red boxes with small numbered badges. The legend (number → rule, selector, count) is rendered as a markdown table in the test report, NOT drawn onto the screenshot.

## Annotation Script

```javascript
(() => {
  // Remove any previous annotation overlay
  const existing = document.getElementById('__vv_overlay');
  if (existing) existing.remove();

  // Create overlay — fixed, covers viewport, no pointer interaction
  const overlay = document.createElement('div');
  overlay.id = '__vv_overlay';
  overlay.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:2147483647;';
  document.body.appendChild(overlay);

  // Content-aware bounding box: for block elements spanning full viewport width,
  // use the tightest rect around actual content (text/children) instead.
  function getContentRect(el) {
    const rect = el.getBoundingClientRect();
    const vw = window.innerWidth;

    // If element width is >= 90% of viewport, it's likely a block-level container.
    // Try to get tighter bounds from its inline content or children.
    if (rect.width >= vw * 0.9) {
      // Try Range-based text bounds first (tightest for text-bearing elements)
      const range = document.createRange();
      range.selectNodeContents(el);
      const rects = range.getClientRects();
      if (rects.length > 0) {
        let minLeft = Infinity, minTop = Infinity, maxRight = -Infinity, maxBottom = -Infinity;
        for (const r of rects) {
          if (r.width === 0 && r.height === 0) continue;
          minLeft = Math.min(minLeft, r.left);
          minTop = Math.min(minTop, r.top);
          maxRight = Math.max(maxRight, r.right);
          maxBottom = Math.max(maxBottom, r.bottom);
        }
        if (minLeft !== Infinity) {
          const contentWidth = maxRight - minLeft;
          // Only use content bounds if meaningfully tighter than element bounds
          if (contentWidth < rect.width * 0.8) {
            return {top: minTop, left: minLeft, width: contentWidth, height: maxBottom - minTop};
          }
        }
      }

      // Fallback: use children bounding rects
      if (el.children.length > 0) {
        let minLeft = Infinity, minTop = Infinity, maxRight = -Infinity, maxBottom = -Infinity;
        for (const child of el.children) {
          const cr = child.getBoundingClientRect();
          if (cr.width === 0 && cr.height === 0) continue;
          minLeft = Math.min(minLeft, cr.left);
          minTop = Math.min(minTop, cr.top);
          maxRight = Math.max(maxRight, cr.right);
          maxBottom = Math.max(maxBottom, cr.bottom);
        }
        if (minLeft !== Infinity) {
          const childrenWidth = maxRight - minLeft;
          if (childrenWidth < rect.width * 0.8) {
            return {top: minTop, left: minLeft, width: childrenWidth, height: maxBottom - minTop};
          }
        }
      }
    }

    // Element is already reasonably sized — use as-is
    return {top: rect.top, left: rect.left, width: rect.width, height: rect.height};
  }

  // Failures to annotate: [{selector, number}]
  // - selector: CSS selector for the failed rule
  // - number: 1-indexed rule number, used as the badge text and as the join key
  //           to the report's failure table
  const failures = __FAILURES__;

  const results = [];
  for (const f of failures) {
    const els = document.querySelectorAll(f.selector);
    if (!els.length) {
      results.push({selector: f.selector, number: f.number, annotated: false, reason: 'not found'});
      continue;
    }
    let drawn = 0;
    for (const el of els) {
      const rect = getContentRect(el);
      if (rect.width === 0 && rect.height === 0) continue;

      // Red bounding box (one per failed element — no cap)
      const box = document.createElement('div');
      box.style.cssText = `position:fixed;top:${rect.top}px;left:${rect.left}px;width:${rect.width}px;height:${rect.height}px;border:3px solid red;border-radius:2px;pointer-events:none;`;
      overlay.appendChild(box);

      // Numbered badge in top-left corner of the box
      const badge = document.createElement('div');
      badge.textContent = String(f.number);
      badge.style.cssText = `position:fixed;top:${rect.top}px;left:${rect.left}px;background:red;color:white;font:bold 12px/1 system-ui,sans-serif;padding:3px 6px;min-width:18px;text-align:center;border-radius:2px;pointer-events:none;`;
      overlay.appendChild(badge);

      drawn++;
    }
    results.push({selector: f.selector, number: f.number, annotated: drawn > 0, count: drawn});
  }
  return results;
})()
```

Replace `__FAILURES__` with the actual failure array. Example:

```javascript
const failures = [
  {selector: "header", number: 1},
  {selector: "button.primary", number: 2}
];
```

Each rule gets ONE number. All matched elements for that rule share the same badge number — that's the point. The report's legend maps `1 → "header bg expected dark, got rgb(255,255,255)"` and `2 → "button radius expected >=8px, got 0px"`.

## Workflow

1. Run all verify_* calls. Collect failures from results.
2. Assign a 1-indexed number to each failed rule. Build a `number_to_rule` mapping `{1: {selector, name, expected, actual, count}, 2: ...}` — the report uses this same mapping to render the legend table.
3. Build the failures array for annotation: `[{selector, number}, ...]`.
4. Call `evaluate_js` with the annotation script (failures substituted in).
5. Call `screenshot(session_id)` to capture the annotated viewport.
6. If failures are below the fold: `scroll(session_id, "down")` → re-run annotation for those selectors → screenshot again.
7. Render the legend table in the test report using `number_to_rule` — see `references/verification_report.md`.

## Safety

- The overlay uses `position: fixed` and `pointer-events: none` — it cannot receive clicks, cannot shift layout, cannot affect scroll behavior.
- No existing element's style, class, attributes, or DOM position is modified.
- `getComputedStyle()` on any existing element returns the same values before and after annotation.
- The overlay has id `__vv_overlay` — re-running the script clears the previous overlay first (idempotent).
- verify_* tools can safely be called after annotation without false positives.

## Cleanup

To remove annotations (e.g., before re-running verification):

```javascript
(() => {
  const overlay = document.getElementById('__vv_overlay');
  if (overlay) overlay.remove();
  return {removed: true};
})()
```

## Limitations

- Only annotates elements in the current viewport. Below-fold failures require scrolling and re-annotating.
- Numbered badges may overlap each other if many failures are clustered (e.g. 47 failed buttons in a tight grid). This is acceptable — the spatial extent is still visible from the boxes; the legend in the report carries the per-rule detail.
- Screenshot captures the viewport at current scroll position — not full-page annotated.
- Works for elements that have a non-zero bounding rect. Hidden elements (display:none) cannot be annotated visually.
- Block-level elements (header, footer, h2, section) span full viewport width. The script uses content-aware bounds: it measures the actual text/children content rect and draws the box around that instead of the full block width. If content is still wide (>80% of element width), it falls back to the element rect.
