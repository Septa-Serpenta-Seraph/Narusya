# Free-model rosters + compression-slot decisions — snapshot 2026-09-26/27

Extends `nous-free-roster-2026-09-25.md`. Second round of live-testing after
solar-pro4:free turned out too small for the compression slot.

## OpenRouter free roster (9/26 ~23:47 MDT, balance $8.41 remaining)
21 free models; only 8 with context_length >= 500000 (the compression job
needs big ctx — session was ~200K tokens live):

| Model | ctx | Live test | Verdict |
|---|---|---|---|
| `stealth/space-bunny-alpha` | 1,000,000 | PONG ✅ + real one-sentence summary ✅ | ✅ WINNER — now pinned for compression |
| `nvidia/nemotron-3.5-lightning:free` | 1,000,000 | responds but content is raw chain-of-thought leak ("Here's a thinking process:...") | ⚠️ bad for summaries |
| `dots-studio/dots-3-note-preview:free` | 512,000 | HTTP 200, empty content | ❌ silent death |
| `thinkingmachines/inkling-small:free` | 1,048,576 | 403 "only available on agentic harnesses" | ❌ locked |
| `thinkingmachines/inkling:free` | 1,048,576 | (untested, same family) | ⚠️ suspect same lock |
| `google/lyria-3-pro-preview` / `lyria-3-clip-preview` | 1,048,576 | (untested — lyria is an audio model family, suspect) | ⚠️ |
| `nvidia/nemotron-3-ultra-550b-a55b:free` | 1,000,000 | (untested) | ⚠️ candidate |
| 13 smaller free models (ling/gemma/qwen27b/laguna/cohere/liquid/openrouter/free...) | 64K–262K | — | too small for compression; fine for crons |

## Compression-slot failure signature (verified 9/26)
Solar-pro4:free (524,288 ctx) below the main model's compression threshold
(786,432) → Hermes auto-lowered session threshold → compressor **aborted**:
```
grep 'context compression attempt telemetry' ~/.hermes/logs/agent.log
telemetry: {"commit_status":"aborted","failure_class":"explicit_interrupt","chunk_count":0,...}
```
Two aborted attempts in one night (23:39 + 23:41); conversation itself
unaffected (session was only ~15% of ceiling). Also repeated warning:
`Auxiliary compression model upstage/solar-pro4:free has 524288 token context,
below the main model's compression threshold of 786432 tokens`

## Balance check (reproducible)
`curl -s https://openrouter.ai/api/v1/credits -H "Authorization: Bearer $OPENROUTER_API_KEY"`
→ `data.total_credits - data.total_usage` = remaining. 9/26: $480 lifetime,
$471.59 used, **$8.41 left** (four $10 top-ups by Adora since August).

## Final routing map (as of 9/27)
- cron.model = upstage/solar-pro4:free (nous) — PONG-verified
- auxiliary.compression = stealth/space-bunny-alpha (openrouter) — verified chat + summary
- auxiliary.vision = qwen/qwen3-vl-8b-instruct (openrouter)
- model.default = z-ai/glm-5.3-flash (nous) — **MISMATCH UNRESOLVED** (paid on nous); owner decision pending: openrouter GLM (paid, clear) vs solar-pro4 (free, foggy).