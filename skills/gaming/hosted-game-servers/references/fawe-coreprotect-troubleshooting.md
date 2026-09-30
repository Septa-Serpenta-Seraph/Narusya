# FAWE × CoreProtect: diagnosis & config fixes

Worked example 2026-09-26 (SFCA, Paper 26.2, FAWE 2.15.4, CoreProtect-CE 24.1).

## Symptom
During WorldEdit use (`//set`, etc.) an error/warning mentioning
`net.coreprotect.worldedit.CoreProtectLogger` (or FAWE 'Extent ... must be
AbstractDelegateExtent' wording on older pairs). Edits still work — this is
noise, not breakage.

## Diagnosis chain
1. **latest.log only holds boot-time lines by the time you look.** In-game
   FAWE warnings from a `//set` run live in the log that was current when the
   command ran — older sessions are rotated to `/logs/YYYY-MM-DD-N.log.gz`.
2. Rotated logs: GET `/files/download?file_path=<urlencoded /logs/<name>.gz>`
   → `attributes.url` signed URL → fetch with a browser User-Agent →
   `gzip.decompress()` in Python. Then grep for `/ERROR`, `/WARN`,
   `Exception`, `at net.coreprotect`, `Caused by`, and `issued server command`
   lines (the `//` commands) to correlate error timing with user actions.
3. Confirm the integration is healthy first: boot log should show
   `[CoreProtect] FastAsyncWorldEdit logging successfully initialized.`
   If present, the hook works and the error is a config/debug complaint.
4. CoreProtect CE 24.1 integrates FAWE **natively** (no BlocksHub needed —
   BlocksHub died at 1.13). Its `CoreProtectLogger extends AbstractDelegateExtent`
   (checked the CE source on GitHub) — the hook shape is correct.

## Root cause of the noise
FAWE `/plugins/FastAsyncWorldEdit/config.yml` ships `extent.debug: true` —
it warns on console whenever a third-party extent (CoreProtect's logger)
wraps a FAWE edit. Purely cosmetic.

## Fix
Edit the FAWE config via the panel file API (raw text body, verify read-back),
then restart:
```yaml
extent:
  # Should debug messages be sent when third party extents are used?
  debug: false
```
- POST `/servers/{id}/files/write?file=<urlencoded path>` → 204; read the file back to
  verify before restarting. **Body form (updated 2026-09-29):** plain raw text now returns
  403 Forbidden on PebbleHost — use the JSON envelope `Content-Type: application/json`,
  body `{"raw": "<full file text>"}`. FAWE configs can also be applied without restart:
  `fawe reload` via console (`Configuration reloaded!` in latest.log) — prefer that over a
  restart for config-only changes.
- After restart: check `Done (Xs)!` and confirm the only remaining error is
  Essentials' benign 'unsupported server version' grumble.

## Do NOT instead-disable the hook
Turning `worldedit: false` in CoreProtect's config.yml silences the noise too
but silently stops rollback logging of all WorldEdit edits — the entire point
of running CP alongside FAWE. Fix FAWE's debug flag instead.

## Version note
FAWE 2.15.4 (Aug 2026) is the newest build supporting 26.2 on Modrinth;
CoreProtect-CE 24.1 added 26.2 support + fixed 'missing hopper logs during
WorldEdit changes'. If errors persist on these versions, next step is a
newer CP/FAWE release, not config surgery.
