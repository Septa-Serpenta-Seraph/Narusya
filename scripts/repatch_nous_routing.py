#!/usr/bin/env python3
"""
re-patch nous provider routing (OpenRouter-only).

Hermes updates revert our guard that stops the `provider` routing object
(only/ignore/order/sort/data_collection/zdr/require_parameters) from being
sent to the Nous endpoint, which returns HTTP 400.

Re-apply both patches idempotently. Safe to run repeatedly (no-op if already
applied). Run from the hermes-agent repo root, or pass the repo path:

    python3 ~/.hermes/scripts/repatch_nous_routing.py [/path/to/hermes-agent]

After patching, restart the gateway from OUTSIDE the gateway process:
    hermes gateway restart
    # or: systemctl --user restart hermes-gateway
"""
import os
import sys

REPO = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    "~/.hermes/hermes-agent"
)
os.chdir(REPO)

HELPER = os.path.join(REPO, "agent/chat_completion_helpers.py")
NOUS = os.path.join(REPO, "plugins/model-providers/nous/__init__.py")

# --- Patch 1: helper returns {} for Nous --------------------------------
HELPER_OLD = '''def _provider_preferences_for_agent(agent) -> Dict[str, Any]:
    """Build the validated provider-routing object shared by request paths."""
    preferences: Dict[str, Any] = {}'''

HELPER_NEW = '''def _provider_preferences_for_agent(agent) -> Dict[str, Any]:
    """Build the validated provider-routing object shared by request paths."""
    # OpenRouter-only. The Nous endpoint centrally decides routing and returns
    # HTTP 400 if we send `only`/`ignore`/`order`/`data_collection`/`zdr`/
    # `require_parameters`/`sort`. Never emit a `provider` object for Nous.
    if getattr(agent, "provider", None) in {"nous", "nous-portal", "nousresearch"}:
        return {}
    preferences: Dict[str, Any] = {}'''

# --- Patch 2: Nous profile never emits provider object -------------------
NOUS_OLD = '''        provider_preferences = context.get("provider_preferences")
        if provider_preferences:
            body["provider"] = provider_preferences
        return body'''

NOUS_NEW = '''        provider_preferences = context.get("provider_preferences")
        # Nous centrally decides routing; sending a `provider` object returns
        # HTTP 400. Never emit provider routing here (OpenRouter-only feature).
        # Ignore any passed preferences defensively.
        return body'''


def apply(path, old, new, label):
    with open(path) as fh:
        src = fh.read()
    if new in src:
        print(f"[ok] {label}: already applied, skipping")
        return True
    if old not in src:
        print(f"[!!] {label}: anchor NOT FOUND (patch target changed). "
              f"Manual review needed.")
        return False
    src = src.replace(old, new, 1)
    with open(path, "w") as fh:
        fh.write(src)
    print(f"[+] {label}: applied")
    return True


def main() -> bool:
    if not os.path.isdir(REPO):
        print(f"[!!] repo not found: {REPO}")
        return False
    ok1 = apply(HELPER, HELPER_OLD, HELPER_NEW, "helper _provider_preferences_for_agent")
    ok2 = apply(NOUS, NOUS_OLD, NOUS_NEW, "nous profile build_extra_body")
    # syntax check
    try:
        import ast
        for f in (HELPER, NOUS):
            ast.parse(open(f).read())
        print("[ok] syntax check passed")
    except SyntaxError as e:
        print(f"[!!] syntax error after patch: {e}")
        return False
    print("\nPatches OK. Restart gateway from OUTSIDE the gateway process:")
    print("    hermes gateway restart")
    return ok1 and ok2


if __name__ == "__main__":
    sys.exit(0 if main() else 1)