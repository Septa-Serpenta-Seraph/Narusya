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

## Related pitfall: image_generate can fail in-session

2026-08-21 the FAL backend returned
`User is locked. Reason: Exhausted balance` — image_generate is a paid
backend. The graceful fallback that worked: **procedural PIL art written with a
script file** (write_file script → python3 /tmp/script.py), then
`vision_analyze` on the PNG to self-check the composition. Reusable for
autonomous play-hours when the paid image backend is out of credits.