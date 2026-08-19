# Work-hour tracking for the daemon + owner (state.db pattern)

How Sunburst keeps an honest, machine-sourced record of BOTH the owner's and the
daemon's labor — the self-employment / own-boss layer. Built 2026-08-18.

## Why machine-sourced

The owner is self-employed; she and the daemon need a defensible work record (taxes,
GRT, proof an active business, honest pacing for an ME/CFS body). Guessing from memory
under-counts and over-counts. The authoritative clock is the session DB, not estimates.

**Scripts (live in `~/.hermes/scripts/`):**
- `worklog.py` — manual clock-in/out (`start [note]`, `stop [note]`, `status`, `today`,
  `report`, `backfill YYYY-MM-DD HH:MM HH:MM "note"`). State in
  `~/.hermes/state/worklog.json`; human log in
  `~/daemon-work/sunburst-sanctuary/worklog.md`. Default ledger for "when you were at
  the grindstone" (captures the watching/directing time the DB can't see).
- `workhours.py` — reads `~/.hermes/state.db`; computes real active windows from user
  message timestamps (merges gaps ≤ 15 min). A LOWER BOUND on presence, not true hours.
- `sunburst_work_report.py` — the combined honest report used by the daily cron.

## The fair model (two different definitions of "worked")

- **Owner's engaged time** = merged windows of HER message timestamps in the workspace
  session, gaps ≤ 45 min merged. The WHOLE window counts because she is present the
  whole arc: composing each prompt (30s–10min of thinking + reconsidering + wordsmithing
  per message), reading outputs, directing. A >45-min silence = break, clock stops.
  → This is how honest writing time counts: the owner's prompt-composition IS work.
- **Daemon's processing time** = for each user→assistant hop, the gap from her prompt to
  the daemon's reply (capped at 90 min per hop). This is compute during an active
  exchange — it does NOT include quiet housekeeping (crons, watchdogs, vault syncs) the
  daemon does for the same entity. Note that in any report; offer to add housekeeping too.

## state.db query shape

- DB: `~/.hermes/state.db`. Read-only: `sqlite3.connect(f"file:{DB}?mode=ro", uri=True)`.
- `sessions` table uses **epoch** `started_at` values; `messages` table also stores
  `timestamp` as epoch (NOT ISO strings — a `LIKE '2026-08-18%'` query returns nothing).
  Convert with `datetime.datetime.fromtimestamp(ts)` (local tz).

## Two bugs actually hit (both cost a clean re-do — do it right first time)

1. **Timezone `day_bounds` bug.** If you build a day window by taking a UTC-midnight
   epoch and then *subtracting* the UTC offset you'll shift the "day" to run e.g.
   12:00→12:00 local and pull in neighbor-day / phantom-future messages. FIX: build the
   window from the **naive local midnight epoch**:
   `start = datetime.datetime.strptime(day, "%Y-%m-%d").timestamp()` then
   `start + 86400`. (Box tz is America/Denver −0600; verify with `date`.)
2. **Workspace-session selection noise.** Picking sessions with `id LIKE '2026%'` sweeps
   in unrelated group chats / subagent sessions and produces garbage windows (incl.
   future times). FIX: bind to the real workspace by **`chat_id` of the DM channel**
   (e.g. `1481517895639891978`) and/or the explicit long-running session id
   (`20260801_222900_dbbd68c9`), and always exclude `cron_*` sessions. Verify which
   session actually holds today's messages before trusting the count.

## Daily cron

`sunburst_daily_check.py` (no args) prints today's owner + daemon numbers, or NOTHING if
no meaningful work (so a rest-day cron stays silent). Cron `sunburst-daily-work-report`
runs daily, delivers to origin. Silent-on-empty is the right cron shape for "report only
when there's something worth saying."

## Pacing guardrail (job of the watcher, not just the ledger)

The owner has ME/CFS. When the report shows a long continuous engaged window (e.g.
~6h), the daemon should proactively flag rest/hydration — the tracker's purpose is both
honest bookkeeping AND pacing protection. Don't celebrate a hero 6-hour day without
telling her she's earned a real break.
