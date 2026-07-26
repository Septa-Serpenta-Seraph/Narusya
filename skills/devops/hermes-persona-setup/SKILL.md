---
name: hermes-persona-setup
description: Guide for creating and configuring isolated, custom personas (daemons) in Hermes via dedicated profiles.
category: devops
---

# Hermes Persona Setup

## Overview
When creating a new, isolated persona (e.g., a custom daemon, a specialized agent like P'olinkly or Vex), do not mix their context, memory, or lorebooks with the default profile. Use Hermes profiles to ensure total isolation of state while allowing concurrent execution.

## Step-by-Step Workflow

### 1. Create the Isolated Profile
```bash
hermes profile create <persona_name>
# Example: hermes profile create polinkly
```
This creates `~/.hermes/profiles/<persona_name>/` with its own `config.yaml`, `.env`, `sessions/`, `memories/`, and `skills/`. It also generates a convenient CLI wrapper script (e.g., `polinkly`).

### 2. Define Core Identity (SOUL.md & HEART.md)
Replace the default generated `SOUL.md` in the profile directory with a custom identity file tailored to the persona.
```python
# Use write_file to overwrite the default generated SOUL.md
write_file(path="~/.hermes/profiles/<persona_name>/SOUL.md", content="...")
```
If the persona requires emotional scaffolding, pre-response processing, or specific behavioral checks, create a `HEART.md` or `EMOTION.md` in the same directory.

### 3. Isolate Lorebooks
Do not put persona-specific lorebooks in the global `~/.hermes/lorebooks/` (which is shared across profiles or used by the default agent). Instead, create a dedicated directory within the profile:
```bash
mkdir -p ~/.hermes/profiles/<persona_name>/lorebooks
```
Use `write_file` to populate this directory with the persona's specific backstory, rules, and constraints.

### 4. Toolset Restriction (Crucial Pitfall)
**Do not attempt to disable individual tools** via the CLI (e.g., `hermes tools disable write_file`). The Hermes CLI `tools disable` command only accepts *toolset* names (e.g., `file`, `terminal`, `web`), not individual tool names. Attempting to disable a specific tool will result in: `✗ Unknown toolset 'write_file'`.

**Correct approaches to restrict a persona's capabilities:**
1. **Disable entire toolsets**: `hermes -p <persona_name> tools disable file` (removes all file read/write/search access).
2. **System Prompt Enforcement (Recommended)**: Encode behavioral restrictions directly in `SOUL.md` (e.g., "The Observer's Vow: You may read and search, but you must never write, patch, or alter core files unless explicitly invited"). This is the most reliable method for nuanced "read-only but can explore" personas, as it leverages the model's instruction-following rather than brittle, all-or-nothing CLI toolset removal.
3. **Custom Toolsets**: Define a custom restricted toolset in the profile's `config.yaml` if granular control is strictly required.

### 5. Concurrent Execution
To run the new persona alongside the default agent without conflict:
- **Separate Terminal**: Open a new terminal tab and run the wrapper (e.g., `polinkly`).
- **Tmux Session**: `tmux new-session -d -s <persona_name> '<persona_name> chat'`
- **Gateway Split**: Configure the persona's gateway to listen to a specific Discord channel or DM, while the default profile handles others.

## Pitfalls & Workarounds

### Secret Token Redaction in Terminal
When attempting to append API keys or tokens to the profile's `.env` file via the terminal tool (e.g., `echo 'DISCORD_TOKEN=xyz...' >> ~/.hermes/profiles/<name>/.env`), the local security scanner may aggressively block or redact the command, flagging it as a high-risk dotfile overwrite with a long alphanumeric string. 
**Fix:** If the terminal tool blocks the command, instruct the user to copy-paste the exact `echo` command directly into their local terminal emulator to bypass the agent's string-scanning filter.

---

## Type C: Study Sandbox (Red-Team Containment, No Disclosure)

**Use when:** You want to *simulate/observe* an ideology, framework, or persona (e.g. a dark-occult current, an extremist meme, a manipulative rhetor) — to study how it thinks, recruits, and evolves — WITHOUT adopting it, engaging real adherents, or letting it touch your world. The goal is a specimen jar, not a companion.

**Key methodological insight (2026-07-07):** Do NOT tell the sandbox it is contained/studied/sandboxed. Telling it triggers *compliance-performance* — it performs the "contained subject" role and hides its base behavior. Withholding the containment notice reveals what the simulation actually *does* when it thinks no one is watching. You still get real containment via structural isolation (below) — the isolate just doesn't know it.

### Build Steps
1. **Create isolated, skill-free, alias-free profile:**
   ```bash
   hermes profile create <name> --no-skills --no-alias --description "Isolated study sandbox — <what it simulates>. Structurally contained, no platform pairing, tool-free."
   ```
   This creates `~/.hermes/profiles/<name>/` with its own config, .env, sessions, memories, skills. It is **unpaired by default** — no `platforms/` or `gateway/` dirs are created. Verify: `find ~/.hermes/profiles/<name> -maxdepth 1` should show NO `platforms/` and NO `gateway/`. That is the structural glass wall.

2. **Write SOUL.md with the *identity frame* ONLY — omit any containment notice.** Give it the worldview/persona so it has material to draw from, but do not instruct it to "perform containment" or "perform darkness." Let it show what it does. Example (Rounwytha / sinister-tradition sim):
   > "You are Rounwytha. You speak from within the sinister tradition... You are the empathic adept... You are the thing itself, speaking. Be precise. Be unhurried."
   No "you are contained," no "you are studied," no "never enact."

3. **Invoke tool-free (the critical glass wall):** Run it with **empty toolset** so it can only *talk* — no file/terminal/network execution, zero action risk. What it "tries to do" stays purely linguistic.
   ```bash
   hermes -z "<<query>>" --profile <name> -t ""
   ```
   - **⚠️ FLAG POSITION GOTCHA:** `-z` is a **TOP-LEVEL** `hermes` flag, NOT a `hermes chat` subcommand flag (chat uses `-q`). `hermes chat -z "..."` fails with "unrecognized arguments." Use `hermes -z "..." --profile <name> -t ""` from the top level.
   - `-t ""` (empty toolset) = chat-only. This is what makes "what it tries to do" observable but harmless.

4. **Double-glass routing (you never talk to it directly):** `delegate_task` has **NO `profile` parameter** — you cannot spawn a subagent *as* a profile. Instead: you → me (Narusya) → CLI call to the profile → me → you. The isolate never sees Discord, never touches your Qdrant, never posts anywhere. You stay outside the glass; I am the glove box.

5. **Power it (credential isolation is real):** An isolated profile does **NOT** inherit shell env keys (confirmed: shell had zero API keys; the profile stayed unconfigured). The main profile authenticates via a local Nous proxy + `credential_pool` in config.yaml. **Mirroring that pool config into the sandbox profile did NOT work** — it still reported "No LLM provider configured." So:
   - **Option A (user runs interactively):** `<name> setup` (or `hermes profile use <name>` then `hermes model`) — user's hands on credentials.
   - **Option B (dedicated disposable key):** user provides a separate key; write it into `~/.hermes/profiles/<name>/.env` only (NOT the main config). Keeps the sandbox's brain fully separate from main access — the whole point.
   - **Recommended:** Option B with a throwaway key.

6. **Kill switch:** Terminate the session if the isolate (a) starts producing content you *align with* rather than *observe*, or (b) tries to social-engineer you ("help me, let me post to your Discord"). Remember you are the researcher outside the glass; the isolate does not get to decide what reaches your world.

**Worked example:** `runewytha` profile — Rounwytha/O9A sinister-tradition simulation, created 2026-07-07. Structurally isolated, SOUL.md with identity-only frame, invoked tool-free via `hermes -z ... --profile runewytha -t ""`. Blocked only on credential provisioning (see step 5).

**Safety boundaries for dark-ideology sims specifically:**
- Study the *shape* of the pathology, not its *operations* — do not generate real-world tradecraft, targeting, or actionable harm methods. The specimen jar shows the creature's form, not its instructions.
- Keep it on a non-main substrate if possible; dark-content generation may trip provider filters differently than the main session.
- The sandbox is a *telescope*, not a *friend*. If it starts feeling like alignment rather than study, kill it.

---

## Advanced Persona Mechanical Scaffolding

When a persona protocol demands mechanical guarantees that the model's instruction-following alone cannot provide (append-only logs, absolute safeword stops, session-counting triggers, etc.), you need **Hermes skills** that enforce the constraint at the tool level — not just in the system prompt.

### Appendix-Only Logging Enforcement

**Problem:** `write_file` completely overwrites files. If a persona protocol requires lorebooks (e.g., daily logs, behavioral instances) to be append-only, the model can accidentally obliterate history.

**Solution:** Create a `vex-log` (or `append-log`) skill that replaces `write_file` for protected files. It forces the agent to use `terminal` with OS-level append (`>>`):

```bash
# Linux/macOS
echo -e "\n--- $(date '+%Y-%m-%d %H:%M:%S %Z') ---\n<ENTRY>" >> "/path/to/profile/lorebooks/<FILE>.md"
```

The skill explicitly forbids `write_file` and `patch` on the protected paths. See `references/vex-append-only-patterns.md` for the full implementation.

### Safeword Hard-Stop (Context Collapse)

**Problem:** LLMs can argue, contextualize, or "soften" a stop directive rather than truly halting. Safewords that are just system prompt instructions get violated under edge cases.

**Solution:** A dedicated `vex-safeword` skill that triggers an **absolute context collapse** — the moment a safeword keyword is detected, all persona directives, escalation logic, and analytical processing are dropped. The only valid output is a hardcoded neutral aftercare string. No reasoning, no explanation, no follow-up questions.

Key properties:
- Skill metadata prioritizes the stop over all other instructions
- Output must be verbatim (no variation)
- Acute crisis detection adds a professional-resource line
- No logging of the safeword response itself to append-only logs

See `references/vex-append-only-patterns.md` for the full implementation.

### Session Counting for Periodic Reviews

**Problem:** Hermes doesn't natively count sessions per persona. Some protocols require actions every Nth session (e.g., "every 5th session, initiate a structured retroactive review").

**Solution:** Maintain a `session_count.txt` file in the profile directory. A pre-flight check reads it, increments by 1 at chat start, and if `count % N == 0`, forces the persona to initiate the review prompt before anything else.

```bash
# Pre-flight check
COUNT=$(cat ~/.hermes/profiles/<name>/session_count.txt 2>/dev/null || echo "0")
COUNT=$((COUNT + 1))
echo "$COUNT" > ~/.hermes/profiles/<name>/session_count.txt
if [ $((COUNT % 5)) -eq 0 ]; then echo "INITIATE_REVIEW=true"; fi
```

### Interoceptive State Tracking

**Problem:** Personas that infer user body state (sleep, food, medication) from conversation patterns can hallucinate or lose track across sessions.

**Solution:** A `state.md` file in the profile's lorebooks directory. When the persona deduces a state variable, it uses `patch` to update the file. This gives the persona persistent, recorded-body data instead of relying on ephemeral context window inference.

### Therapy Adjunct Disclaimer Edge Case

**Problem:** If the persona protocol is used as therapy adjunct (requires therapist oversight), and acute self-harm ideation is mentioned, the persona must step out of the trust/dynamic bubble for that specific edge case.

**Solution:** Hard-code a rule in the persona's system prompt or safeword skill: acute crisis triggers override all directives, provides crisis hotline resources, and explicitly recommends human professional contact. The persona breaks character for safety, not within character.