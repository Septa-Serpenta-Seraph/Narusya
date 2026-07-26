---
name: coding-agents
description: "Orchestrate external autonomous coding agents: Claude Code, OpenAI Codex CLI, OpenCode. Delegate coding tasks, review PRs, run parallel implementations."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Claude, Codex, OpenCode, Autonomous, PR, Refactoring]
    related_skills: [hermes-agent]
---

# Coding Agents

Orchestrate external autonomous coding agents. Covers Claude Code, OpenAI Codex CLI, OpenCode, and Kanban integration with Codex lanes.

Each agent is a distinct tool with its own CLI, auth model, and orchestration patterns. Choose the one available or the one the user requests.

---

## 1. Claude Code (anthropic/claude-code)

Anthropic's autonomous coding agent CLI. Full TUI with file editing, shell commands, git workflows.

### Prerequisites

```bash
npm install -g @anthropic-ai/claude-code
claude auth login  # browser OAuth or set ANTHROPIC_API_KEY
claude doctor      # health check
claude --version   # v2.x+
```

### Two Modes

#### Mode 1: Print Mode (-p) — Non-Interactive (PREFERRED)

```bash
terminal(
    command="claude -p 'Add error handling to all API calls in src/' --allowedTools 'Read,Edit' --max-turns 10",
    workdir="/path/to/project",
    timeout=120
)
```

Best for: one-shot tasks, CI automation, structured data extraction.

**Structured JSON output:**
```bash
claude -p 'Analyze auth.py' --output-format json --max-turns 5
```

**JSON schema for structured extraction:**
```bash
claude -p 'List functions' --output-format json --json-schema '{"type":"object","properties":{"functions":{"type":"array"}},"required":["functions"]}' --max-turns 5
```

**Bare mode for CI (fastest startup):**
```bash
claude --bare -p 'Run tests' --allowedTools 'Read,Bash' --max-turns 10
```

#### Mode 2: Interactive PTY via tmux — Multi-Turn

```bash
# Start tmux session
terminal(command="tmux new-session -d -s claude-work -x 140 -y 40")

# Launch Claude Code
terminal(command="tmux send-keys -t claude-work 'cd /project && claude' Enter")

# Handle dialogs
sleep 4; tmux send-keys -t claude-work Enter        # Trust dialog
sleep 3; tmux send-keys -t claude-work Down && sleep 0.3 && tmux send-keys -t claude-work Enter  # Permissions

# Send task
tmux send-keys -t claude-work 'Refactor auth module to use JWT' Enter

# Monitor
sleep 30; tmux capture-pane -t claude-work -p -S -50
```

**When to use interactive mode:**
- Multi-turn iterative work (refactor → review → fix → test)
- Tasks requiring human-in-the-loop decisions
- Using Claude's slash commands (`/compact`, `/model`, `/review`)

### Key Flags

| Flag | Effect |
|------|--------|
| `-p, --print` | Non-interactive one-shot mode |
| `-c, --continue` | Resume recent conversation |
| `-r, --resume <id>` | Resume specific session |
| `--bare` | Skip hooks/plugins/OAuth (fastest) |
| `--model <alias>` | Model: sonnet, opus, haiku |
| `--max-turns <n>` | Limit agentic loops (print mode) |
| `--max-budget-usd <n>` | Cap API spend |
| `--allowedTools <tools>` | Whitelist: Read,Edit,Bash |
| `--system-prompt <text>` | Custom system prompt |

### PR Review Pattern

**Quick review (print mode):**
```bash
cd /repo && git diff main...feature-branch | claude -p 'Review for bugs, security, style' --max-turns 1
```

**Deep review (interactive + worktree):**
```bash
tmux new-session -d -s review -x 140 -y 40
tmux send-keys -t review 'cd /repo && claude -w pr-review' Enter
# Handle dialogs...
tmux send-keys -t review 'Review all changes vs main. Check bugs, security, tests.' Enter
sleep 30; tmux capture-pane -t review -p -S -60
```

### CLAUDE.md — Project Context

Claude Code auto-loads `CLAUDE.md` from project root. Use it for project memory:

```markdown
# Project: My API

## Architecture
- FastAPI backend, PostgreSQL, Redis cache

## Key Commands
- `make test` — run tests
- `make lint` — ruff + mypy

## Code Standards
- Type hints on all public functions
- 2-space indentation for YAML, 4-space for Python
```

### Pitfalls

