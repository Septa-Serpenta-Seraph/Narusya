# "I'm not seeing any changes" — stale-page / cache debugging (PIPNARU 8/20)

The most confusing failure mode for a self-hosted dashboard: the server
verifiably serves the NEW code, but the user's screen keeps showing the OLD
panel no matter how many refreshes. Two real causes, checked in order.

## Cause 1 — stale standalone pages the user is actually pointed at

When an app evolves (single `x.html` → tabbed `index.html` + `tabs/`), the old
single-page files often linger and keep being served. The user's bookmark / open
tab may be on `body-panel.html` or `pipboy.html` — a frozen snapshot with NONE
of the new features.

Diagnose by recognizing WHICH FILE the URL serves, not just "the server works":
grep the *served* files for a marker of the new feature:
```
curl :<port>/tabs/log.html | grep -c lWeedAdd     # >0  → new code IS live
curl :<port>/body-panel.html | grep -c lWeedAdd    #  0  → a stale file
```

Fix: delete the stale files so they 404 — removes the wrong doors the user can
wander into.

## Cause 2 — browser cache held a pre-change copy

Force no-store on the server by overriding `end_headers()` in the handler. A
plain refresh then can never serve a cached stale copy:
```python
def end_headers(self):
    self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
    self.send_header("Pragma", "no-cache")
    self.send_header("Expires", "0")
    super().end_headers()
```

## Make it self-diagnosable for the user

- Bump a visible version string (e.g. brand `PIP-NARU 4.2` → `4.3`) so the user
  has a one-glance marker that they're on the fresh build.
- Give the exact root URL (ending `/`, nothing after) and mention
  private-tab / hard-reload as the fastest one-time way around a stubborn cache.

## Lesson pattern

When a user reports a change "not showing" but the code is verifiably served:
it is almost never that the edit didn't land — it's that what they're viewing
isn't the file you edited. Name the stale path (an old HTML file, or a cached
copy), then eliminate both possible stale sources.
