---
name: github-workflow
description: "Complete GitHub workflow: auth, repo management, PR lifecycle, code review, issues, codebase inspection. Uses gh CLI and/or curl+git REST API."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Git, gh-cli, PR, Issues, Code-Review, Repositories, CI/CD, Authentication]
    related_skills: [hermes-agent]
---

# GitHub Workflow

Complete guide for working with GitHub repositories, PRs, issues, and CI. Covers authentication, repo management, PR lifecycle, code review, issues management, and codebase inspection.

Each section shows the `gh` way first, then the `git` + `curl` fallback for machines without `gh`.

## When to Use

- Setting up GitHub authentication (GitHub auth)
- Creating, cloning, forking repositories (Repo management)
- Opening, reviewing, and merging pull requests (PR workflow)
- Reviewing code quality, security, correctness (Code review)
- Creating, triaging, and managing issues (Issues)
- Analyzing codebase metrics, LOC, language breakdown (Codebase inspection)

---

## 1. GitHub Authentication Setup

### Auth Detection

When a user asks you to work with GitHub, run this check first:

```bash
# Check what's available
git --version
gh --version 2>/dev/null || echo "gh not installed"
gh auth status 2>/dev/null || echo "gh not authenticated"
git config --global credential.helper 2>/dev/null || echo "no git credential helper"
```

**Decision tree:**
1. If `gh auth status` shows authenticated → use `gh` for everything
2. If `gh` is installed but not authenticated → use "gh auth" method below
3. If `gh` is not installed → use "git-only" method

### Method 1: Git-Only Authentication (No gh, No sudo)

#### HTTPS with Personal Access Token (Recommended)

1. Create a personal access token at **https://github.com/settings/tokens**
   - Scopes: `repo`, `workflow`, `read:org` (if org repos)
   - Expiration: 90 days

2. Configure credential helper:
```bash
git config --global credential.helper store
git ls-remote https://github.com/<username>/<any-repo>.git
# Username: <their-github-username>, Password: <token>
```

3. Set git identity:
```bash
git config --global user.name "Their Name"
git config --global user.email "their-email@example.com"
```

#### SSH Key Authentication

```bash
# Generate key if needed
ssh-keygen -t ed25519 -C "their-email@example.com" -f ~/.ssh/id_ed25519 -N ""

# Add public key to GitHub at https://github.com/settings/keys

# Configure git to use SSH for GitHub
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

### Method 2: gh CLI Authentication

#### Device Code Flow (Headless/Terminal Environments)
This is the most reliable method for terminal-only or headless environments where a desktop browser cannot be opened automatically.

```bash
# 1. Start device flow
gh auth login -h github.com

# 2. The CLI will output a one-time code (e.g., C5D9-CACB) and a URL:
#    ! First copy your one-time code: C5D9-CACB
#    Open this URL to continue in your web browser: https://github.com/login/device

# 3. The user visits the URL in their browser, pastes the code, and authorizes.
# 4. The CLI will automatically detect the authorization and complete the setup.
#    (Note: If run in the background, the command may timeout waiting for the user, 
#    but the auth will still succeed once the user completes it in the browser.)

# 5. Verify
gh auth status
```

#### Token-Based Authentication (Recommended for Headless/Hermes)
**This is the most reliable method in headless or remote terminal environments** where interactive browser auth may time out or drop the connection before the callback completes.

```bash
# 1. User generates a Personal Access Token (PAT) at https://github.com/settings/tokens
# 2. Inject via stdin to avoid interactive prompts:
echo "YOUR_PAT_TOKEN" | gh auth login -h github.com --with-token

# 3. Configure Git to use the authenticated account
gh auth setup-git

# 4. Verify
gh auth status
```
*Note: Do not attempt interactive `gh auth login` in the foreground without a generous timeout, as headless terminals often drop the process (exit code 124) before the GitHub callback can write the token to `~/.config/gh/hosts.yml`.*

#### Interactive Browser Login (Desktop)
```bash
gh auth login
```

### Universal Auth Detection Helper

```bash
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  echo "AUTH_METHOD=gh"
elif [ -n "$GITHUB_TOKEN" ]; then
  echo "AUTH_METHOD=curl"
