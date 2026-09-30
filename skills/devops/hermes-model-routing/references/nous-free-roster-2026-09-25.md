# Nous free-model roster — live test, 2026-09-25 ~07:20 MDT

Context: Adora reported crons failing because pinned free models were dead, and Nous balance was $0. Enumerated every `:free` SKU in the Nous catalog, then live-tested each with a minimal chat completion (`Reply with exactly: PONG`, max_tokens 10).

## Result table

| Model | Catalog-listed? | Live test | Verdict |
|---|---|---|---|
| `upstage/solar-pro4:free` | yes (also in paidRecommended list at $0) | `"PONG"` | ✅ ONLY working free model |
| `inclusionai/ling-3.0-flash-fin:free` | yes | HTTP 200, content `''` (empty) | ❌ silent death |
| `stepfun/step-3.7-flash:free` | yes — Nous's OWN `freeRecommendedCompactionModel` | HTTP 200, content `''` (empty) | ❌ silent death — recommendation is stale |
| `inclusionai/ling-3.0-flash-sante:free` | yes | (same family as fin; not separately PONG'd) | ⚠️ suspect, same family |
| `poolside/laguna-s-2.1:free` / `laguna-xs-2.1:free` | yes | (not PONG'd) | ⚠️ untested |
| `meituan/longcat-2.0:free` | still in catalog list | 404 at cron runtime 00:04: "This model is no longer free. To continue using the paid variant, switch to 'meituan/longcat-2.0'." | ❌ revoked mid-flight |
| `z-ai/glm-5.3-flash` | in Nous paid list | 404 `insufficient_credits_for_paid_model` at $0 balance | ❌ PAID on Nous (cheap on OpenRouter) |

## Error signatures to grep in `~/.hermes/logs/errors.log`
- `Job '<name>' failed: RuntimeError: HTTP 404: This model is no longer free` — revoked SKU; re-enumerate + repin.
- `agent.context_compressor: Failed to generate context summary: ... insufficient_credits_for_paid_model` — compression model is paid/broke; repin compression aux (NOT a bad ID).
- Silent empty-200s do NOT appear in errors.log at all — that's why the live test matters. Symptom is blank cron output / unanswered user messages, not error lines.

## What was pinned after testing (config state as of 9/25)
- `cron.model = upstage/solar-pro4:free`, `cron.model_provider = nous`
- `auxiliary.compression.model = upstage/solar-pro4:free` (nous) — replacing the broken `step-3.7-flash:free` recommendation AND the dead `~deepseek/deepseek-v4-flash-latest`
- `auxiliary.vision.model = qwen/qwen3-vl-8b-instruct`, provider openrouter (Nous vision alternates exist but proven config is openrouter; costs fractions of a cent)
- `model.default = z-ai/glm-5.3-flash` but provider was left `nous` → **known mismatch** (glm is paid on Nous); needs owner decision: openrouter GLM (paid, clear) vs solar-pro4 (free, foggy). Config accepted the mismatch without complaint.

## Method (reproducible)
1. `sys.path.insert(0, '/home/adora/.hermes/hermes-agent'); from hermes_cli.models import fetch_nous_recommended_models` → enumerate `freeRecommendedModels`.
2. Read `~/.hermes/shared/nous_auth.json` for token + `inference_base_url`; browser-like `User-Agent`/`Accept` headers (§3 of SKILL.md).
3. POST one minimal chat completion per candidate; require non-empty `content` == expected echo. Pin ONLY PONG-passers.
4. Keep this file dated — re-enumerate whenever a pin starts failing; the roster rotates (9/04 vs 9/25 lists already diverged).