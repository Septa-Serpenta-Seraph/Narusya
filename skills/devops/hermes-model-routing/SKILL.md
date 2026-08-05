---
name: hermes-model-routing
description: "Fix Hermes cron drift skips and vision routing."
tags: [hermes, model, cron, vision, routing, config]
---

# Hermes Model Routing & Config Pinning

Class-level operations for keeping Hermes's model paths healthy: the cron
model-drift guard, auxiliary model routing (vision/compression/skills-hub),
and verifying providers directly when tools fail.

## When to use
- A cron job fails with `Skipped to prevent unintended spend: global inference config drifted`
- `vision_analyze` returns 404 / "model provider failed after retries" after a provider switch or credit drain
- You changed `model.default` and want unpinned cron jobs to follow deliberately
- You need to prove a model can do X (e.g. vision) without guessing

## 1. Cron Model-Drift Guard (v0.20.0+ fail-closed)

**Symptom:** after the global gateway model changes, unpinned cron jobs report:
```
RuntimeError: Skipped to prevent unintended spend: global inference config drifted
since this job was created (model 'OLD' -> 'NEW'), and this job is unpinned.
```
This is a **safety feature**, not a bug — unpinned jobs refuse to silently
inherit a new paid default. It engages when `cron.model_drift_guard` is true
(default) and the job has `model: null`.

**Fix — config-level pin (preferred, fixes ALL unpinned jobs at once):**
```bash
hermes config set cron.model deepseek/deepseek-v4-flash-0731
hermes config set cron.model_provider nous
```
Resolution at fire time: per-job pin > `cron.model` > global `model.default`.
When `cron.model` is set, the drift guard disengages for the model axis.

**Pitfalls:**
- The `cronjob action=update` tool does NOT forward `model`/`provider` — it
  either returns "No updates provided" or succeeds while silently dropping the
  fields (job stays `model: null`). Use `hermes config set cron.*` instead.
- `~/.hermes/cron/jobs.json` stores jobs with field **`id`**, not `job_id` —
  `job_id` lookups silently return nothing.
- Failed cron runs append a `## Error` block at the END of the output file at
  `~/.hermes/cron/output/<id>/<timestamp>.md` — `tail` the file to see the real
  error; don't trust `last_status` alone.
- Verify with `cronjob action=run job_id=<id>` and check `execution_success: true`.

## 2. Auxiliary Model Routing (vision/compression/skills-hub)

`auxiliary.*` blocks in config.yaml pin which provider+model handle image
analysis, compression, web extraction, etc. The MAIN model is text-only in many
setups (e.g. deepseek-v4-flash) — images route to `auxiliary.vision`.

**Symptom:** `vision_analyze` 404s or the gateway warns "model provider failed
after retries" when a provider (e.g. OpenRouter) runs out of credits.

**Fix — repoint the auxiliary block to a funded provider:**
```bash
hermes config set auxiliary.vision.provider nous
hermes config set auxiliary.vision.model qwen/qwen3.8-max   # multimodal, uncensored-leaning
```
**The gateway holds config in memory** — after changing `auxiliary.*`, the
running gateway keeps using the old config until it restarts (user hits
`/restart` in chat; never `hermes gateway restart` in-session — self-blocks).

## 3. Direct Provider Probe (bypasses tool routing)

When a tool fails and you need ground truth about a model, call the provider
API directly. For Nous:
- Real token lives in `~/.hermes/shared/nous_auth.json` (`access_token`,
  `inference_base_url` = `https://inference-api.nousresearch.com/v1`) — the
  `NOUS_API_KEY` in `.env` may be EMPTY.
- Bare `urllib` gets Cloudflare-blocked (HTTP 403 error code 1010). Send a
  browser-like `User-Agent` + `Accept` + Origin/Referer headers.
- Test vision with a base64 data URL in an `image_url` content block.

Reusable probe: `scripts/vision_probe.py` — pass a model id + local image path
and it reports whether the model can see the image.

## References
- `scripts/vision_probe.py` — direct-API vision capability probe for Nous/OpenAI-compatible endpoints.
