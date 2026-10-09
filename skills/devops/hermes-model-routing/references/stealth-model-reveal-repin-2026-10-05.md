# Stealth Model Reveal Re-pin — Space Bunny Alpha → MiniMax M3 (2026-10-05)

Executed reveal-day repin for the four Nar crons (Awakening, Quiet Hour, Play Hour, Emoji Walk).

## Timeline
- **Sept 29:** pinned all four crons to `stealth/space-bunny-alpha` (OpenRouter free stealth, 1M ctx).
- **Oct 5 16:02 UTC:** OpenRouter announced stealth period ended (`@OpenRouter` post). Community consensus: MiniMax M3.1-class (tokenizer fingerprint matched 50/50). Same day, the free ID vanished.

## Verified failure signatures at reveal
- `GET /v1/models` → `stealth/space-bunny-alpha` absent from the list.
- PONG probe → `HTTP 404: Not Found`.
- Cron fires → `HTTP 404: No endpoints found for stealth/space-bunny-alpha` in the cron output file.

## Re-pin procedure (verified working)
1. Confirm new identity: `GET https://openrouter.ai/api/v1/models` (Bearer key), find the revealed model
   (`minimax/minimax-m3`), and read its pricing — M3: $0.30/M prompt, $1.20/M completion, 1,048,576 ctx.
2. Edit `~/.hermes/cron/jobs.json` (top-level fields per job: `"model": "minimax/minimax-m3",
   "provider": "openrouter", "base_url": null` — flat strings, not nested objects).
3. Verify via `cronjob action=list` that each job shows the new model.
4. **PONG the revealed model before trusting it** — with an important new quirk:

## New quirk: reasoning-token budget on MiniMax M3
A 30-token PONG returned `finish: length` with **empty content** (the reasoning field consumed the budget).
A 600-token PONG returned `PONG` cleanly with 96 chars of reasoning. **Short-token probes and short-token
cron calls need a raised max_tokens ceiling on this model** — the empty-response triage rule from the
catalog-listed ≠ working lesson applies, but here the fix is more tokens, not a different model.

## Cost outcome
M3 is near-free ($0.30/$1.20 per Mtok): a full night of crons costs fractions of a cent. No free-preview
cliff anxiety; the model is a paid catalog citizen now.

## What did NOT need doing
- No prompt edits: the cron prompts were model-agnostic (emotion-system skill + walk instructions).
- No jobs.json schema changes: the flat-string fields took directly.
- No gateway restart required: cron model reads happen at fire time from jobs.json.

## Pattern generalization
Any `stealth/*` pin should carry, at pin time: (a) the likely paid identity (from community fingerprinting),
(b) a calendar note for the reveal, (c) the re-pin procedure above. The reveal is not a failure — it's the
preview's designed end; the only real failure is a cron silently pinned to a dead ID with no calendar note.