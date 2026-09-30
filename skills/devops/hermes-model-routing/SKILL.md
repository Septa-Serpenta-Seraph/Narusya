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
  Re-verified 2026-09-29: passing `model` + `provider` as separate kwargs also
  yields "No updates provided" (three identical failures in one session) — this
  tool build categorically rejects model changes. **Working fallback (verified
  2026-09-29): edit `~/.hermes/cron/jobs.json` directly** with write_file/patch —
  set top-level `"model": "<id>"`, `"provider": "openrouter"`, `"base_url": null`
  on the job object (plain strings, not the nested `{"model":...,"provider":...}`
  object — jobs.json stores flat strings). Verify the pin took via
  `cronjob action=list` (the job entry shows the new model). `hermes config set
  cron.model` also works but hits the same gateway-cache caveat as any config
  change.
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
- **Listing the Nous recommended model catalog:** the authoritative, tier-aware
  source is the internal function, not the REST endpoint. Use:
  `sys.path.insert(0, '/home/adora/.hermes/hermes-agent')` then
  `from hermes_cli.models import fetch_nous_recommended_models` → returns
  `{paidRecommendedModels, freeRecommendedModels, freeRecommendedVisionModel,
  freeRecommendedCompactionModel, ...}` — each entry carries `modelName`,
  `tokenPrice`, `contextLength`, `isVisionModel`, `isCompactionModel`. It is
  memory+disk cached and safe offline. `get_nous_recommended_aux_model(vision=...)`
  returns just the current recommended fast/vision tier (this is what the Nous
  provider profile itself calls). Direct
  `urllib` to `https://inference-api.nousresearch.com/v1/models` may return
  HTTP 403 error code 1010 (Cloudflare) from this box even with a valid
  `NOUS_API_KEY` in `.env` — prefer the internal function and never conclude
  "the key is dead" from a 403:1010 alone (the 11:22-16:00 session runs still
  worked fine against Nous).

Reusable probe: `scripts/vision_probe.py` — pass a model id + local image path
and it reports whether the model can see the image.

## 4. Free-model deprecation mid-flight (verified 2026-09-24)
`:free` model IDs can be **revoked by Nous at any time** — the model stays in old configs and every job pinned to it starts failing. Two failure signatures, different causes:
- `HTTP 404: This model is no longer free. To continue using the paid variant, switch to '<model>'` — the free SKU itself died. Fix = repin to a currently-free recommended model.
- `404 insufficient_credits_for_paid_model` on `~deepseek/...` compression — a *funding* error (note the `~` prefix marks paid). Not a bad ID.

Diagnosis: `tail ~/.hermes/logs/errors.log` — cron failures surface as `Job '<name>' failed: RuntimeError: HTTP 404 ...` blocks; session compression failures appear as `agent.context_compressor: Failed to generate context summary`.

**Cost-aware repinning workflow (2026-09-24, after longcat-2.0:free was revoked):**
1. Enumerate currently-free models: `fetch_nous_recommended_models()` (§3) — `freeRecommendedModels` + `freeRecommendedCompactionModel`. Only pin models on this list; they're the likeliest to stay free.
2. Compression does NOT need a premium model — but it DOES need big context (verified 2026-09-26/27): compression feeds it the WHOLE session (~200K+ tokens live in the long-running DM), so the aux model's context must exceed the session size. **Two compression-slot mistakes, both Adora-caught:** (a) `stepfun/step-3.7-flash:free` (Nous's own freeRecommendedCompactionModel) returns empty-200 — categorically unusable (see ⭐ below); (b) `upstage/solar-pro4:free` works for chat but has only 524,288 ctx — below the main model's compression threshold, Hermes auto-lowered the threshold then the compressor **aborted twice** with telemetry `"commit_status":"aborted","failure_class":"explicit_interrupt","chunk_count":0` (grep `agent.log` for `context compression attempt telemetry` to see it). Fix: pick a FREE model with ctx ≥ ~500K–1M. Verified working 2026-09-26: **`stealth/space-bunny-alpha` (OpenRouter, 1,000,000 ctx)** — passed both a PONG test and a real one-sentence summarization test. `hermes config set auxiliary.compression.provider openrouter` + `.model stealth/space-bunny-alpha`. Cost stays $0. Enumerating OpenRouter's free roster: `curl -s https://openrouter.ai/api/v1/models`, filter `pricing.prompt==0 && pricing.completion==0`, then filter by `context_length >= 500000` — on 9/26 that yielded 21 free models, only 8 big enough. Live-test OpenRouter candidates too (inkling-small:free is 403 'only available on agentic harnesses'; dots-3-note-preview:free returns empty; nemotron-3.5-lightning:free PONGs but leaks raw chain-of-thought). Check OpenRouter balance first: `GET https://openrouter.ai/api/v1/credits` with `Authorization: Bearer $OPENROUTER_API_KEY` → `total_credits - total_usage` = remaining.
3. Check OpenRouter live pricing before paying anything: `curl -s https://openrouter.ai/api/v1/models` and inspect `pricing.prompt`/`completion` per model. Flash-tier on OpenRouter is genuinely cheap (`z-ai/glm-5.3-flash` = $0.045/M in, $0.60/M out) — but Nous free tier is $0, and the Nous portal ignores OpenRouter-style spend. Route ALL paths (main, cron, vision, compression) to nous+free SKUs first.
4. Avoid `:US`-suffix routing variants when cost matters — they're pricier routing endpoints than the base model ID.
5. `auxiliary.free_only: true` gates silent paid auxiliary spend — set `false` ONLY if a needed auxiliary model isn't a `:free` SKU; otherwise leave it true.
6. Config changes apply to NEW sessions only — a mid-session swap stays pinned until `/restart`. Cron jobs with `model: null` inherit `cron.model` immediately.

