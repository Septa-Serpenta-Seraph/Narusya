"""Verify the OpenRouter-only provider-routing gate behaves correctly."""
import sys
sys.path.insert(0, '/home/adora/.hermes/hermes-agent')

from gateway.run import _provider_routing_applies

PR = {"order": ["morph"], "ignore": ["openinference"],
      "require_parameters": True, "data_collection": "deny"}

cases = [
    ("openrouter", True,  "OpenRouter must KEEP routing (fp4 protection)"),
    ("nous",       False, "Nous must DROP routing (rejects it, HTTP 400)"),
    ("openai",     False, "other providers drop routing"),
    (None,         False, "missing provider drops routing"),
]

fails = 0
for provider, expected, why in cases:
    route = {"model": "m", "runtime": {"provider": provider}}
    got = _provider_routing_applies(route)
    ok = (got == expected)
    fails += (not ok)
    print(f"{'PASS' if ok else 'FAIL'}  provider={str(provider):11s} applies={got!s:5s}  {why}")

# malformed inputs must not raise
for bad in [{}, {"runtime": None}, {"runtime": "nonsense"}]:
    try:
        r = _provider_routing_applies(bad)
        print(f"PASS  malformed {str(bad)[:22]:24s} -> {r} (no crash)")
    except Exception as e:
        fails += 1
        print(f"FAIL  malformed {bad} raised {e!r}")

# simulate what actually reaches the API body
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
