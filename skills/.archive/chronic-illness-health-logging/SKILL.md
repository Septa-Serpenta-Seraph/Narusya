---
name: chronic-illness-health-logging
description: "Self-hosted ME/CFS health loggers."
tags: [health, logging, me-cfs, chronic-illness, self-hosted, symptom-tracking]
---

# Chronic-Illness Health Logging & Self-Hosted Trackers

Class-level guide for building and maintaining health-logging systems for chronic
illness (ME/CFS and similar energy-limiting conditions) that are clinically
credible, low-spoon to use, and self-hosted (no cloud). Proven in the PIPNARU
terminal build (2026-08-19) for Adora.

## When to use

- User wants a symptom/health logger, tracker, "body panel", or health dashboard.
- User asks what to log for ME/CFS / long COVID / fibro / POTS, or wants logs
  that hold up for a doctor / disability (SSI/SSDI) application.
- Building a local/self-hosted UI that the user reaches from another device
  (phone on the same Tailnet).
- Any "track my health like a game" request that must stay honest (stat bars
  derived from real log data, not invented numbers).

## The clinically-grounded schema (what to actually log)

Base the schema on **validated instruments**, not vibes:
- **DePaul Symptom Questionnaire-2 (DSQ-2)** — validated ME/CFS symptom domains:
  PEM, cognitive impairment, fever/flu, pain, sleep disruption, orthostatic
  intolerance, genitourinary, temperature intolerance.
- **Canadian Consensus Criteria (CCC)** — requires fatigue, PEM, sleep
  dysfunction, pain; ≥2 neuro/cognitive; ≥1 from two of autonomic/
  neuroendocrine/immune.
- **PEM is delayed 24–48h (hours to days).** Any log must capture **activity/load**
  *and* date — a crash on Wednesday needs Monday's exertion record to explain it.
  This is the single most valuable design decision.
- **Energy envelope / pacing method** (Leonard Jason; RTHM; 50% rule): log
  *perceived vs expended* energy; keep activity, sleep, meds, triggers.
- Apps to borrow field sets from (research-validated): **Bearable, Visible,
  ME/CFS Tracker**. The "30-second quick log from bed" pattern is the right
  UX bar — energy+pain required, everything else optional.

## Architecture pattern (self-hosted, near-zero deps)

- One Python stdlib `http.server` (no Flask/Docker needed) + vanilla HTML/CSS/JS.
- **Markdown files as the datastore** — human-readable logs double as doctor/
  disability evidence (`~/health/logs/quicklog.md`). Do not force a DB.
- JSON APIs: `GET /api/stats` (current parsed state), `GET /api/logs?n=N`
  (recent entries), `POST /api/log` (append).
- Tabs: STAT summary / DATA detail-trends / LOG input.
- **Honesty rule:** stat bars render from parsed real log values only. Never
  invent numbers for the pretty picture — a health tool that lies is poison.

## Serving to another device (Tailnet/phone) — the known path

- Find the box's Tailscale IP (`tailscale status`), bind the server to
  `0.0.0.0` (NOT localhost or the phone can't reach it), then the user opens
  `http://<box-ip>:<port>/` — e.g. `http://100.77.142.40:8765/`.
- Many devices show a plain-HTTP "insecure" warning on a raw tail IP — expected,
  safe on the user's own net; say so, don't promise TLS.
- The server dies on reboot — offer a startup script; don't promise persistence.

## Build/test loop that works (copy these)

1. `curl http://localhost:8765/api/stats` → JSON is real (not mock).
2. `curl -X POST /api/log -d '{...}'` → `{"ok": true}`, file grows.
3. Browser: click through every tab, verify content swaps.
4. **Browser-console fetch** to exercise the true user path without clicks:
   `(async()=>{ await (await fetch('/api/log',{method:'POST',...})).json(); ... })()`
5. **After every E2E, scrub the test entry** from the real log (slice the file
   via Python at the test marker). Test scratch must never live in a medical log.

## Pitfalls (all hit live)

- Dedup parse outputs when reading multiple files — `list(dict.fromkeys(...))`
  for buffs/debuffs or you double-count across logs.
- Fix internal ID mismatches between HTML elements and JS references before
  multi-tab builds (e.g. `stHp` vs `hpFill`); verify with a console fetch.
- **Design for sensory sensitivity:** subtle CRT flicker only, no strobes/flash —
  flares make bright flashing actively harmful for many with ME/CFS.
- Keep a "minimal mode": during a flare the log must accept energy+pain only.
- Don't let the game layer drift into fake mechanics that contradict health
  reality — the RPG skin is cosmetics over honest data.

## References
- `references/pipnaru-terminal.md` — full PIPNARU build detail: file layout,
  API contracts, rich log schema keys, Tailnet serving quirks, E2E test paths.

## Relationship to other skills
- `mutual-health-logging-daemon-human` (user-owned) is the *conversational* log
  ritual; this skill is the *instrumentation* (schemas, terminals). They
  complement: use this skill's schema inside that conversation's logs.