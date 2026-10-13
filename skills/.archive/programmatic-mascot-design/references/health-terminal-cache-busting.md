# Tabbed self-hosted terminal: cache-busting + multi-script tab loader

Pattern from PIPNARU (`~/body-panel`, stdlib `http.server`, Tailnet-only). Applies to any
tabbed single-page UI whose tab bodies are fetched as HTML fragments with inline scripts.

## The bug: tab loader only ran the FIRST script block

A tab file like `tabs/data.html` can contain several `<script>` blocks (e.g. one each for
Visible import, FatigueSense import, body-map/system refresh). The first version of the loader did:

```js
const m = html.match(/<script>([\s\S]*?)<\/script>/);   // only FIRST block
```

So only the first block executed; everything else froze at "loading...".
**Fix — collect and run EVERY block:**

```js
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
document.getElementById('main').innerHTML = html.replace(/<script>[\s\S]*?<\/script>/g, '');
for (const js of scripts) { try { (0, eval)(js); } catch (e) { console.error('tab script', name, e); } }
```

## Cache-busting: three layers (all needed, in order)

1. **No-cache headers on the server** — override `end_headers()` in the `SimpleHTTPRequestHandler`:
   `Cache-Control: no-store, no-cache, must-revalidate, max-age=0` + `Pragma: no-cache` + `Expires: 0`.
   Stops *future* caching; does NOT evict already-cached files.
2. **Per-version cache-buster on tab fetches** — `fetch('tabs/' + name + '.html?v=4.3')`.
   The `?v=` creates a brand-new URL per version, so browsers that cached the pre-header tab files
   are forced to refetch when the version bump happens. Update the version string in BOTH the
   brand label and the fetch every release.
3. **Hard refresh on the client** for leftover stale tabs (pull-to-refresh / Ctrl+Shift+R /
   close-tab-reopen / private tab). Sometimes still needed once per device after adding the headers.

## Symptom → diagnosis

- Root page shows new version but a tab shows old content → that *tab's* fragment was cached
  before the no-cache headers existed; bump version + add `?v=` (layers 1+2).
- User sees "no changes" while server serves everything fine → they're on a stale page or
  a deleted-now-stale sibling file (e.g. an old single-page `body-panel.html` next to the new
  `index.html`). Delete the stale files so there are no wrong doors; verify with `curl` that
  the old paths 404.
- Always verify with `curl` against localhost: what version string is served, are the cache
  headers present, do stale URLs 404.

## Verification recipe

```bash
curl -s http://localhost:8765/ | grep -i "PIP-NARU"            # version served
curl -s -D - -o /dev/null http://localhost:8765/ | grep -i cache  # headers
curl -s -o /dev/null -w "%{http_code}" http://localhost:8765/body-panel.html  # stale → 404
```