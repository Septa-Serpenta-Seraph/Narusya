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
- **Free Nous models return HTTP 400 "This endpoint does not honor caller-supplied provider routing"** — see §0 below.

## 0. Nous rejects provider routing (HTTP 400) — the #1 reason free Nous models fail

**Symptom:** switching a session to a free model over the `nous` provider (e.g.
`meituan/longcat-2.0:free`, `tencent/hy3:free`) fails instantly with:
```
Error code: 400 - 'This endpoint does not honor caller-supplied 'provider' routing
preferences (e.g. 'only', 'ignore', 'order', 'data_collection', ...). Routing is
decided centrally per model... Remove the 'provider' object from your request.'
```
**Root cause:** `provider_routing:` in config.yaml is a GLOBAL block. `gateway/run.py`
forwards its fields (`providers_allowed/ignored/order`, `provider_sort`,
`provider_require_parameters`, `provider_data_collection`) to EVERY provider —
including the Nous portal, which bans caller-supplied routing because routing there
is central. The free model connects fine; the request is then 400'd on the routing
object. (2026-08-26, verified in gateway agent.log.)

**Fix (current upstream structure):** provider routing is OpenRouter-specific by
design (`provider_routing controls OpenRouter provider sorting` per
`hermes_cli/tips.py`). After upstream refactors the routing-request builder lives
in `agent/chat_completion_helpers.py::_provider_preferences_for_agent()` (the
shared choke-point for main loop, summary, background, cron) and the Nous profile
re-emits it in `plugins/model-providers/nous/__init__.py::build_extra_body()`.
Guard BOTH:
- `_provider_preferences_for_agent()` → return `{}` when `agent.provider` is in
  `{"nous","nous-portal","nousresearch"}` (kills the object at every path).
- Nous profile `build_extra_body()` → never set `body["provider"]` (defense in
  depth; the OpenRouter transport path at `agent/transports/chat_completions.py`
  already gates on `is_openrouter`).

**Recovery after a Hermes update wipes the patch (happens every update):**
```bash
python3 ~/.hermes/scripts/repatch_nous_routing.py   # idempotent re-apply
```
This re-patches both files, runs a syntax check, and prints loud warnings if a
future refactor moved the anchor strings (so it never silently no-ops after the
code drifts). Then restart the gateway from a SEPARATE shell, never in-session:
`hermes gateway restart` or `systemctl --user restart hermes-gateway`. The
gateway self-blocks in-session restart (SIGTERM propagates to the agent's own
process). Verify by watching agent.log provider line for `provider=nous`.

**⏳ Stale-gateway cron signature (verified 2026-08-31):** after an update that
wiped the patch, the failure shows up as ALL model-backed cron jobs erroring
with the 400 while SCRIPT-only jobs (vault, backups, watchdogs) keep succeeding.
That split is the tell: the RUNNING gateway process still holds the pre-patch
code (started before the fix was on disk). The fix is the gateway restart above
— NOT editing jobs. Firing a manual `cronjob action=run` through the same stale
gateway re-errors identically; a fresh `hermes gateway restart` loads the patch
and the same manual run then completes `status: ok`. Confirm liveness by the
gateway process start time (`ps -o lstart -p <pid>`) being after the patch.

**Per-session model pin vs config default:** `config.yaml model.default` governs
NEW sessions. A current session can stay pinned to a different model (e.g. after
a manual emergency swap) and keeps using it until that session ends — grep
sessions for the old model ID to confirm it's a session-level pin, not config.
To "try" a switched default, start a FRESH session (it picks up config); don't
trust the current session as proof the new default works.

**Pitfalls:**
- Do NOT fix by removing `provider_routing` from config — that silently drops
  OpenRouter's anti-fp4 protection (glitchy deepseek returns).
- The failure message to grep is: `HTTP 400 ... does not honor caller-supplied
  provider routing preferences`. It appears in `~/.hermes/logs/errors.log`,
  not the dashboard HTML (`127.0.0.1:9119/logs` serves the SPA, not logs).
- When filing an upstream PR: check for existing PRs first — issue #77564
  documents this bug and open PRs #77593 (Nous profile only) and #89425
  (auxiliary only) were stale/partial; ours guarded both sites.

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
hermes config set auxiliary.vision.model qwen/qwen3-vl-8b-instruct  # PROVEN vision model
```
**CRITICAL — verify model IDs before pinning.** `qwen/qwen3.8-max` is NOT a
valid Nous catalog ID: it 404s intermittently ("Couldn't find that, sorry.")
— a call can succeed once then fail, which looks like a transient when it's
actually a bad ID. The model the Hermes codebase itself tests vision with is
`qwen/qwen3-vl-8b-instruct` (see `tests/agent/test_auxiliary_main_first.py`).
Always check the local catalog before trusting a model name:
- `~/.hermes/hermes-agent/website/static/api/model-catalog.json`
- `search_files` for the model ID inside `~/.hermes/hermes-agent/tests/`
  (tests reference models the codebase actually exercises)
**The gateway holds config in memory** — after changing `auxiliary.*`, the
running gateway keeps using the old config until it restarts (user hits
`/restart` in chat; never `hermes gateway restart` in-session — self-blocks).
After a restart, verify with a real `vision_analyze` call — and if the first
call succeeds but a second 404s, suspect the model ID, not the network.

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
