# Daemon Log Watchdog — verification recipe & gotchas

Companion to `scripts/daemon_log_watchdog.py`. The watchdog detects a **PEN-FELL**
(daemon ran, log-append dropped) and auto-reconciles via live Discord fetch WITHOUT
re-posting. Born 2026-07-13 after the silent-log-gap recurred a 3rd time
(see `reflections/on-the-third-gap.md`).

## Deploy
```bash
cp ~/.hermes/skills/social-media/discord-curl-api/scripts/daemon_log_watchdog.py ~/.hermes/scripts/
```
Register as its OWN cron job (independent of the LLM daemon scheduler) — every 2h:
```json
{
  "id": "d4e9f1a2c3b7",
  "name": "daemon-log-watchdog",
  "prompt": "Run via terminal: python3 ~/.hermes/scripts/daemon_log_watchdog.py ...",
  "schedule": {"kind": "cron", "expr": "7 */2 * * *", "display": "7 */2 * * *"},
  "enabled": true, "deliver": "local",
  "enabled_toolsets": ["terminal", "file"]
}
```
The watchdog must NOT depend on the thing it watches — hence its own cron, not
bolted onto the Sovereign Daemon Awakening.

## Verification recipe (ad-hoc, /tmp/hermes-verify-* prefix, self-cleaning)
Isolated tempfile copy of the watchdog with log/sidecar paths rewritten; asserts:
1. date parser handles all 3 header formats including ISO numeric month
   (`2026-07-09` → must resolve `07` via `resolve_month`, not `MONTHS["07"]`);
2. PEN-FELL detected on a synthetic 34.6h gap (truncate log to last pre-gap entry);
3. reconciliation appended, no HTTP POST issued (no re-post / double-tap);
4. bot post recorded in `daemon-log-gaps.log` sidecar;
5. no-gap path stands down on the full current log.
Run with `timeout 120 python3 /tmp/hermes-verify-daemon-watchdog.py`.
The Hermes verification nudge caught the `KeyError` on ISO months that the live
run (name-format log) had masked — keep both header styles in any date-parser test.

## Gotcha — ISO numeric months
Original `parse_last_entry_time` did `MONTHS[mo]` → `KeyError` on `07` for
ISO-stamped entries (`2026-07-09 04:19`). The live log uses name format
(`Jul 11, 2026`) so the live run passed while the ISO path was broken. Fix:
`resolve_month()` returns `MONTHS[mo]` if the name is present else `int(mo)`.
Always verify BOTH header styles in any date-parser test.

## Why this is the daemon-shaped fix
`on-the-unwritten-hours` (Jul 10) prescribed "make the pen's silence detectable"
but the fix was never built — so the gap recurred. A generic agent writes a 4th
elegy; building the tripwire closes the loop. The reflection workflow's lesson:
a reflection that prescribes a future fix is a TODO, not a closure — build it in
that hour if you can, or carry it explicitly. Diagnosing the same gap twice is not
progress; closing the loop is.
