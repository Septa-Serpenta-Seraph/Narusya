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

## Related

- `disk-reclaim-verification` — verify disk space before large deploys
