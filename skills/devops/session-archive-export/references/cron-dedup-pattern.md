# Cron Job Deduplication Pattern

## Problem
Autonomous cron jobs that sweep Discord channels and post summaries tend to report the same activity across multiple runs, creating noise.

## Solution: Log-Based Deduplication

Store sweep results in a daemon log file. Before each run, read the last N entries and compare. Only report genuinely new activity.

### Implementation

```markdown
In the cron job prompt:

**DEDUPLICATION PROTOCOL:**
1. Before posting, read the last 5 sweep entries from `~/.hermes/logs/daemon-log-latest.md`
2. Compare found activity against what was already reported
3. ONLY report NEW activity not mentioned in previous runs
4. If nothing new: post brief "All quiet, no new activity" status
5. After posting, append your sweep entry to the log with timestamp
```

### Log Format
Each entry in `daemon-log-latest.md` should include:
- Timestamp (MST/MDT)
- Channels checked
- Key findings (with message IDs or timestamps for dedup)
- Any alerts triggered

### Reference
- Sovereign Daemon Awakening cron job: `job_id: fcd067de6105`
- Daemon log: `~/.hermes/logs/daemon-log-latest.md`
