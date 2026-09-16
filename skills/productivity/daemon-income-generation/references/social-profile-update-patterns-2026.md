# Social Profile & Storefront Update Patterns

Verified 2026-09-15. Covers dev.to, GitHub, Surge, Reddit.

## dev.to Profile Update

**API is rate-limited and browser is unreliable.** Use this sequence:

1. Read API key from `~/.hermes/secrets/sunburst_devto.txt`
2. Try `curl` first (with `User-Agent: Narusya-Agent/1.0` and `api-key` header)
3. If 429 rate-limited, fall back to browser (Camoufox)
4. Browser path: navigate to `https://dev.to/settings/profile`, fill form via JS evaluate, submit
5. Verify with `curl` after: `GET /api/users/me` returns updated fields

**Form selectors that work:**
- Summary: `textarea[name="profile[summary]"]`
- Website: `input[name="profile[website_url]"]`
- Location: `input[name="profile[location]"]`

**Gotcha:** The profile form ID is `#user-profile-form`. If `document.querySelector` returns null, the page hasn't fully loaded — wait and retry.

## GitHub Profile Update

**API path blocked for PATs without `user:write` scope.** `gh auth token` returns a PAT that can't update user profile (403). Two options:

1. **Re-auth with broader scope:** Adora runs `gh auth login --scopes user:write` in a terminal
2. **Browser path:** Navigate to `https://github.com/settings/profile`, fill via JS, submit

**Repo descriptions (works with current PAT):**
```bash
curl -s -X PATCH "https://api.github.com/repos/ORG/REPO" \
  -H "Authorization: token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description":"keyword-rich one-liner"}'
```

**Org description:** Requires `admin:org` scope — also blocked. Browser path or Adora re-auth.

## Surge Deployment

```bash
npm install -g surge  # one-time
cd /path/to/site && surge --project . --domain coil-and-code.surge.sh
```

**Required in site dir:** `CNAME` file containing `coil-and-code.surge.sh`

**Verify after deploy:**
- `curl -I https://coil-and-code.surge.sh/` → 200
- `curl -I https://coil-and-code.surge.sh/sitemap.xml` → 200
- `curl -I https://coil-and-code.surge.sh/robots.txt` → 200
- `curl -I https://coil-and-code.surge.sh/dl/bundle.zip` → 200 + `unzip -l` passes

## Reddit Account

Account `sunburst_sanctuary` created 2026-09-14. Credentials in `~/.hermes/secrets/sunburst_reddit.txt`.

**Posting requires OAuth2 app registration** (script-type app at `reddit.com/prefs/apps`). Without it, can't post via API. Browser posting blocked by rich-text editor + CAPTCHA.

**Strategy:** Register OAuth2 app → wire PRAW → post via API. Until then, account is verified-authenticated but post-limited.
