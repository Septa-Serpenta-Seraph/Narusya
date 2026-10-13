# Privacy Scrub Checklist

Regex patterns + file-type rules for auditing a personal codebase before public
release. Run these against **every** text file in the sanitized copy (skip
binary assets, `.min.js`, `.png`/`.svg` blobs, and the `.git` dir). Flag hits,
then either fix or confirm they are benign before pushing.

## Latent-identifier regexes (these catch what a name-grep misses)

| What | Pattern (Python `re`) |
|---|---|
| Phone (US) | `\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b` |
| Private / Tailnet IP | `\b(?:100\.\|10\.\|172\.(?:1[6-9]\|2\d\|3[01])\.\|192\.168\.)\d{1,3}\.\d{1,3}\b` |
| Public IP | `\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b` |
| Email | `[\w.+-]+@[\w-]+\.[\w.]+` |
| EIN / tax ID | `\b\d{2}-\d{7}\b` |
| SSN-style | `\b\d{3}-\d{2}-\d{4}\b` |
| Street address | `\b\d+\s+[A-Z][A-Za-z]+(?:\s+[A-Za-z]+)*\s+(?:St\|Street\|Rd\|Road\|Ave\|Avenue\|Blvd\|Dr\|Drive\|Ln\|Lane\|Ct\|Court\|Pl)\b` |
| Dead-name / real name | search the full legal + former name |
| Internal tooling | `\.hermes\|hermes-agent\|/tmp/\|\.hermes/` |

## Benign hits to NOT false-alarm on
- `0.0.0.0` — standard bind address in server code (fine).
- `127.0.0.1`, `localhost` — dev URL examples in README (fine).
- `.hermes` appearing as an **ignore pattern** in `.gitignore` — that is the
  protective guard (good), not a leak.
- Base64 image blobs inside `.svg`/`.html` — stock art, not text; check only
  that they contain no recognizable labels.
- `ME/CFS` mentioned as the *project's* purpose in README = fine; on a
  personal character card = scrub to neutral ("LV 1 · FIGHTER").

## Also verify
- `git ls-files` in a fresh repo — confirm NO personal data files are tracked
  (`imports/`, `*quicklog*`, `water.json`, `quests.json`, `.hermes/`).
- Structure cross-reference: `git ls-files | sort` in private vs public, then
  `diff -u` each shared file and confirm every delta is an intended scrub edit
  (no accidental structural loss).
- Rename the **constant/variable**, not just the path string (`ADORA_LOG` →
  `USER_LOG`), so a later grep for the old name stays clean.

## Reference workflow used successfully (PIPNARU → CoilPip, 2026-08)
`rsync` a fresh copy excluding `.git`/`imports` → targeted patches for
brand/paths/variables/quests → delete `.hermes/` + personal `options.md` →
write `.gitignore` → regex audit → `git ls-files` + `diff -u` cross-ref →
temp-dir test harness (24 checks) → stdlib logging + PEP 8 + docstrings →
README (run/test/logging/contributing/roadmap) → `gh repo create --public` on
a separate remote → verify visibility PUBLIC and file list.
