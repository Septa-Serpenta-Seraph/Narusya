# Auditing a fix for missed sibling call paths

Triggered by Adora's **"want to double check your work?"** — always literal, never
rhetorical. On 2026-08-26 that question caught 3 live bugs in a fix already reported done.

## The failure mode

You find a bug, patch where it manifests, verify it compiles, report success. But Hermes
duplicates agent-construction logic across **surfaces** (gateway / cron / TUI-desktop /
CLI-foreground / CLI-background). A config value forwarded wrongly in one is usually
forwarded wrongly in all of them. Fixing the one you reproduced leaves the rest broken,
and they fail later, silently, somewhere you are not watching.

## Procedure

1. **Grep the whole tree for the exact kwarg/pattern, not the file you fixed:**
   ```bash
   grep -rn "<kwarg>=" --include="*.py" . | grep -v "/tests/"
   ```
2. **Classify every hit** before touching it — do not blanket-patch:
   - **Sender** → needs the guard.
   - **Receiver** (the function's own parameter, e.g. `run_agent.py`) → no change.
   - **Inheritor** (reads an already-gated parent attr, e.g. `tools/delegate_tool.py`)
     → no change; safe by propagation. Verify the parent is gated.
   - **Explicit caller config** (e.g. `batch_runner.py`) → no change.
3. **Prefer one hoisted gate variable** per site over repeating a ternary six times:
   ```python
   _ok = (runtime.get("provider") if isinstance(runtime, dict) else None) == "openrouter"
   _pr = pr if (_ok and isinstance(pr, dict)) else {}   # empty dict keeps .get() valid
   ```
4. **Compile every touched file:**
   ```bash
   for f in <files>; do python3 -c "import ast; ast.parse(open('$f').read())"; done
   ```
5. **Write an executable assertion, not a claim.** Import the real function and test both
   the positive and negative branch plus malformed input. See
   `scripts/verify_routing_gate.py`.
6. **Separate pre-existing lint from regressions.** `git stash` → re-check → `git stash pop`
   proves a warning predates you. Mixin attrs (`self._providers_*`) and untyped
   `runtime.get()` args generate Pyright noise that is NOT yours.

## Reporting honestly

State what is **verified** vs **pending** separately. After this audit the honest summary
was: 5 files patched + all compile + gate unit-tested = verified; gc unfinished, no live
push test yet, `/restart` still required = pending. Adora reads a mixed report as
trustworthy; a uniformly triumphant one that later cracks costs far more.

## Pitfall

Do not treat "it compiles" or "the diff looks right" as verification. Neither exercises the
branch. Only importing the function and asserting both outcomes does.
