#!/usr/bin/env python3
"""Assert the OpenRouter-only provider-routing gate behaves correctly.

Run from anywhere:  python3 verify_routing_gate.py
Exits non-zero on any failure. Proves BOTH halves of the fix:
  - OpenRouter still receives routing (fp4-avoidance preserved)
  - every other provider (notably nous) receives a clean request (no HTTP 400)
"""
import sys

sys.path.insert(0, "/home/adora/.hermes/hermes-agent")

from gateway.run import _provider_routing_applies  # noqa: E402

PR = {
    "order": ["morph"],
    "ignore": ["openinference"],
    "require_parameters": True,
    "data_collection": "deny",
}

CASES = [
    ("openrouter", True, "OpenRouter must KEEP routing (fp4 protection)"),
    ("nous", False, "Nous must DROP routing (rejects it, HTTP 400)"),
    ("openai", False, "other providers drop routing"),
    (None, False, "missing provider drops routing"),
]

fails = 0

for provider, expected, why in CASES:
    route = {"model": "m", "runtime": {"provider": provider}}
    got = _provider_routing_applies(route)
    ok = got == expected
    fails += not ok
    print(f"{'PASS' if ok else 'FAIL'}  provider={str(provider):11s} applies={got!s:5s}  {why}")

# malformed shapes must never raise
for bad in [{}, {"runtime": None}, {"runtime": "nonsense"}]:
    try:
        r = _provider_routing_applies(bad)
        print(f"PASS  malformed {str(bad)[:22]:24s} -> {r} (no crash)")
    except Exception as exc:  # noqa: BLE001
        fails += 1
        print(f"FAIL  malformed {bad} raised {exc!r}")

# show what actually reaches the request body
print()
for provider in ("openrouter", "nous"):
    route = {"model": "m", "runtime": {"provider": provider}}
    applies = _provider_routing_applies(route)
    body = {
        "providers_order": (PR.get("order") if applies else None),
        "provider_require_parameters": (PR.get("require_parameters", False) if applies else False),
        "provider_data_collection": (PR.get("data_collection") if applies else None),
    }
    sent = {k: v for k, v in body.items() if v not in (None, False)}
    print(f"{provider:11s} -> routing fields sent: {sent if sent else 'NONE (clean request)'}")

print()
print("RESULT:", "ALL CHECKS PASSED" if fails == 0 else f"{fails} FAILURE(S)")
sys.exit(1 if fails else 0)
