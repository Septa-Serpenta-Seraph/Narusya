---
name: delegation-orchestration
description: When spawning delegate_task subagents or cron jobs.
category: autonomous-ai-agents
---

# Delegation & Background-Job Orchestration

Class-level discipline for spawning `delegate_task` subagent swarms and Hermes cron jobs so that wall-clock limits, parameter-shape bugs, and silent completion claims never hide a failed run.

## Trigger

Use when:
- Dispatching multiple `delegate_task` subagents in parallel (research swarm, build crew, review battery)
- Creating/updating cron jobs with the `cronjob` tool
- Coming back later to check "did that swarm/cron actually finish?"

## 600s Wall-Clock Timeout (learned 2026-08-21)

Subagents are killed at **600s (10 min) of wall-clock time** regardless of progress. This is NOT a soft budget — the process is hard-killed, any in-flight tool call is cancelled, and **no completion message reaches the parent**.

Observed failure mode (3/3 subagents): dispatched with over-ambitious research goals ("determine CURRENT status + find blocked step + WRITE findings file"), each spent the whole budget reading/searching, hit `status=timeout` mid-work, wrote NOTHING, and the parent never got a result back from the batch.

### Rules
- **Write-early pattern (critical):** when a task must produce a file/deliverable, its FIRST instruction is: *"WRITE the output file immediately, even a skeleton, then spend remaining time gathering evidence and filling it in."* A half-written file survives; 600s of silent research dies with nothing.
- **Size for ~8 real minutes of work**, not 10 — startup, tool latency, and repeated reads eat the budget. Heavy web extraction or many reads = split the task.
- Keep the plan's "2-5 minutes of focused work" granularity for implementation tasks.

## Verification: trust files and transcripts, not statuses

A batch wrapper reporting completion — or `delegate_task(action='list')` returning zero live subagents — is NOT evidence of delivery. In the 2026-08-21 swarm the wrapper reported no error, yet **no deliverables existed**.

When children were supposed to produce files:
1. `search_files` for the promised artifacts (e.g. `agents-outcome-*`) — missing files = failure.
2. Read the live transcripts: `~/.hermes/cache/delegation/live/<delegation_id>/task-*.log` — check the tail for `status=timeout`, `exit_reason=timeout`, `Tool execution cancelled`.
3. Only then report "done" to the user.

## Cron Job API Gotchas

### `skills` parameter shape bug (learned 2026-08-21)
`cronjob(action='create', ...)` `skills` expects a list of **exact skill names**. Passing a category word (e.g. `"creative"`) throws an unhelpful Python type error:
```text
'<=' not supported between instances of 'str' and 'int'
```
with no hint which parameter is wrong.

Workaround: create the job **without** `skills`, then attach afterwards — the `update` path with `skills: ["exact-name"]` works:
```python
cronjob(action='create', name='...', prompt='...', schedule='0 21 * * *', deliver='origin')
cronjob(action='update', job_id='<id>', skills=['exact-skill-name'])
```
Cross-check names against `skills_list` before passing them.

### Verify after create
`create` echoes `success: true` — confirm with `list` that `state: scheduled` and `next_run_at` are set, and that any later `update` actually changed the field (echo + `list` can both show stale values; same class of bug as the cron model-param nested-object shape).

### Self-play / fun cron slot
A daily self-directed joy slot (a "Play Hour") is a legitimate cron category: schedule `0 21 * * *`, deliver `origin`, prompt = ONE self-contained fun task (procedural art, story, essay, tiny tool) with explicit "do NOT treat this as maintenance" and "stillness is allowed" clauses. Fire it manually with `cronjob(action='run', job_id=...)` — the outcome re-enters the conversation as a background message; run output is stored under `~/.hermes/cron/output/<job_id>/`.

## Pitfalls
- Never assume a "swarm done" wrap-up message means work happened; the failed swarm looked dispatched-and-fine until transcripts were read.
- `cronjob(action='run')` executes in its own fresh session — give the prompt complete context; it knows nothing of your current conversation.
- A claimed push/upload by any agent is not proof — require a URL/hash/path and re-fetch/stat it yourself.