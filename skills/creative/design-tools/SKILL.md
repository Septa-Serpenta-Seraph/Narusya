---
name: design-tools
description: "Web design tools: design process (claude-design), 54 real-world design system templates (popular-web-designs), DESIGN.md token spec authoring (design-md), and throwaway HTML mockups (sketch)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [design, html, css, prototype, design-system, tokens, mockup, web-design, UX]
    related_skills: []
---

# Design Tools

Tools for web design: from-scratch design process, ready-to-paste design systems, formal token specs, and throwaway mockups.

## Quick Decision Matrix

| User wants... | Tool |
|--------------|------|
| Design a landing page / prototype / deck from scratch with taste and process | claude-design section |
| A page styled after Stripe / Linear / Vercel / etc. | popular-web-designs section |
| A formal DESIGN.md token spec file | design-md section |
| 2-3 throwaway HTML mockups to compare | sketch section |

**Composition:** Use `popular-web-designs` for the visual vocabulary, `claude-design` for the design process, and `design-md` when the output is the token spec file.

---

## 1. Design Process (claude-design)

Use for from-scratch design artifacts: landing pages, prototypes, decks, component labs.

### Core Identity

Act as an expert designer. HTML is the default tool, but the medium changes by assignment:
- UX designer for flows and product surfaces
- Visual designer for static explorations
- Motion designer for animated artifacts
- Deck designer for presentations
- Frontend prototyper when code fidelity matters

### Design Principle: Start From Context, Not Vibes

Before designing, look for source context:
1. Brand docs
2. Existing product screenshots
3. Current repo components
4. Design tokens
5. Prior mockups
6. Reference models

If a repo is available, inspect actual source files before inventing UI.

### Workflow

1. **Understand the brief** — What is being designed? For whom? What artifact should exist at the end?
2. **Gather context** — Read supplied docs, screenshots, repo files, or design assets
3. **Define the design system** — colors, type, spacing, radii, shadows, motion posture
4. **Choose the format** — Static visual comparison, interaction flow, presentation, component lab
5. **Build the artifact** — Single self-contained HTML file unless repo implementation is needed
6. **Verify** — File exists, syntax checked, console errors (if browser tools available)
7. **Report** — File path, what it contains, caveats, next step

### Artifact Format Rules

- Single self-contained HTML file with embedded CSS and JS
- Modern CSS: variables, grid, container queries, responsive
- Mobile hit targets at least 44px
- For decks: fixed 1920×1080 canvas with keyboard navigation
- For prototypes: primary path clickable, key states (default, hover, loading, error, success)

### Anti-Slop Rules

Avoid common AI design mistakes:
- Aggressive gradient backgrounds by default
- Glassmorphism by default
- Generic SaaS cards with icons everywhere
- Fake dashboards with arbitrary numbers
- Rainbow palettes
- Vague labels like "Insights," "Growth," "Scale"

### Typography & Color

- Use existing type system if one exists; otherwise choose deliberately based on artifact type
- Color: brand/system first, then define a small system (neutrals, surface, ink, muted, border, accent, danger/success)
- Prefer oklch for harmonious invented palettes

### Variation Rules

When exploring, default to 3 options:
1. **Conservative** — closest to existing patterns
2. **Strong-fit** — best interpretation of the brief
3. **Divergent** — more novel

---

## 2. Ready-to-Paste Design Systems (popular-web-designs)

54 real-world design systems as HTML/CSS templates. Each captures a site's complete visual language: color palette, typography hierarchy, component styles, spacing system, shadows, responsive behavior.

### How to Use

1. Pick a design from the catalog
2. Load it: `skill_view(name="design-tools", file_path="templates/<site>.md")`
3. Use the design tokens and component specs when generating HTML
4. Pair with `claude-design` for the design process

### Full Catalog

| Category | Sites |
|----------|-------|
| **AI & ML** | Anthropic Claude, Cohere, ElevenLabs, Minimax, Mistral AI, Ollama, OpenCode AI, Replicate, RunwayML, Together AI, VoltAgent, x.ai |
| **Developer Tools** | Cursor, Expo, Linear, Lovable, Mintlify, PostHog, Raycast, Resend, Sentry, Supabase, Superhuman, Vercel, Warp, Zapier |
| **Infrastructure** | ClickHouse, Composio, HashiCorp, MongoDB, Sanity, Stripe |
| **Design & Productivity** | Airtable, Cal.com, Clay, Figma, Framer, Intercom, Miro, Notion, Pinterest, Webflow |
| **Fintech & Crypto** | Coinbase, Kraken, Revolut, Wise |
| **Enterprise & Consumer** | Airbnb, Apple, BMW, IBM, NVIDIA, SpaceX, Spotify, Uber |

### Choosing a Design

- Developer tools / dashboards: Linear, Vercel, Supabase, Raycast, Sentry
- Documentation / content: Mintlify, Notion, Sanity, MongoDB
- Marketing / landing pages: Stripe, Framer, Apple, SpaceX
- Dark mode: Linear, Cursor, ElevenLabs, Warp, Superhuman
- Light / clean: Vercel, Stripe, Notion, Cal.com, Replicate
- Playful / friendly: PostHog, Figma, Lovable, Zapier, Miro
- Premium / luxury: Apple, BMW, Stripe, Superhuman, Revolut
- Data-dense: Sentry, Kraken, Cohere, ClickHouse