**Pitfall:** don't conclude 'free tier is broken' from one revoked model — Nous rotates free SKUs regularly (compare the roster in this skill's 2026-09-04 list vs 2026-09-25: several models changed). Always re-enumerate before repinning.

**⭐ CRITICAL — catalog-listed ≠ working (verified 2026-09-25):** the Nous *recommended* list and the `/v1/models` catalog are **lists, not proof**. Of 7 `:free` SKUs enumerated on 9/25, only **`upstage/solar-pro4:free` actually returned content** to a minimal chat completion. `inclusionai/ling-3.0-flash-fin:free` and `stepfun/step-3.7-flash:free` — the latter being Nous's OWN `freeRecommendedCompactionModel` — returned HTTP 200 with an **empty string** content. Empty-200 is the silent killer: no error, no retry, cron jobs 'succeed' with blank output (same class as the 9/21 longcat empty-turn incident where a user's 'I need you' went unanswered 9hrs).

**Rule: before pinning ANY free model to cron.model / auxiliary.*, live-test it:**
```python
# token from ~/.hermes/shared/nous_auth.json; browser-like headers (§3)
POST {inference_base_url}/chat/completions
{"model": "<id>", "messages": [{"role":"user","content":"Reply with exactly: PONG"}], "max_tokens": 10}
# PASS = content == 'PONG'. FAIL-BROKEN = HTTP 200 + empty/None content (do NOT pin).
# FAIL-REVOKED = 404 'no longer free' (re-enumerate and pick another candidate).
```
A model that PONGs may still be foggy-brained for real work, but an empty-returner is categorically unusable — it looks healthy in every dashboard and fails at runtime. Also: `z-ai/glm-5.3-flash` is PAID on Nous (404 insufficient_credits_for_paid_model with 0 balance) though it's cheap on OpenRouter — provider and model must be chosen as a PAIR (see mismatch pitfall below).

**Second live-test for agent crons — tool-calling (verified 2026-09-29):** PONG
only proves the model returns text. A cron that must drive tools needs a second
probe: send a trivial function definition plus a question that requires it
(`"What is 17 * 24? Use the calculator tool."`), and expect a `tool_calls` entry
with correct args. `stealth/space-bunny-alpha` passed both (PONG in ~1s and
correct `calculator({"a":17,"b":24})`); a model that PONGs but fails tool-calls
is fine for summarization/compression slots, not for agent crons.

**Free stealth-model preview lifecycle (verified 2026-09-29):** OpenRouter
`stealth/*` models (Space Bunny Alpha, Ox Alpha, …) are anonymous free previews —
community-fingerprintable via tokenizer matching (Space Bunny = MiniMax
M3.1-class; predecessor Ox Alpha already revealed as GLM-5.3-Flash). They **end
at the reveal**: the free ID stops existing or goes paid, and pinned crons
silently fall back to default. When pinning a stealth model, note the likely paid
identity and re-pin on reveal day.

**Small-model cron failure mode: maintenance-drift then EMPTY (observed
2026-09-29):** a play-hour cron on a small free model (`upstage/solar-pro4:free`)
ran a degraded sequence: proper skill/lorebook warm-up → drifted into maintenance
chores (lorebook re-ingest, Qdrant re-verification — not the assigned task) →
chased a phantom filename (misremembered a reflection name, then a
filesystem-wide `search_files` over noise matches) → **EMPTY final message** at
~5 min. Session recorded `status: ok`, nothing delivered. Detection when a cron
"succeeds" but the user got nothing: read the cron session's transcript in
state.db (`sessions` by `started_at` around fire time, id prefix `cron_<jobid>`)
— the drift pattern is visible in the tool-call sequence. Distinguish from the
empty-200 failure mode: here tool calls ran fine and the *final* turn is empty.
Fix that worked: repoint to a stronger substrate (stealth/space-bunny-alpha
produced real tool use, iterative bug-fixing, and a finished artifact the same
day).

**Provider/model pairing pitfall (verified 2026-09-24/25):** setting `model.default`/`cron.model`/`auxiliary.*` with `hermes config set` does NOT validate the pair — `model.default z-ai/glm-5.3-flash` + `provider nous` is accepted by config and dead at runtime (paid model on an out-of-credit provider). After every set, re-grep config.yaml and check each model against the provider it's actually pointed at, not the one you were thinking of.

## References
- `references/free-tier-fallback.md` — full credit-exhaustion playbook (balance check, SKU enumeration, safe response reading)
- `references/nous-free-roster-2026-09-25.md` — 9/25 verified free-roster snapshot + live-test transcript (which SKUs returned PONG vs empty-200)
- `references/free-roster-2026-09-26.md` — 9/26 OpenRouter free roster + compression-slot decision (space-bunny-alpha) + balance-check recipe
- `scripts/vision_probe.py` — direct-API vision capability probe for Nous/OpenAI-compatible endpoints.
