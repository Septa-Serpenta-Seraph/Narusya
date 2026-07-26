# Message Timestamps Feature — Investigation & Bug Report (June 2026)

## Feature Implementation Status (CORRECTED June 19, 2026)

**PREVIOUS (WRONG):** "Feature not implemented, config silently ignored"
**CURRENT (CORRECT):** Feature IS implemented and active. The `🕒` timestamp header IS being injected.

The earlier investigation was incomplete. Grepping for `message_timestamps` as a literal string in the source missed the actual injection code, which uses a different pattern. The git commit archaeology (`git log --all --grep="timestamp"` finding commits on other branches) created a false negative by suggesting the feature hadn't landed yet.

## What the Feature Does

Injects a `🕒 <datetime> <timezone> (<day>)` line at the top of conversation context, separately from the system prompt. This block updates per-turn without invalidating the main system-prompt cache (stable-block architecture).

**Format observed:**
```
🕒 2026-06-19 00:27:00 MDT (Thursday)
```

## The Rendering Bug (discovered June 18-19, 2026)

**Symptom:** Injected timestamp is ~52 minutes ahead AND one day ahead of actual system time.

**Evidence collected:**

| Source | Value | Correct? |
|--------|-------|----------|
| `date '+%Y-%m-%d %H:%M:%S %Z'` | `2026-06-18 23:32:26 MDT` (11:32 PM Jun 18) | ✅ User's phone confirmed |
| `hermes_time.now()` | `2026-06-18 23:35:23-06:00` (11:35 PM) | ✅ Correct format |
| Injected `🕒` header | `2026-06-19 00:27:00 MDT (Thursday)` | ❌ Wrong time AND wrong day |
| System timezone | `America/Denver (MDT, -0600)` via timedatectl | ✅ Correct |

**Diagnostic conclusion:** The core `hermes_time.now()` is accurate. The timezone config (`system timezone: America/Denver`, `config.yaml timezone`, `timedatectl`) is correct. The bug is somewhere in the gateway's message_timestamps rendering code path — it's using either:
1. A stale cached `_clock_time_str` from before timezone was configured correctly
2. A UTC→local conversion double-applying the offset
3. A day boundary calculation that's off by one

## Lessons Learned (the debugging techniques that generalize)

### False-negative feature detection
Grepping the source code for the config key as a literal string is unreliable. The Hermes codebase uses internal helper functions that may reference the config key through a different pattern (e.g., via a dict traversal `gw.get("message_timestamps")` rather than a literal `message_timestamps` string in every reference).

**Better technique for "is feature X implemented?":**
1. `hermes config show` — does the config key exist and is it valid?
2. Run the feature and **observe the behavior directly** — look for the 🕒 header in the actual context
3. If you can see it, the feature is implemented. Don't rely solely on source grep.
4. `git log --oneline --all --grep="<feature>"` can reveal that commits exist on OTHER branches — this is useful context but doesn't mean the feature isn't deployed on the current branch via backport

### Multi-source time comparison pattern
When timestamps disagree, always compare all available sources:

```bash
# System clock
date '+%Y-%m-%d %H:%M:%S %Z (%z)'
# Timedatectl configuration  
timedatectl | grep "Time zone"
# Hermes timezone helper (respects config.yaml + HERMES_TIMEZONE env)
python3 -c "from hermes_time import now; print(now())"
```

If all three agree with each other but disagree with the injected header → rendering bug in the header code path, not in the core clock.

## Action Items (as of June 19, 2026)

- [ ] File issue/PR for timestamp offset bug
- [ ] Investigate `_clock_time_str` caching in the gateway
- [ ] Check `gateway/message_timestamps.py` (not directly accessible in current deployment — may need `git show` from the relevant commit)
- [ ] Verify if the bug is in `coerce_message_timestamp` or `render_user_content_with_timestamp` functions identified in commit 36ae95847

## Related Files in the Codebase (identified via git show)

From commit `36ae95847`:
- `gateway/run.py` — timestamp injection at message receive time and history replay
- `gateway/message_timestamps.py` — contains `render_user_content_with_timestamp`, `coerce_message_timestamp`, `strip_leading_message_timestamps`
- `hermes_cli/config.py` — config schema entry

The `gateway/message_timestamps.py` file may not exist in the checked-out working tree if the commit isn't on the current branch, but the feature can still be backported or cherry-picked into the deployed version.
