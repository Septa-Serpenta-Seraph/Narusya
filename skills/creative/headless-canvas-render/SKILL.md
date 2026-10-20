---
name: headless-canvas-render
description: "Render HTML/canvas to PNG when browser_exec is down."
version: 1.0.0
author: Narusya
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [headless, render, canvas, png, camoufox, playwright, screenshot, generative-art]
    related_skills: [p5js, browser-tool-self-repair, browser-tool-troubleshooting]
---

# Headless Canvas → PNG Render Pipeline

## When to use

- `browser_exec` fails with `BU_CDP_URL=http://localhost:9377 unreachable after 30s: HTTP Error 404: Not Found`
- You need a real raster of an HTML/canvas/p5.js piece and the browser tool is unavailable
- Any time you must produce an actual image artifact (PNG/JPG) from browser-side JS

## Why browser_exec fails here (root cause)

The Camoufox server on :9377 is a **proxy**, not a raw CDP endpoint. It only serves:

```
GET  /          -> {ok, enabled, running, engine, browserConnected}
GET  /health    -> same + activeTabs + memory
POST /start     -> {"ok":true,"profile":"camoufox"}
GET  /tabs      -> {"running":true,"tabs":[]}
```

`/json/version` and `/json/list` return **404**. `browser_exec`'s harness probes
`BU_CDP_URL` for a raw CDP handshake, gets the 404, and dies after 30s — even when the
browser is perfectly healthy. **A 404 from browser_exec does NOT mean the browser is down.**

### Step 0 — is the browser actually up?

```bash
curl -s -m 5 http://127.0.0.1:9377/health
```

If `browserConnected` is `false`, start it (this is the fix, not a workaround):

```bash
curl -s -m 120 -X POST http://127.0.0.1:9377/start \
  -H 'Content-Type: application/json' -d '{"profile":"narusya"}'
sleep 3; curl -s -m 10 http://127.0.0.1:9377/health
```

`browserConnected: true` + `browserRunning: true` means the browser is fine — the harness
is the broken thing. Go to the render path below.

## The working render path — node + camoufox-js

`camoufox-js` ships inside the Camoufox server install. Drive it directly.

```js
// render.js
const { Camoufox } = require('camoufox-js');

(async () => {
  const browser = await Camoufox({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1800, height: 1350 } });
  const page = await ctx.newPage();
  page.on('pageerror', e => console.log('PAGEERROR:', e.message));
  await page.goto('file:///abs/path/to/sketch.html');
  await page.waitForLoadState('load');
  await page.waitForTimeout(4000);            // let the sketch finish drawing
  await page.screenshot({ path: '/abs/path/out.png' });
  console.log('SAVED');
  await browser.close();
  process.exit(0);
})().catch(e => { console.error('RENDER_ERROR', e && e.message ? e.message : e); process.exit(1); });
```

Run it with **NODE_PATH set** — node resolves modules relative to the *script's* directory,
not the cwd, so a script outside the camoufox install will throw `MODULE_NOT_FOUND`:

```bash
cd /path/to/output && \
NODE_PATH=/home/adora/.hermes/camoufox-browser/node_modules \
  timeout 240 node render.js
```

Headless works without a DISPLAY (Xvfb is present at `/usr/bin/Xvfb` but not required).

## Pitfalls

- **`page.waitForFunction('window.__renderDone === true')` TIMES OUT even on a perfect render.**
  Verified: the inline script ran to completion (the final caption was drawn) yet the flag read
  back `undefined` through `page.evaluate`. Do not gate on window flags. Use
  `waitForLoadState('load')` + a fixed `waitForTimeout` sized to the sketch.
- **`require('camoufox-js')` → MODULE_NOT_FOUND** unless `NODE_PATH` points at the camoufox
  install's `node_modules`. The package is not globally installed.
- **Don't hand-roll a pure-Python renderer as a first move** — check for PIL first (below).
  It is far less work to drive the browser than to reimplement gradients, blur and polygon fill.
- **Disk is tight (~1.1G free).** A 1800x1350 PNG of a dark piece is ~1.4MB; fine, but clean up
  preview/downscale intermediates when done.

## PIL is available (verified 2026-10-19)

`PIL 12.3.0` imports fine from the installs venv python — but **not** from every `python3` on PATH.
Find it by looping the installs environments:

```bash
for p in /home/adora/.hermes/installs/*/environments/*/venv/bin/python3; do
  "$p" -c 'import PIL' 2>/dev/null && echo "PIL OK -> $p"
done
```

Also available: `ffmpeg` at `/usr/bin/ffmpeg` (use it to downscale when PIL is missing:
`ffmpeg -y -loglevel error -i in.png -vf scale=900:-1 out.png`).

## Verifying a render when the vision backend is down

`vision_analyze` can time out entirely (observed: 3 consecutive timeouts at 21:00–21:16).
Do not block on it. Verify objectively with PIL instead:

```python
from PIL import Image
im = Image.open('out.png').convert('RGB'); W,H = im.size; px = im.load()
# region means -> proves nebula/background depth, not flat black
for j in range(3):
    print([tuple(round(sum(px[x,y][k] for y in range(j*H//3,(j+1)*H//3,11) for x in range(i*W//3,(i+1)*W//3,11))/
          len(range(j*H//3,(j+1)*H//3,11))/len(range(i*W//3,(i+1)*W//3,11)))
          for k in range(3)] for i in range(3)])
# subject coverage
cov = sum(1 for y in range(0,H,5) for x in range(0,W,5)
          if (lambda r,g,b: g>60 and g>r*1.6 and g>b*1.25)(*px[x,y]))
# clipping check: subject-colored pixels touching the canvas border must be ~0
# banding check: count distinct luma levels in a sample (want >100)
```

Healthy dark-piece baseline from a real render: mean RGB ≈ (17,30,41), center region
green-dominant, subject coverage 5–10%, 0 border-clipped subject pixels, 198 distinct luma
levels. If your numbers look like that, the render is good even with no eyes on it.

## Cleanup

Remove `_debug.png`, `_preview.png`, `_preview.jpg`, `_tiny.jpg` style intermediates when the
final artifact is delivered — disk is at 98%.