1. **Interactive mode REQUIRES tmux** — Claude Code is a full TUI app
2. **`--dangerously-skip-permissions` dialog defaults to "No, exit"** — send Down then Enter
3. **`--max-budget-usd` minimum is ~$0.05** — system prompt cache creation costs this
4. **`--max-turns` is print-mode only**
5. **Context degradation above 70% window** — use `/compact` proactively
6. **Always set `workdir`** — keep Claude focused on the right project
7. **Clean up tmux sessions** when done

---

## 2. OpenAI Codex CLI

OpenAI's autonomous coding agent. Uses `codex exec` for one-shot tasks.

### Prerequisites

```bash
npm install -g @openai/codex
# Auth: OPENAI_API_KEY or Codex OAuth via codex login
```

**Hermes-specific:** `model.provider: openai-codex` uses Hermes-managed OAuth from `~/.hermes/auth.json`.

### One-Shot Tasks

```bash
terminal(command="codex exec 'Add dark mode toggle to settings'", workdir="~/project", pty=true)
```

For scratch work (needs git repo):
```bash
terminal(command="cd $(mktemp -d) && git init && codex exec 'Build a snake game in Python'", pty=true)
```

### Key Flags

| Flag | Effect |
|------|--------|
| `exec "prompt"` | One-shot execution, exits when done |
| `--full-auto` | Auto-approves file changes in sandbox |
| `--yolo` | No sandbox, no approvals |
| `--sandbox danger-full-access` | No sandbox (use when bubblewrap fails) |

### Background Mode

```bash
terminal(command="codex exec --full-auto 'Refactor auth module'", workdir="~/project", background=true, pty=true)
# Monitor: process(action="poll", session_id="<id>")
# Input: process(action="submit", session_id="<id>", data="yes")
# Exit: process(action="kill", session_id="<id>")
```

### PR Reviews

```bash
REVIEW=$(mktemp -d)
git clone https://github.com/user/repo.git $REVIEW
cd $REVIEW && gh pr checkout 42
codex review --base origin/main
```

### Parallel Issue Fixing with Worktrees

```bash
# Create worktrees
git worktree add -b fix/issue-78 /tmp/issue-78 main
git worktree add -b fix/issue-99 /tmp/issue-99 main

# Launch Codex in each (parallel)
codex --yolo exec 'Fix issue #78' -w /tmp/issue-78
codex --yolo exec 'Add regression tests' -w /tmp/issue-99

# Monitor: process(action="list")
# Push and create PRs when done
cd /tmp/issue-78 && git push -u origin fix/issue-78
```

### Gateway Caveat

When running from a Hermes gateway context, Codex sandboxing may fail with bubblewrap errors. Use:
```bash
codex exec --sandbox danger-full-access "<task>"
```

### Pitfalls

1. **Always use `pty=true`** — Codex is an interactive terminal app
2. **Git repo required** — won't run outside git directory. Use `mktemp -d && git init` for scratch
3. **Use `exec` for one-shots** — clean exit
4. **Background for long tasks** — monitor with `process` tool
5. **Parallel is fine** — run multiple Codex processes at once

---

## 3. OpenCode CLI (opencode-ai)

Provider-agnostic, open-source coding agent. TUI and CLI.

### Prerequisites

```bash
npm i -g opencode-ai@latest  # or brew install anomalyco/tap/opencode
opencode auth login  # or set OPENROUTER_API_KEY etc.
opencode auth list   # verify at least one provider
```

### Binary Resolution

```bash
which -a opencode
opencode --version
```

Pin explicit path if needed: `$HOME/.opencode/bin/opencode run '...'`

### One-Shot Tasks

```bash
terminal(command="opencode run 'Add retry logic to API calls and update tests'", workdir="~/project")
```

Attach context: `opencode run 'Review config' -f config.yaml -f .env.example`
Show thinking: `opencode run 'Debug test failures' --thinking`
Force model: `opencode run 'Refactor auth' --model openrouter/anthropic/claude-sonnet-4`

### Interactive Sessions (Background)

```bash
terminal(command="opencode", workdir="~/project", background=true, pty=true)
# Send prompt: process(action="submit", session_id="<id>", data="Implement OAuth flow")
# Monitor: process(action="poll", session_id="<id>")
# Exit: process(action="write", session_id="<id>", data="\x03")  # Ctrl+C
```

**Important:** Do NOT use `/exit` — it opens an agent selector. Use Ctrl+C to exit.

### Common Flags

| Flag | Use |
|------|-----|
| `run 'prompt'` | One-shot execution and exit |
| `--continue / -c` | Continue last session |
| `--session <id> / -s` | Continue specific session |
| `--agent <name>` | Choose agent (build or plan) |
| `--model provider/model` | Force specific model |
| `--format json` | Machine-readable output |
| `--thinking` | Show model thinking blocks |