elif [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
  export GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
  echo "AUTH_METHOD=curl"
else
  echo "AUTH_METHOD=none"
fi
```

### Troubleshooting

| Problem | Solution |
|---------|----------|
| `git push` asks for password | Use a personal access token, not your GitHub password |
| `remote: Permission denied` | Token lacks `repo` scope — regenerate |
| `ssh: Connection refused` | Try SSH over HTTPS: add `Port 443` + `Hostname ssh.github.com` to `~/.ssh/config` |

### ⚠️ Fine-Grained PAT Scope Pitfall

GitHub now recommends **fine-grained tokens** over classic tokens. They default to **read-only** permissions unless you explicitly grant write scopes, and the resulting failure mode is insidious:

**Symptoms** (all true at the same time, which is confusing):
- `gh auth status` reports "✓ Logged in as \<user\>"
- `gh api /user` returns 200 with your profile
- `git push` returns 403 `Permission to <user>/<repo>.git denied to <user>`
- `gh api repos/<user>/<repo>/git/trees -X POST ...` returns 403 "Resource not accessible by personal access token"

**Root cause:** The fine-grained token was generated with read-only (or no) permission for **Contents** and/or **Pull requests**. Both must be set to **Read and write** for push + PR operations.

**Fix:**
1. Go to https://github.com/settings/tokens?type=beta
2. Edit the token (or generate a new one)
3. Under **Repository permissions**, set:
   - **Contents** → Read and write
   - **Pull requests** → Read and write
4. Regenerate and re-authenticate:
   ```bash
   echo "NEW_TOKEN" | gh auth login --with-token
   gh auth setup-git
   ```

**Classic tokens** (type=classic) granted `repo` scope get full repo access by default, which is why older docs don't mention this. The fine-grained split is more secure but the read-only default catches people off guard.

### ⚠️ Fork→Upstream PR Fails with a Fork-Admin Token (createPullRequest blocked)

A fine-grained token with **full admin on your OWN fork** (can push, commit,
manage the fork) can STILL fail to open a PR against an **upstream** org repo:

```
gh pr create --repo NousResearch/hermes-agent --head <you>:<branch> --base main ...
pull request create failed: GraphQL: Resource not accessible by personal access token (createPullRequest)
```

**Why:** creating a PR *against the upstream repo* is a write to THAT repo.
Your token needs `Pull requests: Write` permission scoped to the upstream repo
(and the token must be able to see it), not just Contents on your own fork.
Full admin on your fork does NOT imply PR-write on other repos. The push to the
fork succeeds (own Contents write) and the `gh pr create` then fails — confusing
because half the pipeline worked.

**Diagnose:** `gh auth status` shows logged-in; `gh repo view <your>/<fork>`
shows admin; yet `createPullRequest` is refused. The refused mutation is the
GraphQL clue that it's a token-permission gap on the upstream, not a fork problem.

**Fix options (any one):**
1. **Browser "Compare & pull request"** — the pushed fork branch shows a
   "Contribute" banner; no PR token needed to draft it manually. Fastest fix.
2. Grant the token `Pull requests: Write` on the upstream repo, then re-run
   `gh pr create`.
3. Use a separate token that has PR-write on the upstream (classic `repo`, or a
   fine-grained token scoped to that repo).
4. Fallback entirely to the REST API with a properly-scoped token:
   `POST /repos/<upstream>/pulls` with `head: <you>:<branch>`, `base: main`.

**Also:** before opening the PR, search both open PRs and the issue tracker for
the same bug — org maintainers run triage sweepers that auto-close duplicates.
`gh search prs --repo <owner>/<repo> "<symptom>"` and check linked issues
(`gh issue list --search "<symptom>"`).

---

## 2.5. Fork-Based Contribution PRs (Org Repos You Don't Have Push Access To)

When contributing to an upstream org repo (e.g., `NousResearch/hermes-agent`) where you have no write access, you **cannot push directly** and you **cannot push to your fork via git with the token** unless the token has write scope on *your* fork's remote. The reliable workflow is:

### Setup

```bash
# In a clone of the upstream repo
git remote add fork https://github.com/<your-username>/<fork-repo>.git
```

### PR Workflow

1. **Create branch on your fork** (via API if git push isn't working):
   ```bash
   # Preferred: push via git authenticated with gh credential helper
   git push fork <feature-branch>
   
   # Fallback: create branch via GitHub API
   gh api /repos/<your-username>/<fork-repo>/git/refs -X POST \
     -f ref="refs/heads/<feature-branch>" \
     -f sha="$(git rev-parse HEAD)"
   ```

2. **Open PR from your fork to the upstream branch**:
   ```bash
   # gh auto-detects fork → upstream when the head repo differs
   gh pr create \
     --repo NousResearch/hermes-agent \
     --head <your-username>:<feature-branch> \
     --base main \
     --title "fix: resolve xterm.js initial sizing race" \
     --body "## Summary\n<description>"
   ```

3. The PR target is upstream (`NousResearch/hermes-agent`), but the code lives in your fork. Maintainers review and merge from there.

### Key Notes
- `gh auth setup-git` configures git to use gh's credential helper for HTTPS push — without it, git falls back to interactive username/password and fails on headless machines.
- The `<head> <user>:<branch>` syntax on `gh pr create` is required when opening a PR from a fork to ensure GitHub routes the PR to the correct source.
- If `git push fork` keeps failing with 403 after `gh auth setup-git`, the token itself lacks write scope (see pitfall above).

---

## 2. Repository Management

### Cloning

```bash
# HTTPS clone
git clone https://github.com/owner/repo.git

# Shallow clone
git clone --depth 1 https://github.com/owner/repo.git

# gh shorthand
gh repo clone owner/repo
```

### Creating Repositories

```bash
# Public with MIT license
gh repo create my-project --public --license MIT

# Private with description
gh repo create my-project --private --description "A useful tool"

# From local directory
gh repo create my-project --source . --public --push

# Via curl
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user/repos \
  -d '{"name":"my-project","private":false,"auto_init":true,"license_template":"mit"}'
```

### Forking

```bash
gh repo fork owner/repo --clone

# Keep fork in sync
git fetch upstream
git checkout main && git merge upstream/main
git push origin main
```

### Repository Settings

```bash
# View/edit settings
gh repo view owner/repo
gh repo edit --description "Updated" --enable-wiki=false

# Via curl
curl -s -X PATCH \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO \
  -d '{"description":"Updated","has_wiki":false,"allow_auto_merge":true}'
```

### Branch Protection

```bash
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/branches/main/protection \
  -d '{
    "required_status_checks": {"strict": true, "contexts": ["ci/test", "ci/lint"]},
    "enforce_admins": false,
    "required_pull_request_reviews": {"required_approving_review_count": 1}
  }'
