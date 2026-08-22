# Nous Portal auth-health check (verified 2026-08-21)

Scenario: user says "wanna try another model? It's free on nous." Before
attempting a provider switch, diagnose auth state — do NOT trust claims either
way.

## The three-layer check

1. `hermes auth status nous`
   - `nous: logged out (No access token found for Nous Portal login.)` → no
     token in memory at all.
2. Inspect `~/.hermes/auth.json` → `providers.nous` (redact secrets — print key
   names + value shapes only):
   - If `last_auth_error` = `{code: invalid_grant, relogin_required: True}` →
     stored OAuth token has EXPIRED. The portal is not down; the credential is.
3. Direct probe `https://inference-api.nousresearch.com/v1/models` with no /
   empty bearer → HTTP 403 is EXPECTED without a valid token. A 403 proves
   nothing about portal availability; it proves nothing to conclude.

Also check `~/.hermes/.env` for the `NOUS_API_KEY` line: an `=` with no value
(key present, empty) is a common silent state — grep shows the key exists while
the value is blank.

## Findings on this box (2026-08-21)

- `.env` line 26: `NOUS_API_KEY=` — EMPTY.
- `auth.json`: `active_provider: nous`; `providers: [nous]`;
  `providers.nous.last_auth_error` = `{provider: nous, code: invalid_grant,
  reason: runtime_access_refresh_failure, relogin_required: True}`.
- `hermes auth status nous` → logged out.
- Probe with no bearer → HTTP 403 Forbidden (expected).

## Recovery

```bash
hermes auth add nous        # device/OAuth flow — likely needs a human click/link
hermes auth status nous     # verify token present afterwards
```

`hermes model --no-browser` also exists for headless login flows (scroll the
client-id/scope flags).

## Lesson

- "It's free on nous" → verify credentials; if expired, propose the re-login
  flow as the path, not a shrug.
- An empty `.env` key + dead `auth.json` entry coexist; check BOTH.
- 403 unauthenticated probes are a control, not a diagnosis.