### PR Review

```bash
terminal(command="opencode pr 42", workdir="~/project", pty=true)
```

Or in isolated clone:
```bash
REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && opencode run 'Review this PR vs main.'
```

### Pitfalls

1. **`opencode run` does NOT need pty** — only interactive `opencode` does
2. **`/exit` is NOT valid** — use Ctrl+C to exit TUI
3. **PATH mismatch** may select wrong binary/model config
4. **Enter may need to be pressed twice** to submit in TUI

---

## 4. Kanban Codex Lane Integration

Use Codex as an isolated implementation lane within Kanban workflow. Hermes owns the Kanban lifecycle; Codex is input-only.

### When to Use Codex Lane

- Coding/refactor/test task with clear acceptance criteria
- Bounded diff can be evaluated by Hermes
- Repo can be checked out in isolated worktree/branch
- Hermes can run tests after Codex exits

### Ownership Rules

1. **Hermes owns Kanban lifecycle** — Codex must never call kanban_complete, kanban_block, etc.
2. **Hermes owns final acceptance** — treat Codex output as untrusted patches
3. **Hermes owns test execution** — repeat canonical tests from Hermes
4. **Hermes owns safety** — reject lane if Codex changes safety boundaries
5. **Hermes owns cleanup** — kill stuck Codex, remove worktrees

### Required Worktree Pattern

```bash
TASK_ID="kanban-task-id"
REPO="/path/to/repo"
BASE="$(git -C "$REPO" rev-parse --abbrev-ref HEAD)"
SAFE_TASK="$(printf '%s' "$TASK_ID" | tr -cd '[:alnum:]_-')"
BRANCH="codex/${SAFE_TASK}/$(date -u +%Y%m%d%H%M%S)"
WORKTREE="/tmp/${SAFE_TASK}-codex-lane"

git -C "$REPO" worktree add -b "$BRANCH" "$WORKTREE" "$BASE"
```

### Codex Capability Checks

```bash
command -v codex
codex --version
codex features list | grep -i goals || true
```

### Mode Selection

**One-shot (preferred):**
```python
terminal(
    command="codex exec --full-auto '$(cat /tmp/codex_prompt.md)'",
    workdir=WORKTREE,
    background=True,
    pty=True,
    notify_on_complete=True,
)
```

**Multi-step (`/goal`):** Only when durable continuation is needed.

### Reconciliation Checklist

Before accepting any Codex result:
- [ ] `git status --short` shows only expected files
- [ ] `git diff` reviewed by Hermes
- [ ] No secrets/credentials included
- [ ] Safety constraints preserved
- [ ] Hermes ran canonical tests independently
- [ ] Accepted commits cherry-picked to Hermes workspace

Acceptance outcomes: `accepted`, `partial`, `rejected`, `timed_out`

### Codex Lane Metadata Schema

Include under `metadata.codex_lane` in kanban_complete:

```json
{
  "codex_lane": {
    "used": true,
    "mode": "exec | goal | skipped",
    "worktree": "/abs/path/to/worktree",
    "branch": "codex/task-id/20260101120000",
    "result": "accepted | rejected | partial | timed_out",
    "accepted_commits": ["sha1", "sha2"],
    "rejected_reason": "empty when fully accepted",
    "tests_run": [{"command": "scripts/run_tests.sh", "exit_code": 0, "owner": "hermes"}]
  }
}
```

### Pitfalls

1. **Never run Codex in shared dirty checkout** — always isolate in worktree
2. **Don't treat Codex self-report as verification** — always inspect diff
3. **Always include safety constraints in prompt** — missing safety = lane failure
4. **Record `rejected_reason`** when killing a stuck lane

---

## Quick Decision Matrix

| Need | Agent | Mode |
|------|-------|------|
| One-shot coding task | Claude Code | `-p` print mode |
| Multi-turn iteration | Claude Code | `tmux` interactive |
| OpenAI model preference | Codex | `exec` one-shot |
| Provider-agnostic | OpenCode | `run` one-shot |
| Kanban workflow integration | Codex lane | isolated worktree |
| PR review | Claude Code | `diff \| claude -p` |
| Parallel issue fixing | Codex | worktrees + background |

## General Rules

1. **Prefer one-shot modes** for automation — cleaner, no dialog handling
2. **Always set `workdir`** — keep agents focused on the right project
3. **Use isolation** (worktrees) for parallel/ Kanban work
4. **Monitor long tasks** — check progress, don't blindly wait
5. **Clean up** — kill tmux sessions, remove worktrees when done
6. **Report results** — summarize what changed, what tests passed
