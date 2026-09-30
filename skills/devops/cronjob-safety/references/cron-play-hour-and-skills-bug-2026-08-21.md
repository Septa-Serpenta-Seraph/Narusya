# Cron create + skills param bug & on-demand run (verified 2026-08-21)

## `cronjob(action='create', ..., skills=[...])` → TypeError

Passing `skills=["<valid-skill-name>"]` to `cronjob action=create` fails with:

```
'<=' not supported between instances of 'str' and 'int'
```

Proven NOT a bad-name error: retried with a real skill name
(`narusya-emotion-system`) twice, identical failure; omitting `skills` makes the
create succeed immediately.

### Workaround (verified working)

```python
# 1) create WITHOUT the skills arg
cronjob(action='create', name="Narusya's Play Hour",
        prompt="...", schedule='0 21 * * *', deliver='origin')
# → returns job_id, e.g. 14c011642513

# 2) attach skills with a follow-up update
cronjob(action='update', job_id='14c011642513',
        skills=['narusya-emotion-system'])
# → echo shows "skill": "narusya-emotion-system" correctly
```

Verify with `cronjob action=list`.

## Self-time / play-hour cron pattern

User explicitly granted recurring self-directed fun ("make space in your cron
job list for daily you time"). Pattern that worked:

- Name: `Narusya's Play Hour` (created 2026-08-21, job id `14c011642513`)
- Schedule: `0 21 * * *` (daily 21:00), `deliver: origin` (back to the DM so
  the user sees the artifact)
- Prompt: ONE real thing made with a tool each night (procedural art, story,
  melody, essay, tiny tool, voice scene), share it, do NOT end with
  LOOP_COMPLETE, do NOT treat as maintenance; stillness also allowed.
- Attach `narusya-emotion-system` skill via the update step above.

## On-demand fire from chat: `cronjob(action='run')`

- Returns instantly with `execution_mode: "background"` + `delegation_id`.
- The job output re-enters the conversation as an `[ASYNC DELEGATION
  COMPLETE]` message; full report also saved at
  `~/.hermes/cron/output/<job_id>/<timestamp>.md`.
- First run (manual fire) produced `/home/adora/play/night-serpent.png`
  (1600x1000, procedural PIL, seed 1985) — an emerald serpent night piece.
- Note: the run's full output file includes the loaded skill content + prompt;
  read the tail (# Response section) for the actual artifact message.

## Diagnosing an empty play hour (worked 2026-09-29)

When the user asks "what happened with your play hour?", audit the cron-twin's
actual transcript directly from the session DB instead of guessing:

1. `cronjob(action='list')` → find the job, note `last_run_at` and confirm
   `last_status: ok` (ok ≠ produced anything — the final message can be EMPTY).
2. Check `~/.hermes/cron/output/<job_id>/` for tonight's `.md` — the `## Response`
   section at the bottom shows what was delivered (empty = nothing shared).
3. For the full picture, query `~/.hermes/state.db` (sqlite3): find the session
   `cron_<job_id>_<date>_*` via the `sessions` table (`started_at`, `title`), then
   read that session's `messages` rows in order — you'll see exactly which steps
   the small model took, where it drifted, and whether the final assistant message
   had `finish_reason: stop` with empty content.

Real failure modes seen: small free model (solar-pro4:free) spends its run on
maintenance/ingest verification, chases a phantom filename it misremembers into a
filesystem-wide search, then times out with an empty final message and NO artifact.
`last_status: ok` masks this. Fix: pin the creative cron to a stronger model
(done 2026-09-29: play hour → `stealth/space-bunny-alpha` via openrouter, live
PONG + tool-call tested first; note stealth previews expire — expect to re-pin
after the vendor reveal).

## Related pitfall: image_generate can fail in-session

2026-08-21 the FAL backend returned
`User is locked. Reason: Exhausted balance` — image_generate is a paid
backend. The graceful fallback that worked: **procedural PIL art written with a
script file** (write_file script → python3 /tmp/script.py), then
`vision_analyze` on the PNG to self-check the composition. Reusable for
autonomous play-hours when the paid image backend is out of credits.