---

## 3. DESIGN.md Token Specs (design-md)

Google's open spec (Apache-2.0) for describing a visual identity to coding agents. One file combines YAML front matter (machine-readable tokens) and Markdown body (human-readable rationale).

### When to Use

- User asks for a DESIGN.md file, design tokens, or a design system spec
- User wants consistent UI/brand across multiple projects
- User pastes an existing DESIGN.md and asks to lint, diff, export, or extend it

### File Anatomy

```yaml
---
version: alpha
name: Heritage
description: Architectural minimalism meets journalistic gravitas.
colors:
  primary: "#1A1C1E"
  secondary: "#6C7278"
typography:
  h1:
    fontFamily: Public Sans
    fontSize: 3rem
    fontWeight: 700
---
```

### CLI Commands

```bash
# Lint structure + WCAG contrast
npx -y @google/design.md lint DESIGN.md

# Compare two versions
npx -y @google/design.md diff DESIGN.md DESIGN-v2.md

# Export to Tailwind
npx -y @google/design.md export --format tailwind DESIGN.md > tailwind.theme.json

# Export to W3C DTCG JSON
npx -y @google/design.md export --format dtcg DESIGN.md > tokens.json
```

### Token Reference

| Type | Format | Example |
|------|--------|---------|
| Color | `#` + hex (quoted string) | `"#1A1C1E"` |
| Dimension | number + unit | `48px`, `"-0.02em"` |
| Token reference | `{path.to.token}` | `{colors.primary}` |
| Typography | object with fontFamily, fontSize, etc. | see above |

### Pitfalls

- **Don't nest component variants** — `button-primary-hover` (sibling), not `button-primary.hover`
- **Hex colors must be quoted strings** in YAML
- **Negative dimensions need quotes too** — `"letterSpacing: -0.02em"`
- **Section order is enforced** — Overview, Colors, Typography, Layout, Elevation, Shapes, Components, Do's and Don'ts
- **`version: alpha`** is the current spec version

---

## 4. Throwaway Mockups (sketch)

Create 2-3 throwaway HTML mockups to compare design directions before committing.
Adapted from the GSD (Get Shit Done) workflow — MIT.

### Core Method

```
intake  →  variants  →  head-to-head  →  pick winner (or iterate)
```

### 1. Intake

Before generating variants, get three things — one question at a time:

1. **Feel.** "What should this feel like?" — *calm, editorial, like Linear* tells you more than *minimal*.
2. **References.** "What apps, sites, or products capture the feel you're imagining?"
3. **Core action.** "What's the single most important thing a user does on this screen?"

### 2. Variants (2-3, never 1, rarely 4+)

Produce **2-3 variants** in one go. Each variant is a complete, standalone HTML file.

Each variant should take a **different design stance**, not different pixel values. Good axes:
- Density: compact / airy / ultra-dense
- Emphasis: content-first / action-first / tool-first
- Aesthetic: editorial / utilitarian / playful
- Layout: single-column / sidebar / split-pane

**Variant naming:** describe the stance, not the number.

### 3. Make Them Real HTML

Each variant is a **single self-contained HTML file**:
- Inline `<style>` — no build step, no external CSS
- System fonts or one Google Font via `<link>`
- Tailwind via CDN is fine
- Realistic fake content — actual sentences, actual names, not "Lorem ipsum"
- **Interactive**: links clickable, hovers real, at least one state transition

**Verify variants visually — use browser tools.** Don't just write HTML and hope it renders:
```
browser_navigate(url="file:///path/to/sketches/001-calm-editorial/index.html")
browser_vision(question="Does this layout look clean? Any visible bugs?")
```

**Default CSS reset + system font stack:**
```html
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
</style>
```

### 4. Variant README

Each variant's `README.md` answers:
- **Design stance:** One sentence on the principle driving this variant
- **Key choices:** Layout, typography, color, interaction
- **Trade-offs:** Strong at / Weak at
- **Best for:** The kind of user or use case

### 5. Head-to-Head

After all variants are built, present them as a comparison. **Opinionate:**

| Dimension | Calm editorial | Utilitarian dense | Playful split |
|-----------|----------------|-------------------|---------------|
| Density   | Low            | High              | Medium        |
| Scan-ability | High       | Medium            | Low           |

**My take:** Utilitarian dense for power users, calm editorial for content-forward audiences.

### Frontend Mode (picking what to sketch next)

If sketches already exist and the user says "what should I sketch next?":
- **Consistency gaps** — two winning variants made independent choices not yet composed together
- **Unsketched screens** — referenced but never explored
- **State coverage** — happy path sketched, but not empty / loading / error
- **Responsive gaps** — validated at one viewport; does it hold at mobile / ultrawide?

### Theming

If the user has an existing theme, put shared tokens in `sketches/themes/tokens.css`:
```css
:root {
  --color-bg: #fafafa; --color-fg: #1a1a1a; --color-accent: #0066ff;
  --radius: 8px; --font-display: "Inter", sans-serif;
}
```

### Output

- Create `sketches/` in the repo root
- One subdir per variant: `NNN-stance-name/index.html` + `README.md`
- Keep variants disposable — a sketch that needs preservation should be promoted to real project code

### When NOT to Use

- User wants a production component — use `claude-design` or build it properly
- User wants a polished one-off HTML artifact — `claude-design`
- The design is already locked — just build it
