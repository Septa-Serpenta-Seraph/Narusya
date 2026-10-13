# Public-repo leak response — org sweep + git-filter-repo scrub (2026-08-22)

Case study: the storefront `coil-and-code` public repo contained the whole business
folder (EIN, legal name, internal prep docs), and the `Narusya` persona repo — a
nightly auto-backup target — carried `config.yaml` (internal Tailnet IP
`100.116.86.38:6969`) plus SSI case / medical-background / physician-letter files
under `skills/welfare/...`. All were removed from working tree AND history; the
Narusya repo was restored to public per Adora's standing architecture (sensitive →
vault only, public repos stay public with clean trees).

## 1. Org-wide sweep (find the leaks)

```bash
# Every repo + visibility
gh repo list <org> --limit 50 --json name,visibility --jq '.[] | "\(.name): \(.visibility)"'

# For each public repo: fetch every text file raw and grep for hard PII.
for repo in <repos...>; do
  files=$(gh api "repos/<org>/$repo/git/trees/HEAD?recursive=1" --jq '.tree[].path' \
          | grep -E '\.(py|md|txt|json|yaml|yml|sh|conf|cfg|toml)$' | head -100)
  for f in $files; do
    curl -s "https://raw.githubusercontent.com/<org>/$repo/HEAD/$f" \
      | grep -ilE '42-4517237|03729639006|daniel p|adora|505-490|505-644|10 lucero|sunburstsanctuarynm@gmail.com|100\.11[0-9]\.' \
      && echo "  ^^ $f"
  done
done
```

Triage hits: **hard PII** = EIN/tax IDs, phones, street address, dead-name, gmail,
Tailnet IPs (100.x) → must scrub. **Soft** = first name in project credit prose
("Built by Adora & Narusya", "Reported by Adora") → public-by-design, leave alone.
The raw.githubusercontent grep will also match `lorebooks/*.md` full of "Adora" —
that's the persona content, not a leak; always open the hit to see WHAT matched.

## 2. History rewrite with git-filter-repo

```bash
# Standalone install (pip --user FAILS inside Hermes venv)
curl -sL -o /tmp/git-filter-repo https://raw.githubusercontent.com/newren/git-filter-repo/main/git-filter-repo
chmod +x /tmp/git-filter-repo

# Fresh clone — NEVER the live backup repo the cron pushes from
git clone git@github.com:<org>/<repo>.git /tmp/<repo>-scrub && cd /tmp/<repo>-scrub

# Dry run first
/tmp/git-filter-repo --dry-run --invert-paths \
  --path config.yaml \
  --path skills/welfare/disability-benefit-advocacy/references/adora-ssi-case.md \
  --path skills/welfare/disability-benefit-advocacy/references/physician-functional-letter.md \
  --path skills/welfare/mutual-health-logging-daemon-human/references/adora_medical_background.md

# Real strip (removes origin remote by design — re-add before push)
/tmp/git-filter-repo --invert-paths --path config.yaml --path <...>

# Verify by OBJECT (empty = gone):
git rev-list --all --objects | grep -c 'adora_medical_background\|adora-ssi-case\|physician-functional' || echo "0 traces"
git rev-list --all --objects | grep '/config\.yaml$'   # nothing = clean

# Re-add origin + force-push
git remote add origin git@github.com:<org>/<repo>.git
git push -f origin HEAD:main
```

PITFALL: `git log --oneline -- config.yaml` matches `abliteration-config.yaml`
(path-prefix matching) — looks like the file is still there when it isn't. The
`git rev-list --all --objects | grep '/config\.yaml$'` exact check is the truth.

## 3. Reset the pushing side (stop the re-leak)

The `Narusya` leak came from `~/.hermes/backup-repo` (SSH remote to the public
GitHub repo), updated nightly at 02:00 by `backup.sh` which rsyncs live
`~/.hermes/skills/`, `lorebooks/`, `config.yaml` into the repo. After the force-push:

```bash
git -C ~/.hermes/backup-repo fetch origin
git -C ~/.hermes/backup-repo reset --hard origin/main
# confirm the sensitive files are no longer tracked:
git -C ~/.hermes/backup-repo ls-files | grep -c 'config.yaml'  # only the benign template remains
```

## 4. Restore visibility + report

`gh repo edit <org>/<repo> --visibility public --accept-visibility-change-consequences`
only after tree + history verified clean. Tell the user the visibility changed and
why — they own the public/private decision, not the daemon.

## Leak classes seen (add to any future sweep)
- Business folder pushed wholesale into a public "products" repo (EIN, dead-name,
  NM tax prep, operating agreement draft).
- Persona/backup repo auto-pushing live `skills/` (welfare/medical refs), `lorebooks/`,
  and `config.yaml` with internal Tailnet IPs.
- Node_modules dirs in git (huge, and crypto filenames like `ripemd160.js` false-alarm
  on health-ish greps — benign).
