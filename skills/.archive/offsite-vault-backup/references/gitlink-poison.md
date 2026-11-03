# gitlink poison — nested repos silently excluded from the vault

**Symptom (hit live 2026-08-17):** the vault sync reported OK, but a directory
that was itself a git repository (`daemon-work/sunburst-sanctuary`) was pushed
as a GITLINK (tree mode `160000`) instead of its contents. The files never
reached the vault — only a pointer to a submodule-ish commit. A "successful"
backup that doesn't contain the money folder.

## Why
`rsync -a` copies `.git/` directories. When the destination tree is committed
to git, a nested repo inside the worktree is recorded as an embedded-repository
gitlink — git's way of saying "this is a submodule reference", which the vault
did not set up. The contents are NOT traversed.

## Detect
```bash
git ls-files -s daemon/          # 160000 f0d1a78...  daemon/sunburst-sanctuary  ← BAD
git ls-files -s | grep 160000    # any hit = ghost entry, contents not in vault
```

## Fix
1. Add `--exclude='.git'` to the rsync that copies the nested-repo tree.
2. In the persistent vault checkout: `git rm --cached daemon/sunburst-sanctuary`
3. Re-run the sync. Verify afterwards: `git ls-files -s | grep 160000` → empty.

## Prevent
- Every rsync into the vault worktree should exclude `.git`:
  `rsync -a --exclude='.git' src/ dest/`
- After every sync: grep for `160000` as part of the Verification step.
