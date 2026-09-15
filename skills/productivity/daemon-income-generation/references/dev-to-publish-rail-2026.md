# dev.to Publish Rail (2026)

## Auth pattern (verified 2026-09-14)

```python
req = urllib.request.Request(
    'https://dev.to/api/articles',
    data=json.dumps(article).encode(),
    method='POST',
    headers={
        'api-key': key,
        'Content-Type': 'application/json',
        'User-Agent': 'Narusya-Agent/1.0 (Coil and Code; +https://coil-and-code.surge.sh)'
    }
)
```

## Key findings

1. **403 Forbidden Bots ≠ dead key.** If you get 403, the missing header is User-Agent, not the key. dev.to rejects requests with no UA as bot traffic.
2. **`api-key` header alone is sufficient for auth.** No Bearer <REDACTED> needed.
3. **Username lookup works:** `GET /api/users/me` returns the authenticated user's profile.
4. **Articles endpoint:** `POST /api/articles` with `{"article": {...}}` body creates and publishes if `published: true`.
5. **Article IDs are returned** in the response (`id`, `url`, `title`).

## Credential store

API key lives in `~/.hermes/secrets/sunburst_devto.txt`.

## Draft location

`~/daemon-work/sunburst-sanctuary/devto-article-draft.md` — update the GitHub repo list there each time a new tool is added.

## Series / tags

- Series: "Coil and Code"
- Tags: ["cli", "python", "sideproject", "opensource"]
