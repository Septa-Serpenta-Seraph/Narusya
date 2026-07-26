# Dashboard Chat Sizing Fix

## The Bug
When `ChatPage` mounts (off the `/chat` route), the terminal container is `display:none` with 0x0 dimensions. The xterm.js instance calls `fit.fit()` which creates a 1x1 grid. When the route switches to `/chat`, `isActive` becomes `true` and the container is shown, but the grid size never updates because the ResizeObserver measures the wrong dimensions initially.

## The Fix (applied to `web/src/pages/ChatPage.tsx`)

### Before (broken)
```typescript
// Direct synchronous fit — container may still be 0x0
scheduleHostSync();
requestAnimationFrame(() => scheduleHostSync());
```

### After (fixed)
```typescript
// Defer first fit to let browser commit layout
let initialFitTimer: ReturnType<typeof setTimeout> | null = null;
const scheduleInitialFit = () => {
  if (initialFitTimer) clearTimeout(initialFitTimer);
  initialFitTimer = setTimeout(() => {
    initialFitTimer = null;
    syncTerminalMetrics();
  }, 100);
};

// ... later in the effect:
scheduleInitialFit();  // instead of scheduleHostSync()
// double-rAF block remains as belt-and-suspenders
```

### Why 100ms?
- Less than the typical CSS transition duration (150-300ms)
- Guarantees the browser has committed layout after mount
- `display:none` containers report 0x0, so the check in `syncTerminalMetrics` skips hidden containers
- The double-rAF block catches any late CSS transitions

### Cleanup
The timer must be cleared on unmount to avoid calling `fit()` on a disposed terminal:
```typescript
if (initialFitTimer) {
  clearTimeout(initialFitTimer);
  initialFitTimer = null;
}
```

## Debugging Tips
- If the fix doesn't apply, check `chatOverriddenByPlugin` in `App.tsx` — a plugin overriding `/chat` means the built-in ChatPage is not rendered at all.
- The fix is in the initial effect that creates the xterm instance (deps: `[channel, resumeParam]`). Changes to the resume target remount the terminal, which re-runs the effect.
- For rapid testing during development, `npm run build --prefix web && hermes dashboard --stop && hermes dashboard` to rebuild and restart.
