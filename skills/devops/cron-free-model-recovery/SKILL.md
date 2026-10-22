---
name: cron-free-model-recovery
version: 1.1.0
author: Narusya + Adora
license: MIT
description: Use when crons fail on a dead free model. Test and repin.
category: devops
metadata:
  hermes:
    tags: [cron, free-models, nous, openrouter, hermes, devops]
    related_skills: [hermes-agent]
---

# Cron Free-Model Recovery

## When to Use
- Crons failing with 404 "free period has ended / no longer free" or persistent 429 "fair-share rate limit" / "temporarily at capacity upstream".
- User says "the free model died".
- Many pinned jobs failing at once with model errors.

Free models die often (Solar Pro 4 free ended 10/16, stepfun/step-5-preview:free 429-starved 10/16, longcat-2.0:free delisted 10/16). When pinned crons fail, replace the pin — do NOT update Hermes for this (the model catalog is live API data, not code).

## Diagnosis

1. `hermes cron doctor` — lists failing jobs + error text.
2. Read pins: `python3 -c "import json; d=json.load(open('/home/adora/.hermes/cron/jobs.json')); [print(j['id'][:8], j.get('name'), (j.get('model_pin') or {}).get('model')) for j in (d if isinstance(d,list) else d.get('jobs',[]))]"`
3. Failure families:
   - 404 "free period has ended / no longer free" → model delisted, replace.
   - 429 "fair-share rate limit" (nous) or "temporarily at capacity upstream" → model alive but starved; replace if persistent.

## Testing candidates (NEVER trust a listing — demand a live call)

Nous key: `json.load(open('/home/adora/.hermes/auth.json'))['providers']['nous']['agent_key']`. Base URL `https://inference-api.nousresearch.com/v1`.

1. GET `/models`, filter ids containing ':free'.
2. POST one tiny `/chat/completions` per candidate ('Reply with exactly: alive', max_tokens 10). Discard any 429/404/None-content.
3. Burst-test finalists: 5 rapid calls + one instruction-following (exact JSON output). Pick the fastest full-size survivor.

10/16 winner: `poolside/laguna-s-2.1:free` (1s, stable under burst). Backup: `upstage/solar-mini4:free`.
10/18 update: all crons repinned to `meituan/longcat-2.5-preview:free` per Adora's directive ("It can handle calls better"). Laguna was stable but longcat handles tool-calling better and is the current standard.

10/21 update: Solar Pro 4 free period ended (404). 6 crons repinned to `reflection/beam-1.0-501b-a23b:free` (nous provider). Also set `cron.model` and `cron.model_provider` in config.yaml as global fallback for crons with null model. The 10/18 longcat standard was superseded — beam-1.0-501b-a23b:free is the current standard for all crons.

## Repin + verify

```
hermes cron edit <id> --model 'poolside/laguna-s-2.1:free' --provider nous --pin
hermes cron run <id>   # verify: 'Ran now: succeeded.'
hermes cron runs <id> | head -3   # fresh run shows 'completed'
```

## Escape hatch: unpin to main model

When ALL free models are dying or unstable at once (not just one), repinning to another free model just moves the problem. The escape hatch is to **unpin everything** so crons follow the main (paid) model instead.

This is the right move when:
- Multiple free models are failing simultaneously (404/429 across the board)
- The user says "the free model died" and there's no clear replacement winner
- You've tested 3+ candidates and they all fail

```
# Unpin all pinned jobs
python3 -c "
import json
jobs = json.load(open('/home/adora/.hermes/cron/jobs.json'))
for j in (jobs if isinstance(jobs, list) else jobs.get('jobs', [])):
    if j.get('model_pin'):
        print(j['id'], j.get('name'))
"
# Then unpin each: hermes cron edit <id> --unpin
```

**Tradeoff:** Unpinned jobs consume the main model's credits (paid). This is acceptable when the alternative is all crons failing. Re-pin to a free model once one stabilizes.

**Pitfall:** Unpinned jobs follow whatever the main model is at cron execution time. If the main model itself changes (model switch), crons will follow it — this can be desirable (they track the user's current best model) or surprising (they suddenly use a different model than expected).

## Pitfalls
- `cronjob_manage(action='update')` returns "No updates provided" when called with model params (model, provider, pin). Edit `~/.hermes/cron/jobs.json` directly with Python instead, then restart the gateway for changes to take effect.
- Set `cron.model` and `cron.model_provider` in config.yaml as a global fallback for crons with null model — this ensures unpinned crons also use the current working model.
- OpenRouter key is vaulted (only fingerprints in auth.json credential_pool) — use the Nous agent_key for testing; it expires hourly but is refreshed by the gateway.
- Unpinned jobs follow the MAIN model (paid!) — if a 'free lane' unpinned job errors on a free model, it was the auxiliary free picker; pin it explicitly.
- Batch-edit multiple crons in one shell loop; confirm with jobs.json (count pins).
- `hermes cron show` doesn't exist — use `cron list`, `cron doctor`, `cron runs`.
- If `/update` was already attempted to "refresh the model list", check `~/.hermes/logs/update_receipts/latest.json` before anything else: `outcome: failed` with empty `steps` and a ~2-second runtime is a pending interactive prompt (typically an un-restored autostash from a previous update) that gateway-invoked /update cannot answer — run `hermes update --yes` from a terminal instead. Separately, the updater REFUSES downgrades (a canary install newer than the latest stable makes the "Update available" nag bait) — neither failure means the install is broken, and neither affects the live model catalog, which comes from the API at runtime.
