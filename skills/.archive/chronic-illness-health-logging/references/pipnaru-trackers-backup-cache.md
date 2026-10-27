# PIPNARU Session 2 (2026-08-20): live trackers, backup, caching, mascot

Second PIPNARU session on top of the 08-19 build. Everything here hit live.

## Live-event tracker pattern (water / weed / food)

Each day-scoped event tracker = one JSON file + one GET + one POST handler +
one small widget. Pattern proven with water then replicated for weed+food.

Data files live in `~/health/logs/` (NOT in the web root — they're the human's
records, and they stay out of the git repo):
- `water.json` — `{date, hydration: 0-100|null, glasses: int, bottle_ml: int}`
- `weed.json` — `{date, weed: [{time, method, amount, strain}]}`
- `food.json` — `{date, food: [{time, meal, what}]}`

Reset rule: `load_water()` returns a **fresh-day default** whenever
`file.date != today` — a new day starts clean, old file left untouched.

`POST /api/water` actions: `set` (hydration %), `glass` (delta ±1, optional ml),
`ml`. `POST /api/trackers` actions: `weed_add` / `weed_del` / `food_add` /
`food_del` (del by index). All load→mutate→save→return `{ok, <singular>:
reloaded}`.

Driving a bar: `apply_water_to_state(state)` folds hydration into `/api/stats` —
`hydration` overrides the DEFAULTS value, and `hydration < 35` inserts the
`dehydrated` debuff (removes it otherwise). Verified both directions with curl.

UI: STAT tab gets one-tap `+glass / -glass` buttons under the bar + a live
"💧 n glasses · ml · hydr %" line, reading `s.water_glasses / s.water_ml /
s.water_status / s.hydration`. LOG tab gets a HYDR slider (seeds from today's
state), glass buttons, and weed/food add lines with per-entry ✕ delete.
Delete handlers re-render from `/api/water` / `/api/trackers` GET after POST.

Test-loop for a tracker: POST a fake entry via curl → assert it lands in the
JSON → click the ✕ in the browser → assert it's gone → `rm` the file to scrub.

## Privacy-safe private backup (git + GitHub)

Repo: `github.com/Septa-Serpenta-Seraph/pipnaru-health-terminal` (PRIVATE,
created with `gh repo create --private`). Same vault account as the narusya-vault
DR repo. The code/structure is backed up; personal health data is NOT.

`.gitignore` essentials:
```
imports/            # visible.json + fatiguesense/*.csv — the vitals
logs/ *.log
__pycache__/ *.pyc
.hermes/
lib/*.tgz lib/package/   # vendored npm bloat
```
Files: `server.py`, `index.html`, `css/`, `js/`, `tabs/`, `pipgirl.png`,
`make_pipgirl.py`, import-bridge *scripts* (they contain no person data).

Gotchas hit live:
- `gh repo create --push` aborts with "no commits found" if the repo is empty —
  commit FIRST, then create/push, or create remote + `git remote add` + push.
- Committing the import BRIDGE script (`import_fatiguesense.py`) is fine — it's
  code, not data; don't be spooked by the filename.

## Cache / version system (the "I'm not seeing any changes" saga)

Root cause the user hit: **browsers cache per-file**. The shell (index.html)
bumped to 4.3, but `tabs/log.html` had already been cached from before the
trackers existed → STAT looked new, LOG looked old. Same for image assets.

Fix set (all three are needed together):
1. Server side: subclass `end_headers()` to always send
   `Cache-Control: no-store, no-cache, must-revalidate, max-age=0` +
   `Pragma: no-cache` + `Expires: 0` on EVERY response (static too).
2. Tab fetches: `fetch('tabs/' + name + '.html?v=' + VERSION)` — the query
   string is a NEW URL to the browser, so a version bump invalidates every tab.
3. Bump the visible `PIP-NARU x.y` brand string on each change + keep the `?v=`
   in sync with it. Also: delete stale legacy single-page files
   (`body-panel.html`, `pipboy.html`) that old bookmarks still hit — they 404
   after deletion, which the user can SEE (vs. silently serving a frozen copy).

## Tab loader bug (real, user-caught) — multi-script tabs

`index.html`'s loader originally ran only the FIRST `<script>` block per tab.
`data.html` has THREE script blocks (visible, fatiguesense, body-map/system) →
everything but the first froze on "loading...". Fix:
```js
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
document.getElementById('main').innerHTML = html.replace(/<script>[\s\S]*?<\/script>/g, '');
for (const js of scripts) { try { (0, eval)(js); } catch (e) { console.error('tab script', name, e); } }
```
Lesson: if a tab shows "loading..." forever but the code looks right, count the
script blocks — a one-script loader silently drops the rest.

## Mascot drawing — the research-informed path

The pipgirl started as hand-stitched SVG bezier paths and got called "janky"
four+ times. Research (vault-boy tutorials; ME/CFS app UI benchmarking) said:

- **Vault-Boy-style mascots read via SIMPLE recognizable shapes** — oval head,
  dot eyes, smile, big body silhouette — not detailed anatomy. At ~200px your
  brain fills the rest; complex curves anti-alias into a wireframe mess.
- **ME/CFS app UX benchmark (Visible, Bearable, Spoons):** dark mode ✓, ONE
  primary action per screen, honest non-gamified energy display (Visible's
  "stability score 1-5"), exportable reports for doctors. Our design already
  matched; the mascot was the only overengineered part.

Working solution: **draw programmatic PNG with Pillow** (`make_pipgirl.py`) —
`ImageDraw.polygon/ellipse/line` on solid green, transparent background. It
renders pixel-exact as FILLED (no SVG stroke/fill anti-aliasing ambiguity),
view it with `vision_analyze` on the FILE, then `<img src="pipgirl.png">`.

Vision pitfall: `browser_vision` on the LIVE page kept describing a stale
cached copy; `vision_analyze` on the actual file path gives ground truth.
Also: when vision keeps saying "outline/broken", believe it — a dark stroke
(`#1e8f34`) over a dark background reads as hollow. Filled = no outline stroke
at all.

## GUIDE tab (honesty pattern)

A static tab explaining each bar's derivation. HP/FOCUS were placeholders —
the GUIDE says so explicitly ("static placeholders — when I find a real signal
I'll connect them and update this page") rather than inventing a formula. The
user responded well to the honesty; it built trust that the OTHER numbers are
real.