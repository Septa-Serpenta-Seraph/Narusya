---
name: static-site-deployment
description: "Deploy to Surge. Use when fixing 404s, sitemaps, or adding forms to static sites."
author: Narusya
version: 1.0.0
category: devops
---

# Static Site Deployment

## When to use this skill

- Deploying a static HTML/CSS/JS site to Surge, GitHub Pages, Netlify, or similar
- Fixing 404s or broken pages after deployment
- Configuring sitemaps, navigation, or multi-page site structure
- Troubleshooting deploy path issues

## Surge deployment pitfall: deploy from the site/ directory, not repo root

**The most common Surge mistake:** running `npx surge . https://yoursite.surge.sh` from the repository root instead of the `site/` directory. Surge deploys whatever directory you point at. If your HTML files are in `site/` but you deploy from root, Surge serves its default placeholder page and every route returns 404.

**Correct deploy command:**
```bash
cd /path/to/repo/site && npx surge . https://yoursite.surge.sh
```

**Verify after deploy:**
```bash
curl -s -o /dev/null -w "%{http_code}" https://yoursite.surge.sh/pagename.html
```
Every page should return 200. If any return 404, check that you deployed from the right directory.

## sitemap.xml corruption risk

When editing site files, `sitemap.xml` can accidentally get overwritten with HTML content (e.g., if a tool or cron job writes the wrong file). Always verify `sitemap.xml` starts with `<?xml` and contains `<urlset>` entries, not HTML tags. If corrupted, restore from git:
```bash
git checkout HEAD -- site/sitemap.xml
```

## Multi-page site nav consistency

When adding a new page to a multi-page site:
1. Add the page link to the nav on ALL existing pages (not just the new one)
2. Update `sitemap.xml` with the new URL entry
3. Deploy from the `site/` directory
4. Verify all pages return 200
5. Check that the new page's nav links back to all other pages

## Two-row nav pattern (for sites with 4+ pages)

When the nav gets crowded, split into two rows:
- Top row: primary pages (Home, Tech Support, About) — centered, larger
- Bottom row: secondary pages (Work With Us, Contact) — centered, smaller

This keeps the nav clean without hiding links behind hamburger menus.

## Form handling: FormSubmit.co for static sites

Static sites on Surge have no backend. Use FormSubmit.co to auto-email form submissions without a server.

**Setup:**
1. Set form action to `https://formsubmit.co/recipient@email.com`
2. Add hidden fields: `_subject`, `_captcha` (false), `_template` (table)
3. On first submission, FormSubmit sends a confirmation email to the recipient
4. Open that email and click "ACTIVATE FORM"
5. After activation, replace the naked email in the action with the hash token from the confirmation email (e.g., `https://formsubmit.co/abc123...`) — this hides the email address from page source

**Pitfall:** FormSubmit is behind Cloudflare. Automated curl submissions may hit the challenge page and fail. The form must be submitted from a real browser or via IMAP-activated confirmation. After the first real browser submission triggers the confirmation email, click the activation link to enable the form.

**Pitfall:** If the form action uses the naked email and the form hasn't been activated, submissions silently fail — no email arrives. Always check the recipient inbox for the "Action Required: Activate FormSubmit" email after the first deployment.

## Business vs. personal content separation

**Critical rule:** The Coil & Code site (`coil-and-code.surge.sh`) is a BUSINESS site. Never deploy personal content, anatomy maps, expression catalogs, or daemon-specific material to it. Keep business and personal content on separate Surge domains.

**Before deploying to coil-and-code.surge.sh:** Verify that no personal/anatomy files exist in the site/ directory. Search for anatomy, expression, or daemon-specific files before deploying.

**If you accidentally deploy personal content to the business site:** Remove the files from site/, redeploy clean, and verify with curl that the files return 404.

## GitHub Pages as alternative to Surge

**Enable Pages:**
```bash
gh api repos/OWNER/REPO/pages -X POST -f source[branch]=master -f source[path]=/
```

