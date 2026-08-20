# Serving a Local UI to Another Device Over the Tailnet (no SSH tunnel)

**Verified 2026-08-19:** Adora needed to open a self-contained HTML "body-panel"
character-sheet from her *phone* while couch/bed-bound. Both devices were already on
the same Tailnet, so no SSH tunnel was needed — just a Tailnet-address URL.

## Pattern (static/self-contained HTML files)

1. **Serve on 0.0.0.0**, not loopback:
   ```bash
   python3 -m http.server 8765 --bind 0.0.0.0
   ```
   (py3.8+ often defaults to 0.0.0.0 anyway — be explicit for clarity/robustness.)

2. **Get the box's Tailnet address** — this becomes the URL:
   ```bash
   tailscale status
   # → 100.77.142.40 narusya daniel@ ... (the box's tail IP)
   ```

3. **Give the user the full URL** — `http://100.x.x.x:<port>/<file.html>`.
   NEVER `localhost` (meaningless on their device). Plain HTTP over a tail IP triggers
   a browser "insecure" warning — tell them up front that's expected on a private
   tailnet and safe to proceed, so it doesn't scare them off.

4. **Verify before promising** (from the box):
   ```bash
   curl -s -o /dev/null -w "%{http_code}\n" http://<tailip>:<port>/<file.html>
   # → 200
   ```
   Raw-IP HTTP curl may trip an approval/prompt — expected, it's the tailnet.

5. **Lifecycle:** `http.server` dies with the process or reboot. Offer a startup
   script or relaunch-on-request so "open it from my phone" stays one step. Bound to
   0.0.0.0 it's exposed to whatever the Tailnet exposes — say "reachable from your
   Tailnet, not the public internet," don't overclaim "secure."

## Body-panel context (why gamify health data)
Rendering a person's health log as an RPG character sheet / annotated body map (HP,
Stamina, buffs/debuffs) is not trivializing — it gives the user agency over pain by
making it visible, trackable, playable. All stat values MUST trace to real records;
never invent numbers for the aesthetic. Let the figure + arrows annotate real systems.
Common failure to avoid: draft corruption/mojibake in system-description strings —
scrub before showing the user their own body map.