```

### Secrets Management

```bash
gh secret set API_KEY --body "value"
gh secret list
```

Via curl requires encryption with repo's public key (see `references/github-api-cheatsheet.md`).

### Releases

```bash
gh release create v1.0.0 --title "v1.0.0" --generate-notes
gh release list
```

### GitHub Actions

```bash
gh workflow list
gh run list --limit 10 --branch main
gh run view <RUN_ID> --log-failed
gh run rerun <RUN_ID> --failed

# Trigger workflow manually
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/workflows/$WORKFLOW_ID/dispatches \
  -d '{"ref": "main"}'
```

### Gists

```bash
gh gist create script.py --public --desc "Useful script"
```

---

## 3. Pull Request Lifecycle

### Branch Creation

```bash
git checkout main && git pull origin main
git checkout -b feat/description
```

Branch naming: `feat/description`, `fix/description`, `refactor/description`, `docs/description`

### Commits

```bash
git add .
git commit -m "feat: add JWT-based authentication

- Add login/register endpoints
- Add JWT token generation"
```

Conventional Commits format: `type(scope): short description`
Types: `feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `chore`, `perf`

### Push and Create PR

```bash
git push -u origin HEAD

# With gh
gh pr create \
  --title "feat: add JWT authentication" \
  --body "## Summary
- Adds login and register API endpoints
- JWT token generation and validation" \
  --draft

# With curl
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d '{"title":"feat: add JWT auth","body":"Summary of changes.","head":"branch","base":"main"}'
```

### Monitor CI

```bash
gh pr checks
gh pr checks --watch  # poll until complete

# With curl
SHA=$(git rev-parse HEAD)
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status
```

### Auto-Fix CI Failures

Loop: check CI → read logs → fix → commit → push → re-check (up to 3 attempts)

```bash
gh run list --branch $(git branch --show-current) --limit 5
gh run view <RUN_ID> --log-failed
```

### Merging

```bash
gh pr merge --squash --delete-branch

# With curl
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/merge \
  -d '{"merge_method":"squash"}'
```

---

## 4. Code Review

### Local Changes (Pre-Push)

```bash
git diff main...HEAD --stat
git diff main...HEAD
git diff main...HEAD --name-only

# Check for common issues
git diff main...HEAD | grep -n "print(\|console\.log\|TODO\|FIXME\|password\|secret"
```

### Review Checklist

- **Correctness**: Edge cases, error paths, null handling
- **Security**: No hardcoded secrets, SQL injection, XSS, path traversal
- **Quality**: Clear naming, DRY, focused functions
- **Testing**: New paths tested, edge cases covered
- **Performance**: No N+1 queries, appropriate caching
- **Documentation**: Public APIs documented, README updated

### Review Output Format

```
## Code Review Summary

### Critical
- **src/auth.py:45** — SQL injection: user input passed directly to query.

### Warnings
- **src/models.py:23** — Password stored in plaintext.

### Suggestions
- **src/utils.py:8** — Duplicates logic in core/utils.py:34.

### Looks Good
- Clean separation of concerns in middleware
```

