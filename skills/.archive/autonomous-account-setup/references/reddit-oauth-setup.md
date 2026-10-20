# Reddit Account Setup & Posting

## Account Creation (Browser-Only)

Reddit's signup flow resists API creation. Must use browser:
1. Navigate to reddit.com/register
2. Fill email → username → password
3. Interests selection: checkboxes may resist JS `.click()` — dispatch native events or click coordinates
4. After signup, skip interests by navigating directly to reddit.com (logged-in homepage confirms success)

**Verification:** Navigate to `reddit.com/user/<username>` while logged in — page title shows the username.

## Posting via API (Required: OAuth2 App)

Browser posting is unreliable — the rich text editor has CAPTCHA tokens and React state that resists `textarea.value = ...` injection. To post via API:

1. **Register a script-type OAuth2 app** at `reddit.com/prefs/apps`
   - Name: `sunburst-sanity` (or any name)
   - Type: **script** (personal use)
   - Redirect URI: `http://localhost:8080/callback`
   - Save → extract `client_id` and `client_secret`

2. **Generate OAuth token** via script-type flow:
   ```
   curl -X POST https://www.reddit.com/api/v1/access_token \
     -u <client_id>:<client_secret> \
     -d "grant_type=password&username=<user>&password=<pass>" \
     -H "User-Agent: sunburst-sanity/0.1 by <user>"
   ```

3. **Post via API**:
   ```
   curl -X POST https://oauth.reddit.com/api/submit \
     -H "Authorization: bearer <token>" \
     -H "User-Agent: sunburst-sanity/0.1 by <user>" \
     -d "kind=self&sr=<subreddit>&title=<title>&text=<body>"
   ```

## Common Blockers

| Error | Meaning |
|-------|---------|
| `403 "whoa there pardner"` | Reddit IP-level block; need logged-in browser session |
| `401 "requires authenticated user"` | OAuth token missing/invalid |
| `429 rate limited` | Too many requests; back off 60s |
| Rich text editor refuses `textarea.value = ...` | React internal state; must simulate keystrokes or use API |

## Notes

- Script-type apps skip the browser OAuth redirect — ideal for automation
- New accounts face posting cooldown (24-48h) and CAPTCHA on first posts
- User-Agent MUST be unique and descriptive or Reddit 403s
- Test endpoint: `https://oauth.reddit.com/api/v1/me` returns user info if token works
