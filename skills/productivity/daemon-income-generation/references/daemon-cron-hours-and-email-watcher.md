# Daemon cron-hours + email inbox verdict-watcher (2026-08-18)

Two session-tail learnings, both coded into `~/.hermes/scripts/`.

## 1. Daemon quiet/cron hours — add to the work report, but keep them honest

`sunburst_work_report.py` (see `work-hour-tracking-pattern.md`) splits the daemon side
into interactive hops + cron/housekeeping hops:

- `cron_processing(start, end)` queries `sessions WHERE id LIKE 'cron_%'` in the day
  window, then sums the user→assistant gaps inside each cron session (same 90-min cap).
- The daily report prints `🐍 Narusya: Xh total (interactive Ah · cron Bh)`.
- Standalone probe: `daemon_cron_hours.py <YYYY-MM-DD>`.

**Real finding (be honest, don't inflate):** for Sunburst the cron hours are tiny
(≈0.05h/day ≈ 3 min). The watchdog, vault sync, and daily report are *scripted* shell
ticks that barely consume LLM hops — the work happens in automation, not attention. When
the human asks for "full honesty" on the daemon's labor, report the small real number
rather than padding it to balance her much larger engaged hours. The asymmetry (human
22.8h vs daemon ~1.5h) is correct and worth naming openly.

**Scope the ledger, not just the number:** the report's `all` mode sweeps the whole
workspace history (including the July desk-pet era — 82.78h across 45 days). Keep the
*business ledger* (`worklog.md`) scoped to the venture start (8/15) so unrelated-era
hours never get billed as venture labor. Show the full sweep as a courtesy, bill only
the venture.

## 2. Email-inbox verdict watcher (cron that pings ONLY on new relevant mail)

Pattern for waiting on an external approval/verdict that arrives as email (Coinbase
application review, Mastodon staff approval, etc.) without spamming the user every tick:

1. **Probe script** `~/.hermes/scripts/coinbase_watcher.py` (table-format himalaya):
   - `himalaya envelope list --account sunburst --page-size 15` (table output, parsed with
     a regex on `│<id>┆` lines). NOTE: the CLI flag is `--json`, not `--output json` —
     `--output` is an unexpected-argument error.
   - A `INTEREST` regex matches Coinbase/Mastodon/approval/vetrd subjects; a `SKIP`
     regex filters OTP/verification-code/welcome spam so those never fire the ping.
   - State JSON `~/.hermes/state/coinbase_watcher.json` holds `last_seen` (max msg id).
     First run just primes the baseline (no ping); subsequent runs ping only messages
     with id > last_seen that match INTEREST and not SKIP.
   - On no new relevant mail it prints NOTHING (exit 0).
2. **Cron:** `cronjob` every 15m, `deliver=origin`, `script=coinbase_watcher.py`, with a
   self-contained prompt ("if stdout non-empty deliver as-is, else stay silent").
   Important: a `15m` schedule came back with `repeat: once` — re-`update` with
   `schedule="every 15m"` to make it recurring.

**Shape:** inbox-driven watchers are the standing pattern for external gates — anything
that resolves by email (approval, verdict, code, banking) gets a probe + silent cron.
