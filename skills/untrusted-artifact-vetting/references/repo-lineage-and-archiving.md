# Repo lineage verification and takedown archiving

Use when Adora wants a copy of a public repo preserved before it disappears, or wants the genuine upstream version distinguished from its forks and rebrands. Posture is identical to the parent skill: download bytes only, never build, install, or execute.

## Procedure

1. **Get identifying facts from authoritative write-ups first.** Threat advisories, vendor blogs, and research posts usually name the original developer handle, the exact version, the commit ID, and the takedown date. GitHub search alone will not surface these. Record the upstream owner/repo, version, and commit SHA before searching mirrors.
2. **Confirm the original's status** with `GET https://api.github.com/repos/<owner>/<repo>`. A 404 confirms it was removed; note `archived`/`disabled` if still present.
3. **Find mirror candidates** via `GET /api.github.com/search/repositories?q=<name>+in:name`, the GitHub topic page, and web search for `<tool> mirror archive original source`. Rank by stars/forks and by descriptions that claim to preserve original history.
4. **Verify lineage by commit object, not by description.** In each candidate clone run `git cat-file -t <original-sha>`; if present, follow with `git show -s --format='%H %an %aI %s' <original-sha>` to confirm author and message. A mirror whose README claims it is "unmodified" may not contain the original commit at all; another may contain it plus a local patch on HEAD.
5. **Export the exact upstream tree at that commit**, not the mirror's HEAD:
   ```bash
   git archive --format=tar.gz --prefix=<clean-name>/ -o <out>.tar.gz <original-sha>
   sha256sum <out>.tar.gz
   tar tzf <out>.tar.gz | wc -l
   ```
   This excludes `.git` and any post-takedown patches, giving the genuine pre-takedown source.
6. **Report with an epistemic boundary.** Give the archive path, full commit ID, sha256, and file count. State explicitly that nothing was built, installed, or executed, and that provenance was verified by commit object rather than by mirror claims.

## Pitfalls

- **Never trust a mirror's self-description of "unmodified" or "original."** Verify the original commit object exists in that clone; provenance asserted in a README is a claim, not evidence.
- **Export at the original commit, not at mirror HEAD.** HEAD commonly carries localization, self-updater URL changes, or other patches that change the artifact's identity even when the original history is present.
- **A repo being rebranded does not make it a different tool.** When file layout and language match the advisories, say the lineage is the same family but keep the identity claim narrow unless verified by commit.
- **Downloading is the whole task.** Do not run `build.sh` or `install.sh` from the archived tool to inspect it; read bytes and archive.
