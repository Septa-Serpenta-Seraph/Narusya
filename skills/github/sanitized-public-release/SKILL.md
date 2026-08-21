---
name: sanitized-public-release
description: Publish a privacy-clean public repo from a private codebase.
---

# Sanitized Public Release

Turning a private/personal project (health data, personal logs, identity) into an open-source public repo that is shareable **as-is** without leaking anything private. Used for Adora's personal projects (PIPNARU → public "CoilPip", storefront, tools shared with Tyler/Vesper/community).

**Non-negotiable rule:** a public repo is permanent and crawled by bots/humans. Personal/health data pushed there is *gone*. Never reuse private git history; build a fresh sanitized artifact.

## Workflow

1. **Make a fresh copy, not a branch.** `rsync -a --exclude='.git' --exclude='__pycache__' --exclude='imports' <private>/ <public>/`. Never branch the private repo — its history contains the real data.
2. **Scrub personal identifiers** (grep the copy, replace in place):
   - Brand/persona names → neutral (e.g. `NARUSYA`→`COILPIP`, `ADORA`→`OPERATOR`)
   - Real username labels on UI screens
   - Personal file paths / variable names (`ADORA_LOG`→`USER_LOG`)
   - Business/legal identifiers (EINs, tax IDs, account numbers) in quests/data
   - Health diagnosis strings on UI ("ME/CFS" on a character card → neutral "LV 1 · FIGHTER")
   - Dead-name / name mappings — MUST be removed, map records with dignity
3. **Delete internal files** the copy dragged in: `.hermes/`, internal plans, personal `options.md` (replace with a neutral structure note).
4. **Deep audit sweep** — run a regex pass for *latent* identifiers a grep for names misses (see `references/scrub-checklist.md`): phone numbers, private/Tailnet IPs, emails, EIN/SSN patterns, dead-name, street addresses, `.hermes`/`/tmp/`.
5. **Structure cross-reference** to prove nothing was lost: `git ls-files` diff private vs public; then `diff -u` each shared file and confirm the *only* changes are the intended scrub edits (no accidental structural damage).
6. **Sanitize data files:** move live user state (`~/health`, `imports/`, `*.json`) OUT of the repo; add a `.gitignore` that guarantees they can never be committed. Never push data off-Tailnet.
7. **Bug-test before public:** a test harness that redirects every data store to a temp dir and exercises all endpoints (never touches the user's real data). Run it; all green.
8. **Code quality before public:** stdlib `logging` (module logger + `basicConfig` at `__main__`, override `log_message` to route request logs), PEP 257 docstrings, `autopep8 --aggressive` + manual fixes, `pycodestyle --max-line-length=120` clean.
9. **Docs:** README with run/test/logging/contributing sections, an explicit "where to submit PRs" block (links to `/pulls` and `/issues`), a golden rule ("never commit personal health data"), and a roadmap.
10. **Push to a *public* repo** on a **separate** remote from the private one. Verify `gh repo view <name> --json visibility` = PUBLIC and the remote file list matches the staged set.

## Pitfalls
- **Port conflict during testing:** a stdlib server hardcodes its port; if the live service already holds it, a test run dies with `Address already in use`. Test via a port arg or by importing the module and overriding paths (see the temp-harness pattern).
- **Variable-name leak:** renaming the path string isn't enough — rename the *constant* too (`ADORA_LOG`→`USER_LOG`) or a future grep for the old name flags it.
- **Mascot/asset naming drift:** if a generator writes `pipgirl.png` but the UI references `coilgirl.png`, regeneration breaks the link. Align generator output name with the deployed asset (`git mv` the script too).
- **autopep8 editing pixel art:** `--aggressive` can reformat coordinate tuples. Re-run the generator after formatting and byte-compare the output PNG to confirm the art is unchanged.
- **`.hermes` in a `.gitignore`** is the protective *pattern* (good), not a leak — don't false-alarm on it during the audit.
- **py_compile gate** before restarting any user service; restarting `pipnaru.service`/similar requires the user's explicit consent (protocol).

## Sync-back
When the public version gains quality (logging, tests, style), sync those improvements **back** to the private source — but preserve the private identity (personal paths, real quests, name). Only the *mechanics* (logging, docstrings, PEP 8, test harness) transfer; scrub edits do not reverse apply.

## Support files
- `references/scrub-checklist.md` — full regex patterns + file types to check for a privacy audit.
