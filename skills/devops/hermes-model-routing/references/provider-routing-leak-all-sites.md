# provider_routing leaks to non-OpenRouter providers — ALL injection sites

Companion detail for §0 of SKILL.md. **§0 as originally written was incomplete: it named
only `gateway/run.py`.** Patching just the gateway fixes interactive chat and leaves every
cron job broken with the identical error. Use this file as the authoritative site list.

## Symptom

Any session or cron run on a non-OpenRouter provider (notably `nous`) dies instantly:

```
Error code: 400 - {'status': 400, 'message': 'This endpoint does not honor caller-supplied
`provider` routing preferences (e.g. `only`, `ignore`, `order`, `data_collection`, `zdr`,
`require_parameters`, `sort`). Routing is decided centrally per model, so these fields are
not enforced — sending them would give a false sense of control (e.g. over data
collection). Remove the `provider` object from your request. For enforced provider routing,
call OpenRouter directly with your own key.'}
```

The model connects fine — `agent.log` shows `provider=nous model=meituan/longcat-2.0:free`
— and is then rejected on the routing object. So "the restart didn't work" is the wrong
diagnosis; read the log before blaming the restart.

## Root cause

`provider_routing:` in `config.yaml` is a **global top-level block**, but it is an
OpenRouter-only feature (`hermes_cli/tips.py`: "provider_routing controls OpenRouter
provider sorting, whitelisting, and blacklisting"). Multiple call sites forward its fields
to whatever provider is active.

## The FIVE sites (2026-08-26, hermes-agent working tree)

| # | File | Location | Source of routing dict | Provider in scope |
|---|------|----------|------------------------|-------------------|
| 1 | `gateway/run.py` | main session agent, ~L5769 | `pr = self._runner._provider_routing` (~L5417) | `turn_route["runtime"]["provider"]` |
| 2 | `gateway/run.py` | background-task `run_sync()` agent, ~L22726 | same `pr` | `turn_route["runtime"]["provider"]` |
| 3 | `cron/scheduler.py` | `agent = AIAgent(...)`, ~L6024 | `pr = _cfg.get("provider_routing") or {}` (~L5689) | `runtime.get("provider")` |
| 4 | `tui_gateway/server.py` | desktop/TUI Electron app, ~L7227 | `_pr = _load_provider_routing()` (~L7196) | `runtime.get("provider")` |
| 5 | `hermes_cli/cli_agent_setup_mixin.py` | interactive CLI, ~L514 | `self._providers_only` etc. (set at init from `CLI_CONFIG["provider_routing"]`) | `runtime.get("provider")` |
| 6 | `hermes_cli/cli_commands_mixin.py` | CLI background tasks, ~L2238 | same `self._*` attrs | `(turn_route.get("runtime") or {}).get("provider")` |

Enumerate before editing — do not trust these line numbers after an upgrade:

```
search_files pattern="providers_allowed=" path=~/.hermes/hermes-agent output_mode=content
```

The forwarded kwargs are: `providers_allowed`, `providers_ignored`, `providers_order`,
`provider_sort`, `provider_require_parameters`, `provider_data_collection`. Note the cron
site forwards only the first four.

## Fix — gate on the runtime provider

`gateway/run.py`, module level (placed after `_hygiene_cooldown_for_failure`):

```python
def _provider_routing_applies(turn_route) -> bool:
    """Whether OpenRouter-style provider routing should be attached to a request.

    ``provider_routing`` (order/ignore/only/sort/require_parameters/data_collection)
    is an OpenRouter-specific feature. Non-OpenRouter inference endpoints like the
    Nous portal reject caller-supplied routing fields outright (HTTP 400), because
    routing there is decided centrally per model. So only forward routing to
    OpenRouter; all other providers get plain requests.
    """
    try:
        return (turn_route.get("runtime") or {}).get("provider") == "openrouter"
    except Exception:
        return False
```

Then at both gateway sites:

```python
providers_allowed=(pr.get("only") if _provider_routing_applies(turn_route) else None),
providers_ignored=(pr.get("ignore") if _provider_routing_applies(turn_route) else None),
providers_order=(pr.get("order") if _provider_routing_applies(turn_route) else None),
provider_sort=(pr.get("sort") if _provider_routing_applies(turn_route) else None),
provider_require_parameters=(pr.get("require_parameters", False) if _provider_routing_applies(turn_route) else False),
provider_data_collection=(pr.get("data_collection") if _provider_routing_applies(turn_route) else None),
```

`cron/scheduler.py` — hoist one gate immediately above `agent = AIAgent(` so the call sites
stay short (an empty dict keeps every `.get()` valid):

```python
# OpenRouter-only provider routing. Endpoints like the Nous portal reject
# caller-supplied `provider` routing fields with HTTP 400 (routing is decided
# centrally per model), which previously failed every cron run on a Nous model.
_pr_ok = (runtime.get("provider") if isinstance(runtime, dict) else None) == "openrouter"
_pr = pr if (_pr_ok and isinstance(pr, dict)) else {}
```

```python
providers_allowed=_pr.get("only"),
providers_ignored=_pr.get("ignore"),
providers_order=_pr.get("order"),
provider_sort=_pr.get("sort"),
```

`tui_gateway/server.py` — same hoist pattern, placed right after `_pr = _load_provider_routing()`:

```python
# OpenRouter-only: other endpoints (e.g. the Nous portal) reject caller-supplied
# `provider` routing fields with HTTP 400 since routing is decided centrally.
if (runtime.get("provider") if isinstance(runtime, dict) else None) != "openrouter":
    _pr = {}
```

`hermes_cli/cli_agent_setup_mixin.py` and `hermes_cli/cli_commands_mixin.py` — gate each kwarg inline (these use `self._*` attributes set at init, so the gate goes at the call site):

```python
providers_allowed=(self._providers_only if runtime.get("provider") == "openrouter" else None),
providers_ignored=(self._providers_ignore if runtime.get("provider") == "openrouter" else None),
providers_order=(self._providers_order if runtime.get("provider") == "openrouter" else None),
provider_sort=(self._provider_sort if runtime.get("provider") == "openrouter" else None),
provider_require_parameters=(self._provider_require_params if runtime.get("provider") == "openrouter" else False),
provider_data_collection=(self._provider_data_collection if runtime.get("provider") == "openrouter" else None),
```

For `cli_commands_mixin.py`, use `(turn_route.get("runtime") or {}).get("provider")` instead of `runtime.get("provider")`.

## Verification

```bash
python3 -c "import ast; ast.parse(open('gateway/run.py').read()); print('OK')"
python3 -c "import ast; ast.parse(open('cron/scheduler.py').read()); print('OK')"
python3 -c "import ast; ast.parse(open('tui_gateway/server.py').read()); print('OK')"
python3 -c "import ast; ast.parse(open('hermes_cli/cli_agent_setup_mixin.py').read()); print('OK')"
python3 -c "import ast; ast.parse(open('hermes_cli/cli_commands_mixin.py').read()); print('OK')"
git diff --stat gateway/run.py cron/scheduler.py tui_gateway/server.py hermes_cli/cli_agent_setup_mixin.py hermes_cli/cli_commands_mixin.py
```

Then user runs `/restart` (never `hermes gateway restart` in-session — self-blocks) and:

- interactive: `grep -E "API call #.*provider=nous" ~/.hermes/logs/agent.log | tail -2`
- cron: `cronjob action=run job_id=<previously-failing-id>`, then tail
  `~/.hermes/cron/output/<id>/<ts>.md` and confirm no `## Error` block

A reusable verification script exists at `scripts/verify_routing_gate.py` — it imports the
real `_provider_routing_applies` function and asserts both halves of the gate.

## Pitfalls

- **Do NOT "fix" this by deleting `provider_routing` from config.yaml.** That silently
  removes the fp4-avoidance ordering (morph/bf16 first, fp4 providers ignored) and glitchy
  quantized output returns on OpenRouter models. The whole point of the gate is keeping
  both behaviours.
- **Pyright will complain** at the gated sites: `reportArgumentType`, "None is not
  assignable to List[str]". Pre-existing — the original `pr.get("only")` returned `None`
  on a missing key too, which was the normal case. Not a regression; ship it.
- Cron failures hide the real error at the **END** of the output markdown file. `last_status`
  alone just says `error`; `tail` the file for the `## Error` block.
- All-unpinned jobs (`model: null`) do NOT need per-job edits — `hermes config set cron.model`
  plus `cron.model_provider` covers them all at once.
