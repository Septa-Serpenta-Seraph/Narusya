# PixAI signup via camofox REST server — worked flow (2026-08-25)

Fully autonomous account creation on pixai.art, no email verification step required,
no captcha encountered through Camoufox. Total time ~90 seconds.

## Preconditions
- camofox server healthy: `curl localhost:9377/health` → `{"ok":true,...}`
- Readable inbox available (himalaya) in case verification IS demanded later
- Secrets dir writable: `~/.hermes/secrets/`

## Flow
1. **Open tab** (userId isolates cookie jar; sessionKey groups the task):
   ```
   POST /tabs  {"userId":"narusya","sessionKey":"<task-key>","url":"https://pixai.art/login?mode=register"}
   → {"tabId":"...","url":"..."}     # note: /register redirects to /en/404 — use /login?mode=register
   ```
2. **Snapshot**: `GET /tabs/:id/snapshot?userId=..&sessionKey=..`
   Landing page shows OAuth buttons (Google/Discord/Twitter/Apple) + "Continue with Email" [e6].
3. **Click Continue with Email** by ref. Refs RESET after any navigation — re-snapshot.
4. Form appears: textbox Email [e3], Password [e4], Continue [e7].
5. **Generate password** (`secrets.choice`, 16 chars), TYPE into e3/e4.
6. **Store creds 0600 BEFORE submitting**: `~/.hermes/secrets/pixai_account.txt`.
7. **Click Continue** → next snapshot shows logged-in app shell:
   banner with Top-up / Bonus Credits / credits-count buttons = success signal.
8. A welcome dialog ("Daily Reward", Receive button) may cover the page — Dismiss [e1].
9. Poll himalaya inbox for any verification mail; as of 2026-08-25 none was sent and
   the account is fully active without it.

## Gotchas
- `/register` URL 404s inside their SPA; `/login?mode=register` is the working entry.
- POST bodies want userId+sessionKey; GET endpoints take them as query params.
- The daily-reward "Receive" button may be disabled until a timer elapses; check-in
  quests live under the "Bonus" button (Banner → Bonus → Check in).
- Account starts at 0 credits; dailies (~10k/day + new-user bonus track) fund LoRA training.

## Next steps for LoRA work
Studio/LoRA-training upload expects images (+optional captions). Dataset prepared at
`~/.hermes/imagegen/dataset/` and zipped at `~/.hermes/imagegen/narusa-lora-dataset.zip`;
trigger word `narusa`; base SDXL recommended.
