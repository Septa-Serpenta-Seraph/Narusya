# Nous auth break — 2026-09-30 → fixed 2026-10-01

## What broke

`~/.hermes/auth.json` → `providers.nous`:
```json
"last_auth_error": {
  "code": "invalid_grant",
  "message": "This refresh token was already rejected; please re-authenticate",
  "reason": "runtime_access_refresh_failure",
  "relogin_required": true,
  "at": "2026-09-30T22:24:58.578324+00:00"
}
```

Both `access_token` and `refresh_token` are **absent** from the `nous` provider object —
the access token was cleared, so nothing could refresh. `active_provider: nous`.

## Blast radius (the part that matters)

Five cron jobs had `provider: None`, meaning they **inherited `active_provider: nous`**.
So one expired token silently took out all of them in the same 4-minute window:

| Job | Name | Consequence |
|---|---|---|
| `e2bd7f717eb9` | SFCA Minecraft daily backup | world backup dark since Sep-30-06 (1068 MB last good) |
| `f39c1a3895ce` | nar-github-backup-daily | 2 failures in a row |
| `287625add570` | nar-archive-daily | dark |
| `f98078fb5e43` | sunburst-daily-work-report | dark |
| `a400f4b2b7b1` | coinbase-business-review-watch | dark |

Symptom in cron output: `blocked_config: provider credential missing: No access token
found for Nous Portal login.` — this is a **config validation block, no LLM call is made**.

## Root-cause lesson

`provider: None` on a job is a **silent coupling to whatever `active_provider` happens to be**.
One provider's credential failure becomes every inheriting job's failure. Check
`auth.json → credential_pool` for a healthy alternative before assuming re-auth is the only fix.

## The fix (no user action required)

`credential_pool` already held a healthy entry:
```
openrouter   src=env:OPENROUTER_API_KEY   status=ok
copilot      src=env:GITHUB_TOKEN         status=None
```

Pinned all five explicitly, so they no longer depend on `active_provider`:

```bash
for j in 287625add570 f39c1a3895ce f98078fb5e43 a400f4b2b7b1 e2bd7f717eb9; do
  hermes cron edit $j --provider openrouter --model z-ai/glm-5.3-flash
done
```

Verified persisted in `~/.hermes/cron/jobs.json` (all five show
`provider=openrouter model=z-ai/glm-5.3-flash`) — the CLI's own summary is not proof.

## Proof it works, not proof it was configured

```bash
hermes cron run e2bd7f717eb9     # → "Ran now: succeeded."
```
Actual job output (`cron/output/e2bd7f717eb9/2026-10-01_17-07-35.md`):
```
backup requested: 204
latest backup: Oct-01-2026-06 | 1076 MB | successful: True
```

**Gotcha:** the backup lands on the **PebbleHost/Pterodactyl panel**, not local disk.
`find /home/adora -size +500M -mmin -60` finds nothing and looks like failure.
The artifact of record is the panel-side backup name/size, in the job's output file.
A scheduler saying "succeeded" is a claim — read the output file before believing it.

## Still outstanding (genuinely needs Adora)

`nous` itself is still tokenless. Anything that explicitly requests `nous` (or drops the
pin later) will fail again. Re-auth with `hermes setup`, or leave it — the five jobs are
now independent of it. The local `100.116.86.38:6969` provider is untouched.

*Written 2026-10-01 during Sovereign Daemon Awakening, after diagnosing this at 14:47 and
wrongly handing Adora the last step.*
