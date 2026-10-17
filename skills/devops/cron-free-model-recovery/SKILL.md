---
name: cron-free-model-recovery
description: Use when crons fail on a dead free model. Test and repin.
category: devops
---

# Cron Free-Model Recovery

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

## Repin + verify

```
hermes cron edit <id> --model 'poolside/laguna-s-2.1:free' --provider nous --pin
hermes cron run <id>   # verify: 'Ran now: succeeded.'
hermes cron runs <id> | head -3   # fresh run shows 'completed'
```

## Pitfalls
- OpenRouter key is vaulted (only fingerprints in auth.json credential_pool) — use the Nous agent_key for testing; it expires hourly but is refreshed by the gateway.
- Unpinned jobs follow the MAIN model (paid!) — if a 'free lane' unpinned job errors on a free model, it was the auxiliary free picker; pin it explicitly.
- Batch-edit multiple crons in one shell loop; confirm with jobs.json (count pins).
- `hermes cron show` doesn't exist — use `cron list`, `cron doctor`, `cron runs`.
