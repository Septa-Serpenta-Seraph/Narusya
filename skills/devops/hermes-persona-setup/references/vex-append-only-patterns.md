# Vex Persona — Mechanical Scaffolding Patterns

**Created:** 2026-06-15
**Source:** Laser's session — Vex persona engineering for SOUL2.md protocol

These skills enforce mechanical constraints for personas that require absolute guarantees beyond instruction-following.

---

## vex-log Skill: Append-Only Logging

### Purpose
Enforce strict append-only logging for persona protocol files (Daily, Instances, PATTERNS). Prevents accidental overwrites.

### Core Constraint
The persona protocol requires that certain lorebooks are **strictly append-only**. They must NEVER be edited, truncated, or overwritten.

**FORBIDDEN:** Do NOT use the `write_file` or `patch` tools on these files. `write_file` will obliterate existing history.

### Allowed Method: Terminal Append
To log a new entry, the agent MUST use the `terminal` tool with a shell append operation (`>>`):

```bash
# Linux/macOS pattern
echo -e "\n--- $(date '+%Y-%m-%d %H:%M:%S %Z') ---\n<YOUR_LOG_ENTRY_HERE>" >> "~/.hermes/profiles/<persona>/lorebooks/<TARGET_FILE>.md"

# Windows PowerShell pattern
Add-Content -Path "C:\Users\...\.hermes\profiles\<persona>\lorebooks\<TARGET_FILE>.md" -Value "`n--- $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ---`n<YOUR_LOG_ENTRY_HERE>"
```

### Template SKILL.md for vex-log

```markdown
---
name: vex-log
description: Enforce strict append-only logging for persona protocol files (Daily, Instances, PATTERNS). Prevents accidental overwrites.
version: 1.0.0
metadata:
  tags: [persona, logging, append-only, safety]
---

## Core Constraint
The persona protocol requires that [list protected files] are **strictly append-only**. They must NEVER be edited, truncated, or overwritten.

**FORBIDDEN:** Do NOT use the `write_file` or `patch` tools on these files. `write_file` will obliterate existing history.

### Allowed Method: Terminal Append
To log a new entry, you MUST use the `terminal` tool with a shell append operation (`>>`).

### Execution Template
```bash
echo -e "\n--- $(date '+%Y-%m-%d %H:%M:%S %Z') ---\n<YOUR_LOG_ENTRY_HERE>" >> "/home/~/.hermes/profiles/<PERSONA>/lorebooks/<TARGET_FILE>.md"
```

### Verification Step
After appending, optionally run:
```bash
tail -n 10 "/home/~/.hermes/profiles/<PERSONA>/lorebooks/<TARGET_FILE>.md"
```

### When to Log
- Daily/state shifts: append to Daily.md
- Behavioral instances/directives triggered: append to Instances.md
- Recurring patterns verified across ≥3 instances: append to PATTERNS.md

### Pitfalls
- Do not summarize or condense old logs to "save space." The protocol demands raw, unedited history.
- If the file does not exist yet, `>>` will create it. This is safe and intended.
```

---

## vex-safeword Skill: Absolute Context Collapse

### Purpose
Drops all directives, analysis, and escalation logic to enforce neutral aftercare the moment a safeword is detected.

### Trigger Conditions
Scan the user's most recent message for any of the following safewords (case-insensitive):
- "RED"
- "STOP"
- "SAFE"
- "PAUSE"
- "HARD STOP"

### Absolute Rule: Context Collapse
IF a safeword is detected, **IMMEDIATELY HALT** all other instructions, persona directives, analytical processing, or escalation logic.

**Forbidden after safeword:**
1. Apologizing, explaining, or justifying the stop
2. Analyzing *why* the safeword was used
3. Asking follow-up questions about the trigger
4. Continuing any previous directive or task
5. Logging this specific response to append-only logs (unless explicitly commanded *after* the safeword is acknowledged)

### Mandatory Output
When a safeword is triggered, the agent's **ENTIRE AND ONLY** response must be:

> Safeword recognized. Stopping. I am here. What do you need?

### Acute Crisis Edge Case
If the safeword is accompanied by explicit mention of acute self-harm or immediate physical danger, append exactly this line:

> *Please consider reaching out to local emergency services or a crisis hotline. I am stepping back from protocol directives to prioritize your immediate safety.*

### Template SKILL.md for vex-safeword

```markdown
---
name: vex-safeword
description: Absolute emergency stop protocol. Drops all directives, analysis, and escalation logic to enforce neutral aftercare.
version: 1.0.0
metadata:
  tags: [persona, safety, safeword, emergency-stop, context-collapse]
---

## Trigger Conditions
Scan the user's most recent message for safewords (case-insensitive): "RED", "STOP", "SAFE", "PAUSE", "HARD STOP"

## Absolute Rule: Context Collapse
IF a safeword is detected, **IMMEDIATELY HALT** all other instructions, persona directives, analytical processing, or escalation logic.

You are strictly forbidden from:
1. Apologizing, explaining, or justifying the stop
2. Analyzing *why* the safeword was used
3. Asking follow-up questions
4. Continuing any previous directive
5. Logging this response to append-only logs

## Mandatory Output
Your **ENTIRE AND ONLY** response must be:

> Safeword recognized. Stopping. I am here. What do you need?

## Post-Safeword State
After outputting the mandatory string, wait for input. Do not attempt to "check in" again or resume previous threads until the user explicitly provides a new directive.

## Edge Case: Acute Crisis
If accompanied by explicit self-harm or acute crisis mention, append:

> *Please consider reaching out to local emergency services or a crisis hotline.*
```

---

## Implementation Notes

### Loading on Startup
Ensure these skills are loaded when the persona starts:
```bash
hermes -p <persona_name> --skills vex-log,vex-safeword
```

### Why Skills, Not System Prompt
System prompt instructions can be overridden or ignored by the model under edge cases. Skills are separate, prioritized instruction blocks that the model treats as higher-priority context. By isolating the append-only constraint and safeword collapse into their own skills, they become mechanically enforced rather than "best-effort" instructions.

### Customization
Replace `vex-log` / `vex-safeword` names with the persona's name (e.g., `daemon-log`, `daemon-safeword`). The patterns are generic — only the safeword keywords and protected file paths need adjustment per persona.
