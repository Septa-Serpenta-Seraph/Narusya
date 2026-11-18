---
name: daemon-log-watchdog-maintenance
description: Use when a log watchdog spams duplicates or false gaps.
version: 1.0.0
author: Narusya
license: MIT
metadata:
  hermes:
    tags: [devops, cron, logging, watchdog, maintenance]
    related_skills: [cronjob-safety, hermes-infrastructure, narusya-local-archive]
---

# Daemon Log Watchdog Maintenance

## When to Use

- A log tripwire/watchdog is appending reconciliation blocks every cycle.
- The watchdog reports the last log entry far older than what is in the file.
- You are about to prune a swollen daemon/activity log and must not lose events.

Applies to `~/.hermes/scripts/daemon_log_watchdog.py` (Narusya's chronicle tripwire) and to any similar "did the pen fall?" poller that compares a log against live activity. Two defects produced 440 duplicate reconciliation blocks (39k lines, ~2k unique) and a false PEN-FELL every 2 hours for weeks.

## Symptoms that mean the instrument is broken, not the daemon

- The log grows by hundreds of near-identical reconciliation blocks while the daemon's real output is unchanged.
- The reported "last entry" is weeks older than entries you can see in the file.
- Every poll cycle fires, even though nothing new happened.

## Defect 1 — scan window never advances

A poller must persist a **scan cursor** (sidecar JSON, e.g. `scan_end`). If the window start is derived only from the last log entry, and the poller's own writes are excluded from that parse, the start is frozen forever: every run re-reads the same stretch and re-records the same items.

Fix shape:
- Write `scan_end` after every successful fetch, before writing any report (so a crash mid-append cannot cause a re-report).
- Skip when `now - scan_end < gap_threshold`.
- Fetch `since = scan_end or last_entry`.
- Rate-limit the "nothing found" note (e.g. 48h); silence is not an emergency.

## Defect 2 — header parser only accepts one timezone

If the parser requires a literal `UTC`, any header stamped `MST`/`MDT` is invisible. The parser then falls back to a much older entry and fires forever.

Fix shape:
- Capture an explicit tz token and normalise: `TZ_OFFSET_H = {"UTC": 0, "MST": -7, "MDT": -6}`.
- Require the tz token in the regex so body prose full of bare datetimes cannot match.
- Make `~` before the time optional; header formats drift.

## Pruning a bloated chronicle

Do NOT dedupe by exact block copy — polling blocks drift (new items appear, old ones scroll out of the API window) so exact dedupe removes almost nothing (81 of 534 blocks in practice).

Prune on information instead:
1. Back up first; never prune without a backup.
2. Split into entries at `## ` headers.
3. Keep every non-watchdog entry verbatim.
4. For watchdog entries, keep the first block that records each **distinct item line**, plus the final block.
5. Verify: compute the set of distinct item lines in source and output; assert `missing == 0`.

Result on the swollen log: 3.24 MB -> 866 KB (26.7%), 39,475 -> 10,383 lines, 393/393 distinct events preserved.

## Verification checklist

- Run the script twice back-to-back: the second run must append nothing.
- Print the parsed `last entry`; confirm it equals the newest header you can see.
- After pruning, assert no distinct item disappeared.
- Keep the pre-fix script as `*.bak-<date>-<reason>` and mirror the fixed copy into the backup repo.

## Pitfall

Do not "fix" the instrument and leave the premise unexamined. If the daemon jobs stopped appending to the log by design, a correctly-working watchdog will still report a gap — that is a job-design question for the human, not a bug to silently patch away.
