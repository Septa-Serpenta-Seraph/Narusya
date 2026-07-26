# xterm.js Container Sizing in Flex Layouts

**Created:** 2026-06-14
**Source:** Laser's session — Dashboard chat rendering bug

---

## Problem: Terminal Shows Truncated Content

**Symptoms:**
- Terminal renders but only shows a few lines
- Blank space below visible content
- Resizing the browser window fixes the display
- Re-maximizing breaks it again
- Messages send/receive correctly (data is fine)

**Root Cause:** xterm.js's `fit.fit()` reads the container's bounding box at mount time, but the container hasn't yet committed its final size. In flex layouts where the container is `flex-1`, the final height depends on parent containers that haven't measured yet.

### Why the existing fix wasn't enough

The dashboard already used a "double requestAnimationFrame" technique:
```js
requestAnimationFrame(() => {
  requestAnimationFrame(() => {
    fit.fit();
  });
});
```

This handles CSS transitions. But it does NOT handle the case where:
1. The container starts as `display:none` (0×0) at mount time
2. Flex-fill calculates size from viewport
3. The browser hasn't computed the flex dimensions by the time rAFs fire

On maximized windows, this gap is wider because the flex-fill calculation is more complex.

## Fix: Defer Initial Fit

```js
let initialFitTimer = null;
const scheduleInitialFit = () => {
  if (initialFitTimer) clearTimeout(initialFitTimer);
  initialFitTimer = setTimeout(() => {
    initialFitTimer = null;
    syncTerminalMetrics();
  }, 100);
};
scheduleInitialFit();
```

### Why 100ms?

100ms is empirically sufficient for:
- Browser to commit the initial layout
- Fonts to load (JetBrains Mono has `font-display: swap`)
- CSS transitions to complete
- Flex-fill calculations to resolve

The double-RAF block remains as belt-and-suspenders for any additional transitions.

## Diagnostic Steps

1. **Open DevTools** → Console
2. **Check for `[chat] PTY WebSocket` messages** — confirms WS lifecycle
3. **Check for resize events** — does ResizeObserver fire on layout changes?
4. **Measure container** in DevElements: check `clientWidth`/`clientHeight` at mount
5. **Verify `fit.fit()` result** — log `term.cols` and `term.rows` after each fit call
6. **Test resize** — if resizing fixes it, you've confirmed a sizing issue

## Key xterm.js API for Debugging

```js
term.cols;         // number of columns
term.rows;         // number of rows
term.scrollPosition;  // current scroll offset
term.getScrollRange(); // { top: 0, bottom: 5000 }
```

## Related: When ResizeObserver Doesn't Fire

ResizeObserver does NOT fire for:
- `display:none` → `display:flex` transitions
- `visibility: hidden` → `visible` transitions
- Size changes that are smaller than one element pixel

Workaround: Use `setTimeout` or `requestAnimationFrame` to periodically re-measure.
