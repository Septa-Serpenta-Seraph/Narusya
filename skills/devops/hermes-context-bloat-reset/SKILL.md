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
