# Publishing a public copy of a health project + the "Bethesda" mascot recipe

Session-2 tail (2026-08-20). Two reusable workflows proven live on PIPNARU/CoilPip.

## Public privacy-scrub release (CoilPip)

Goal: publish the *code/structure* of a personal health project publicly with
ZERO personal data. Verified live end-to-end.

1. **Copy clean** — never publish the working tree in place:
   ```
   rsync -a --exclude='.git' --exclude='__pycache__' --exclude='imports' \
     ~/body-panel/ ~/coilpip-public/
   rm -rf ~/coilpip-public/.hermes        # internal plans = personal context
   ```
2. **Grep-sweep identifiers** — names, diagnoses, EINs/tax IDs, addresses,
   and *variable names* (not just display strings):
   ```
   grep -rInE 'ADORA|NARUSYA|ME/CFS|EIN|42-4517237|adora\.md|Klitgaard|Lucero' \
     --include='*.py' --include='*.html' --include='*.md' --include='*.css' --include='*.js' .
   ```
   Fix each hit. **Variable names count** (`ADORA_LOG` → `USER_LOG`) — grep
   only catches the literal; a name like `ADORA_LOG` at a path
   `~/health/health-notes.md` still carries the human's name in the code.
3. **Neutralize content**: replace the person's name on the character card
   (`ADORA` → `COILGIRL`), drop their diagnosis label (`ME/CFS` → neutral),
   swap personal/business quests for generic samples (an EIN in a quest is a
   real identifier), strip internal planning docs.
4. **Verify staged + remote tree** before `--public`:
   ```
   git init -b main && git add -A
   git ls-files | grep -iE 'imports|quests\.json|water\.json|weed\.json|food\.json|quicklog|\.hermes'   # want: nothing
   gh repo create <name> --public --source=. --remote=origin --push
   gh api repos/<owner>/<repo>/contents --jq '.[].name'   # confirm online tree
   ```
   Keep `imports/`, `logs/`, `*.health.json`, `__pycache__/`, `.hermes/`,
   vendored tarballs in `.gitignore`.
5. **Honest caveat to state**: if the server reads live state from
   `~/health/logs/`, running it on the user's own machine serves *their* data
   (that's the point) — but the committed repo carries none of it. A forker
   gets a clean template.

Note: `gh repo create --push` aborts "no commits found" on an empty repo —
commit first (or create remote + `git remote add` + push).

## "Bethesda recipe" mascot (why Vault Boy works — researched)

Real Fallout history (from Wikipedia/Fandom research): Vault Boy is the
product of a **4-artist hand-off pipeline iterated over years** — Leonard
Boyarsky concept → George Almond cards → Tramell Ray Isaac finalized the look
→ Natalia Smirnova redrew every image for FO3/4/76. Not one genius stroke: a
*curation pipeline* of passes by professional mascot artists. So iterating
many times is the expected path, not a failure.

The design rubric that makes a mascot READ at icon size (~200px):
1. **Base on a recognizable cultural archetype** (Rich Uncle Pennybags /
   50s ad-man), not a random shape.
2. **One signature pose** that carries meaning (Vault Boy's thumbs-up = "all
   fine when it isn't"). Our ME/CFS twist: the *rested* thumbs-up — "all good
   because I actually rested."
3. **Inset contrasting features** — DARK hair + face + eyes set INTO the
   lighter head. This is the single most missed step: a flat one-color
   silhouette reads as a blob; contrast is what makes the face/hair read.

The user explicitly asked to research "how Bethesda did it" and engaged with
the mascot as a fun artifact — it's a beloved, playful thread, keep the tone
light and iterative.

## Hard-won mascot pitfalls (all hit live this session)

- **Drawing SVG bezier "by hand" blind does NOT work for a mascot.** Complex
  torso/limb curves anti-alias into a wireframe at 200px. Stop after a couple
  passes and switch to **Pillow-drawn PNG** (`ImageDraw.polygon/ellipse/line`,
  solid fill, transparent bg) — pixel-exact, renders FILLED reliably. Export
  via a `make_<name>.py` script, view with `vision_analyze` on the FILE, then
  `<img src="...png">`.
- A **dark stroke over a dark background reads as hollow/outline** even when
  filled (e.g. `#1e8f34` stroke on a black bg). Solid mascot = NO outline
  stroke; put the stroke-color contrast ONLY in inset details.
- **`browser_vision` on the live page keeps analyzing a stale/compressed
  copy** of the small figure — it repeatedly reported "outline/broken" for a
  PNG the file-level `vision_analyze` confirmed as solid-filled. For ground
  truth on a small graphic, analyze the FILE (or a full-res page crop), not
  the downscaled live screenshot.
- A three-stroke blocky letter can read as Cyrillic (N vs И) — check what a
  letter *reads as*, and redraw with clean columns + correct diagonal slope.
- FAL/AI-image backend can be out of balance mid-session — the Pillow fallback
  is the right move for simple vector-style mascots anyway (no dependency).

## Relationship
`chronic-illness-health-logging` governs the PIPNARU/CoilPip family. The
private backup + cache/loader fixes from the same session are in
`references/pipnaru-trackers-backup-cache.md`.