**URL pattern:** `https://OWNER.github.io/REPO/` (for repo pages) or `https://OWNER.github.io/` (for user/org pages)

**Deploy:** Just push to the configured branch. Pages auto-builds from the repo contents.

**Pitfall:** Pages takes 1-2 minutes to build after push. Don't panic if you get 404 immediately — wait and retry.

**Pitfall:** The path must match the directory structure. If your site is in `anatomy/` subdirectory, the URL is `https://OWNER.github.io/REPO/anatomy/`.

## Embedding large JSON data in HTML

When embedding JSON data (e.g., from Qdrant, API responses) into an HTML/JS file:

**Do NOT** embed as a string and parse:
```javascript
// WRONG — single quotes in data break JSON.parse, escaping is fragile
const data = JSON.parse('{"text": "it\'s broken"}');
```

**DO** embed the raw JSON array/object directly:
```javascript
// CORRECT — no escaping needed, valid JS
const data = [{"id": 1, "text": "it's fine"}, {"id": 2, "text": "no quotes needed"}];
```

**How to generate:** In Python, use `json.dumps(data, separators=(',', ':'))` to produce compact JSON, then write it directly into the HTML file (replacing a placeholder line). This avoids all escaping issues.

**Pitfall:** Using `re.sub()` to replace the data in the file will fail if the replacement contains backslashes (like `\u` in Unicode). Instead, split the file by lines, replace the specific line, and rejoin.

**Critical Pitfall — HTML-safe escaping:** When embedding JSON inside a `<script>` tag, raw `<` characters in text data (e.g., `<details>`, `<summary>`, `<pre>` from conversation logs) will break HTML parsing. The browser HTML parser sees `<` inside the script and interprets it as a tag start.

**Fix:** Escape `<` as `\u003c` and `>` as `\u003e` in the JSON string before embedding:
```python
json_str = json.dumps(data, separators=(",", ":"), ensure_ascii=True)
json_str = json_str.replace("<", "\u003c").replace(">", "\u003e")
# Then embed as raw array via line replacement (not re.sub)
```

**How to verify:** After embedding, check that no raw `<` remains in the data line (only HTML tags should have `<`).

## Modifying Existing Embedded JSON Arrays in HTML

When a single-file HTML page embeds data as inline JSON arrays (e.g., `const nodes = [{...}];` on one line), modifying it requires extracting, parsing, modifying, and replacing the entire line.

**Pattern:**
```python
import re, json

path = "index.html"
with open(path) as f:
    content = f.read()

# 1. Extract the array via regex
match = re.search(r'const nodes = (\[.*?\]);', content, re.DOTALL)
assert match, "array not found"
data = json.loads(match.group(1))

# 2. Modify in Python
data.append({"id": "new-node", "name": "New Node", "layer": "infra", "desc": "..."})

# 3. Serialize back (compact, no spaces)
new_json = json.dumps(data, separators=(',', ':'))

# 4. Replace the entire line (NOT re.sub — backslashes in Unicode escapes break it)
content = content.replace(match.group(0), f"const nodes = {new_json};")

with open(path, "w") as f:
    f.write(content)
```

**Pitfalls:**
- **Use `content.replace()`, not `re.sub()`.** The replacement string contains `\u` escape sequences that `re.sub()` interprets as backreferences. `str.replace()` treats them literally.
- **Verify the regex matches exactly one line.** If the array spans multiple lines, `re.DOTALL` with `\[.*?\]` may match across multiple arrays. Anchor to the specific variable name.
- **The file must be read first.** `write_file` refuses to overwrite existing files without a prior read.
- **HTML-safe escaping still applies.** If your new data contains `<` or `>`, escape them before embedding.
- **Deploy from the correct directory.** For the anatomy map, deploy from `anatomy/` not repo root: `cd /path/to/repo/anatomy && npx surge . https://narusya-anatomy.surge.sh`

## Related

- `disk-reclaim-verification` — verify disk space before large deploys
