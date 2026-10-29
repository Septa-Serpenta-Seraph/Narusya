# Static Site Deployment

## When to use

Building and deploying a static HTML/CSS site (no framework, no build step) to Surge or Cloudflare Pages.

## Approach: Marisa's method

Pure static HTML — no React, no Vite, no build tools. Hand-written HTML with inline CSS. Host on Cloudflare Pages or Surge.

## Surge deployment

```bash
# Install surge (if not available)
npm install -g surge

# Deploy a directory
surge ./site domain.surge.sh

# Example
surge /home/adora/coil-and-code/site coil-and-code.surge.sh
```

Surge publishes immediately. No build step. Files are served as-is.

## Cloudflare Pages deployment

1. Push site to a GitHub repo
2. Connect repo to Cloudflare Pages
3. Set build command to empty (no build)
4. Set output directory to the site folder (e.g., `site/`)

## Design conventions (Coil & Code)

- Dark theme: `--bg: #0f1410`, `--gold: #d4af37`, `--emerald: #2e8b57`, `--bone: #f2e8d5`, `--muted: #9aa59c`
- Georgia serif for body, system sans for nav
- Max width 820px, centered
- Gold borders, emerald accents
- Navigation bar: Home / About / (future pages)
- Shared `coil-and-code.png` logo (193KB)

## Pitfalls

- Surge requires authentication on first deploy (opens browser for login)
- CNAME file in site dir sets custom domain
- robots.txt and sitemap.xml should be updated when adding new pages
- Keep CSS inline in each HTML file — no external stylesheets, no build step
- Test locally with `python3 -m http.server` before deploying