### PR Review (GitHub)

```bash
# Check out PR locally
git fetch origin pull/123/head:pr-123
git checkout pr-123
git diff main...pr-123

# Post inline review with gh
gh pr review 123 --approve --body "LGTM!"
gh pr review 123 --request-changes --body "See inline comments."

# Post inline review with curl (atomic multi-comment)
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/reviews \
  -d '{"commit_id":"SHA","event":"REQUEST_CHANGES","body":"Review","comments":[{"path":"src/x.py","line":45,"body":"Fix this"}]}'
```

Event values: `APPROVE`, `REQUEST_CHANGES`, `COMMENT`

---

## 5. Issues Management

### Viewing Issues

```bash
gh issue list
gh issue list --state open --label "bug"
gh issue list --search "authentication error" --state all
```

### Creating Issues

```bash
gh issue create \
  --title "Login redirect ignores ?next= parameter" \
  --body "## Description\nAfter logging in, users always land on /dashboard.

## Steps to Reproduce
1. Navigate to /settings while logged out
2. Log in
3. Expected: go to /settings. Actual: /dashboard" \
  --label "bug,backend" \
  --assignee "username"
```

### Managing Issues

```bash
# Labels
gh issue edit 42 --add-label "priority:high,bug"
gh issue edit 42 --remove-label "needs-triage"

# Assign
gh issue edit 42 --add-assignee username

# Comment
gh issue comment 42 --body "Root cause is in auth middleware."

# Close/Reopen
gh issue close 42
gh issue reopen 42
```

### Issue Triage Workflow

1. List untriaged: `gh issue list --label "needs-triage"`
2. Read and categorize each issue
3. Apply labels and priority
4. Assign if owner is clear
5. Comment with triage notes

### Bulk Operations

```bash
# Close all wontfix issues
gh issue list --label "wontfix" --json number --jq '.[].number' | \
  xargs -I {} gh issue close {} --reason "not planned"
```

### Quick Reference

| Action | gh |
|--------|-----|
| List issues | `gh issue list` |
| Create issue | `gh issue create --title "..." --body "..."` |
| Add labels | `gh issue edit N --add-label "bug,priority:high"` |
| Assign | `gh issue edit N --add-assignee user` |
| Comment | `gh issue comment N --body "..."` |
| Close | `gh issue close N` |
| Search | `gh issue list --search "keyword"` |

---

## 6. Codebase Inspection

Analyze repositories for lines of code, language breakdown, file counts, and code-vs-comment ratios.

### Prerequisites

```bash
pip install --break-system-packages pygount 2>/dev/null || pip install pygount
```

### Basic Summary

```bash
cd /path/to/repo
pygount --format=summary \
  --folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next,.tox,.eggs" \
  .
```

**IMPORTANT:** Always use `--folders-to-skip` to exclude dependency/build directories.

### Filter by Language

```bash
pygount --suffix=py --format=summary .
pygount --suffix=py,yaml,yml --format=summary .
```

### Output Formats

```bash
# Summary table (default)
pygount --format=summary .

# JSON for programmatic use
pygount --format=json .
```

### Special Pseudo-Languages

- `__empty__` — empty files
- `__binary__` — binary files
- `__generated__` — auto-generated
- `__duplicate__` — identical content
- `__unknown__` — unrecognized types

### Pitfalls

1. **Always exclude .git, node_modules, venv** — without `--folders-to-skip`, pygount may hang
2. **Markdown shows 0 code lines** — pygount classifies all Markdown as comments
3. **JSON files show low counts** — pygount counts JSON conservatively; use `wc -l` for accuracy

---

## Workflow Examples

### Complete PR Workflow

```bash
# 1. Start from clean main
git checkout main && git pull origin main

# 2. Branch
git checkout -b fix/login-redirect-bug

# 3. (Agent makes code changes)

# 4. Commit
git add src/auth/login.py tests/test_login.py
git commit -m "fix: correct redirect URL after login

Preserves the ?next= parameter instead of always redirecting to /dashboard."

# 5. Push
git push -u origin HEAD

# 6. Create PR
gh pr create --title "fix: correct redirect URL" --body "Preserves ?next= parameter."

# 7. Monitor CI
gh pr checks --watch

# 8. Merge
gh pr merge --squash --delete-branch
git checkout main && git pull origin main
```

### PR Review Workflow

```bash
# 1. Check out PR
git fetch origin pull/42/head:pr-42
git checkout pr-42

# 2. Read diff
git diff main...pr-42

# 3. Run tests
python -m pytest 2>&1 | tail -20

# 4. Post review
gh pr review 42 --approve --body "Reviewed by Hermes Agent."
```
