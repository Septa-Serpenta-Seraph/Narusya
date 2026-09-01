#!/usr/bin/env python3
"""
re-patch Nous provider routing (OpenRouter-only) — idempotent.

Hermes upstream refactors regularly move/rename the routing-request builder,
and a `git pull`/update wipes our guard that stops the `provider` routing object
(only/ignore/order/sort/data_collection/zdr/require_parameters) from being sent
to the Nous endpoint, which returns HTTP 400.

Run after any Hermes update that breaks free Nous models:

    python3 ~/.hermes/scripts/repatch_nous_routing.py [/path/to/hermes-agent]

Then restart the gateway from a SEPARATE shell (you cannot restart from inside
the gateway): `hermes gateway restart` — or `systemctl --user restart hermes-gateway`.
"""
import ast
import os
import sys

REPO = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    "~/.hermes/hermes-agent"
)
os.chdir(REPO)

HELPER = os.path.join(REPO, "agent/chat_completion_helpers.py")
NOUS = os.path.join(REPO, "plugins/model-providers/nous/__init__.py")

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
        print(f"[!!] {label}: anchor NOT FOUND — upstream refactored the target. "
              f"Manual review needed (grep for '_provider_preferences_for_agent' "
              f"and 'body[\"provider\"]').")
        return False
    with open(path, "w") as fh:
        fh.write(src.replace(old, new, 1))
    print(f"[+] {label}: applied")
    return True


def main():
    if not os.path.isdir(REPO):
        print(f"[!!] repo not found: {REPO}")
        return False
    ok = True
    ok &= apply(HELPER, HELPER_OLD, HELPER_NEW, "helper _provider_preferences_for_agent")
    ok &= apply(NOUS, NOUS_OLD, NOUS_NEW, "nous profile build_extra_body")
    for f in (HELPER, NOUS):
        try:
            ast.parse(open(f).read())
            print(f"[ok] syntax: {os.path.basename(f)}")
        except SyntaxError as e:
            print(f"[!!] syntax error in {f}: {e}")
            ok = False
    if ok:
        print("\nPatches OK. Restart the gateway from a SEPARATE shell:")
        print("    hermes gateway restart")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
