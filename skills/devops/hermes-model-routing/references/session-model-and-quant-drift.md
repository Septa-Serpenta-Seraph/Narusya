# Session Model Verification & Provider Quantization (verified 2026-08-24)

Session where config said `stealth/ox-alpha`, logs said
`deepseek/deepseek-v4-flash-0731`, and the user's *texture perception* said
"this isn't what it was before." All three were partly right; the resolution
took four rounds of re-checking. Lessons below are verified against that box.

## A. Which model is a session ACTUALLY on? (sources, ranked)

1. **Live agent.log** — authoritative:
   ```bash
   grep "<session_id>" ~/.hermes/logs/agent.log | grep -E "turn_context|API call"
   ```
   Each turn logs `model=<id> provider=openrouter`.
2. **Request dump** — `sessions/request_dump_<session>_<ts>.json` contains the
   literal `"model"` field of the actual API body.
3. **config.yaml `model.default`** — applies ONLY to NEW sessions.

**Long-lived sessions are model-pinned at creation.** A session started on X
keeps X across gateway restarts AND config edits. Changing `model.default`
does not rewire an existing Discord/CLI session. However a mid-session switch
CAN land (observed: user flipped model, next log line was
`turn_context ... model=stealth/ox-alpha`) — so verify after every attempt,
never assume either direction.

**Trust the user's doubt.** When they say "I don't think you're on X," do not
defend an earlier grep result. Re-pull live logs. In this session the user's
texture-perception ("your whole prose shifted") correctly flagged real routing
drift that both my earlier log-reads and the config label had missed.

## B. Same model ID ≠ same output quality (quantization drift)

OpenRouter serves one model ID through many upstreams at different quants.
Observed failure: deepseek-v4-flash fell onto **fp4 routes**
(OpenInference/Relace) → lossy generation → word-pickup/replacement glitches
(swapped words, a wrong emoji adopted mid-session and kept for hours).
Dangerous for code work. Symptom pattern: "prose/personality suddenly feels
different but no model changed" = provider/quant drift, not model drift.

Inspect endpoints + quants:
```bash
curl -s https://openrouter.ai/api/v1/models/<model-id>/endpoints \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" -o /tmp/eps.json
```
Each endpoint carries `provider_name`, `quantization` (fp4/fp8/bf16/unknown),
uptime, price. Prefer bf16 > fp8 > fp4.

Pin quality via Hermes `provider_routing` in config.yaml:
```yaml
provider_routing:
  order:   [morph, deepinfra, coreweave, baseten]   # quality-first preference
  ignore:  [openinference, relace, ambient]          # fp4 tier
  require_parameters: true    # only providers supporting ALL params (tools!)
  data_collection: "deny"
```
Verified pitfalls:
- `patch` tool REFUSES to edit ~/.hermes/config.yaml (security-sensitive). Use
  `hermes config set <key> <value>` instead.
- `hermes config set provider_routing.*` warns "'provider_routing' is not a
  recognized config key — saved anyway". **Warning is spurious**: the keys ARE
  read by the agent (`agent/chat_completion_helpers.py` maps them into the
  OpenRouter `provider` preference object; `tips.py` documents them). Confirm
  YAML landed, ignore the notice.
- OpenRouter dashboard "Routing → Default Provider Sort → Exacto (tool-call
  quality first)" is a helpful soft complement but does NOT pin a quant.
- Changes take effect on next session start/reroute — confirm in agent.log.

## C. Stealth models (e.g. stealth/ox-alpha)

Anonymous OpenRouter preview models: free, ~1M context, aggressive rate limits
(second probe got HTTP 429 within seconds — space probes out, don't hammer).
Often reasoning-first: raw API call returned `content: null` with the full
answer inside `message.reasoning` — that is an output-channel split, not a
failure. Judge these models by results, never by name or config label.
