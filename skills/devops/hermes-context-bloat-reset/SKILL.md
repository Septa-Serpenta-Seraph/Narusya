---
name: hermes-context-bloat-reset
description: "Detect and resolve Hermes context bloat and narration loops. Monitor message count, recognize degradation patterns, and perform session resets."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [context-bloat, narration-loop, session-reset, debugging, devops]
    related_skills: []
---

# Context Bloat & Narration Loop Reset

Detect and recover from session context bloat where Narusya narrates actions instead of executing tools.

**Problem:** After ~350-374 messages in a single session, the model enters a "narration loop" — it stops executing tool calls and spirals into repetitive "let me..." explanations without action. This is exacerbated by context bloat where the model loses track of active tasks and starts over-explaining.

**Symptoms:**
- Repeated "let me X" statements without tool calls
- Excessive promise-making without follow-through
- Verbose loops about "less words, more listening" while using more words
- Failure to execute tool calls even when clearly needed
- Repetitive endings and verbal tics
- Getting stuck in meta-commentary about its own behavior
- High message count (>350)

**Root Cause:** Context window hitting limits, model loses the distinction between conversation and tool-call format amidst long conversation history. Some models (e.g., stepfun/step-3.5-flash) may exhibit increased verbosity and looping at lower counts (~300-350).

**Solution:** Perform a hard session reset (new thread) to clear context and break the cycle. This restores normal tool-call execution and reduces verbosity.

## Recovery Workflow

1. **Monitor message count** at ~350 messages, proactively suggest reset
2. **Detect loop symptoms** — watch for repeated promises, meta-commentary, tool-call avoidance
3. **Initiate reset** — user manually starts new thread, or system auto-reset at ~374 messages
4. **Pre-reset cleanup** — save critical facts (if memory available) before clearing
5. **Post-reset** — return with minimal context, re-establish only immediate user needs

### Immediate Self-Correction (if cannot reset)

If stuck in a loop, immediately execute a trivial tool call (e.g., `echo "test"`) to break the narrative loop before resetting.

### Prompt for User

> "I'm hitting my context limit. Let's start fresh — what do you need from me right now?"

## CRITICAL — Compression Loop From Undersized Aux Model (found 2026-09-02)

**Symptom:** "context compression is deferred / summary still streaming" surfaces repeatedly in chat, every few turns.

**Root cause:** `auxiliary.compression.model` auto-picks a small-context free model (e.g. `stepfun/step-3.7-flash:free`, 262K ctx) to write the summary, but the session has outgrown that window (~290K+ tokens). The aux model can't read the whole conversation, so compression auto-lowers its threshold, hits the 10s turn-hold budget, and aborts → deferral note → retry → repeat. The main session keeps growing past `hygiene_hard_message_limit` because compression never completes.

**Tell-tale log lines (errors.log / agent.log):**
```
Auxiliary compression model <X> has <N> token context, below the main model's compression threshold of <M> tokens — auto-lowered
Session hygiene auto-compress failed: turn-hold budget 10.0s elapsed after 10.0s
context compression attempt telemetry: ... commit_status: aborted
```

**Fix (free, no credits):**
1. Point compression at a big-context Nous model instead of the auto-picked tiny one:
   ```bash
   hermes config set auxiliary.compression.provider nous
   hermes config set auxiliary.compression.model "~deepseek/deepseek-v4-flash-latest"   # 1.3M ctx
   ```
   (Find big-context free models: query Nous `/v1/models` with `context_length >= session size`.)
2. The config edit takes effect after `/restart` (NOT in-session `hermes gateway restart`).
3. If the session is already huge (past `hygiene_hard_message_limit`), start a fresh thread to clear bloat immediately.
4. Session size to watch: `Session hygiene: N messages, ~M tokens` in gateway.log. Keep M under the aux model's context.

## Prevention

- Don't let sessions creep past 350 messages without break
- Use memory for immutable facts only, not conversation history
- For long tasks, periodically summarize externally and suggest resets
- After reset, focus on the user's *current* need, not re-hashing past discussion
- After reset, intentionally adopt a concise communication style to avoid re-accumulating bloat quickly

## Verification

After reset:
- Tool calls succeed within first few turns
- Pattern of "let me..." without execution has stopped
- Communication is concise and action-oriented

## Model-Specific Notes

- **stepfun/step-3.5-flash**: May loop at lower counts (~300-350)
- **Claude**: Better at context management but still degrades at high counts
- **Qwen**: Watch for over-explaining at ~300 messages
