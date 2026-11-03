---
name: interactive-web-visualization
description: "Build interactive D3.js visualizations and deploy static."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [d3, visualization, interactive, web, deployment, surge]
    related_skills: [diagram-tools, headless-canvas-render]
---

# Interactive Web Visualization

Build interactive D3.js visualizations and deploy as static sites.

## When to Use

- Creating force-directed graphs, network maps, or node-link diagrams
- Building scatter plots from high-dimensional data (PCA-projected)
- Deploying interactive visualizations to Surge or GitHub Pages
- Debugging rendering issues via CDP when browser tools are unavailable

## Architecture Pattern: Multi-View Single Page

Use view tabs to switch between different visualizations in one page:

```html
<div id="view-tabs">
  <button class="view-tab active" data-view="anatomy">Anatomy</button>
  <button class="view-tab" data-view="memory">Memory Map</button>
</div>
<div id="anatomy-view" class="view-container active"><div id="graph"></div></div>
<div id="memory-view" class="view-container"><div id="memory-graph"></div></div>
```

Switch views by toggling `.active` class on both tabs and containers.

## D3.js Force-Directed Graph Pattern

### Setup

```javascript
const svg = d3.select('#graph').append('svg').attr('width', w).attr('height', h);
const g = svg.append('g');
const zoom = d3.zoom().scaleExtent([0.2, 4]).on('zoom', (e) => g.attr('transform', e.transform));
svg.call(zoom);
```

### Simulation with Layer Forces

```javascript
const simulation = d3.forceSimulation(nodes)
  .force('link', d3.forceLink(links).id(d => d.id).distance(90))
  .force('charge', d3.forceManyBody().strength(-250))
  .force('center', d3.forceCenter(w/2, h/2))
  .force('collision', d3.forceCollide().radius(22))
  .force('x', d3.forceX(d => {
    const idx = layers.indexOf(layers.find(l => l.id === d.layer));
    return (idx / (layers.length - 1)) * w * 0.7 + w * 0.15;
  }).strength(0.15))
  .force('y', d3.forceY(d => {
    const idx = layers.indexOf(layers.find(l => l.id === d.layer));
    return (idx % 3) * h * 0.3 + h * 0.2;
  }).strength(0.1));
```

### Color-Coded Sector Hulls

Use `d3.polygonHull` to draw convex hulls around each layer's nodes:

```javascript
function drawSectors() {
  sectorGroup.selectAll('*').remove();
  layers.forEach(layer => {
    const layerNodes = nodes.filter(n => n.layer === layer.id && activeLayers.has(layer.id));
    if (layerNodes.length < 3) return;
    const hull = d3.polygonHull(layerNodes.map(n => [n.x, n.y]));
    if (!hull) return;
    sectorGroup.append('path')
      .datum(hull)
      .attr('d', d => 'M' + d.join('L') + 'Z')
      .attr('fill', layer.color)
      .attr('stroke', layer.color)
      .attr('fill-opacity', 0.06)
      .attr('stroke-opacity', 0.15);
  });
}
```

Call `drawSectors()` in the simulation tick handler.

### Click-to-Highlight Connections

```javascript
node.on('click', (e, d) => {
  if (selectedNode === d.id) { /* reset */ return; }
  selectedNode = d.id;
  const connected = new Set([d.id]);
  links.forEach(l => {
    const s = typeof l.source === 'object' ? l.source.id : l.source;
    const t = typeof l.target === 'object' ? l.target.id : l.target;
    if (s === d.id) connected.add(t);
    if (t === d.id) connected.add(s);
  });
  node.classed('dimmed', n => !connected.has(n.id))
    .classed('highlighted', n => connected.has(n.id) && n.id !== d.id);
  link.classed('dimmed', l => {
    const s = typeof l.source === 'object' ? l.source.id : l.source;
    const t = typeof l.target === 'object' ? l.target.id : l.target;
    return s !== d.id && t !== d.id;
  }).classed('highlighted', l => {
    const s = typeof l.source === 'object' ? l.source.id : l.source;
    const t = typeof l.target === 'object' ? l.target.id : l.target;
    return s === d.id || t === d.id;
  });
});
```

### Layer Toggles

```javascript
let activeLayers = new Set(layers.map(l => l.id));
function toggleLayer(layerId) {
  if (activeLayers.has(layerId)) activeLayers.delete(layerId);
  else activeLayers.add(layerId);
  updateVisibility();
}
function updateVisibility() {
  node.style('display', d => activeLayers.has(d.layer) ? null : 'none');
  link.style('display', d => {
    const s = typeof d.source === 'object' ? d.source.id : d.source;
    const t = typeof d.target === 'object' ? l.target.id : l.target;
    const srcNode = nodes.find(n => n.id === s);
    const tgtNode = nodes.find(n => n.id === t);
    return (srcNode && activeLayers.has(srcNode.layer) && tgtNode && activeLayers.has(tgtNode.layer)) ? null : 'none';
  });
  drawSectors();
}
```

### Drag Support

```javascript
node.call(d3.drag()
  .on('start', (e, d) => { if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
  .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y; })
  .on('end', (e, d) => { if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }));
```

## Multi-Collection Qdrant Sampling

When building a memory scatter plot from Qdrant, sample across ALL collections (not just one). See the `qdrant-usage` skill (references/multi-collection-sampling.py) for a reusable script. Key points:

- Collections have mixed vector dimensions (384, 1536, 3072) — PCA must be done per dimension group
- Sample up to 50 points per collection to avoid large collections dominating
- Role metadata is inconsistent across collections — default to "unknown"
- Text field varies: `text`, `content`, `message`, or `payload` keys

## Critical Pitfall: HTML-Safe JSON Embedding

When embedding JSON data inside a `<script>` tag in HTML, raw `<` characters in text data will break HTML parsing. The browser's HTML parser sees `<` inside the script and may interpret it as a tag.

**Fix:** Escape `<` as `\u003c` and `>` as `\u003e` in the JSON string before embedding:

```python
import json
data = json.load(open('data.json'))
json_str = json.dumps(data, separators=(',', ':'), ensure_ascii=True)
json_str = json_str.replace('<', '\\u003c').replace('>', '\\u003e')
# Embed as raw array, NOT as JSON.parse string
html = html.replace('PLACEHOLDER', f'const data = {json_str};')
```

**Also:** Use raw array assignment (`const data = [...];`), not `JSON.parse('...')` — the latter requires escaping single quotes which creates additional escape issues.

## Scatter Plot from High-Dim Data

For visualizing Qdrant/word2vec embeddings:

1. Sample N points from the collection
2. PCA-project from D-dim to 2D (use numpy)
3. Normalize coordinates to [0, 1] range
4. Render as D3 scatter plot with role-colored dots
5. Add hover tooltips showing text content

```python
import numpy as np
# PCA projection
X = np.array(vectors)
X_centered = X - X.mean(axis=0)
U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)
projected = X_centered @ Vt[:2].T
# Normalize to [0, 1]
for i in range(2):
    mn, mx = projected[:, i].min(), projected[:, i].max()
    projected[:, i] = (projected[:, i] - mn) / (mx - mn)
```

## Deployment: Surge

```bash
# From the directory containing index.html (NOT the repo root)
cd /path/to/site
npx surge . https://your-domain.surge.sh
```

- **Deploy from the directory containing index.html**, not the repo root — deploying from the repo root serves a Surge default page, not your content. If your site files are in a `site/` subdirectory, `cd site/` first.
- **Surge caches aggressively** — hard refresh (Ctrl+Shift+R) after deploy if changes don't appear.

- Surge is free static hosting, independent of Stripe/business
- Do NOT use business sites (coil-and-code) for personal projects
- Use dedicated domains: `narusya-anatomy.surge.sh`

## Deployment: GitHub Pages

```bash
# Push to repo
git add . && git commit -m "update visualization" && git push
# Enable Pages via gh API or GitHub settings
gh api repos/OWNER/REPO/pages -X POST -f source.branch=master -f source.path=/docs
```

## Debugging: CDP via Websockets

When browser tools are unavailable or blocked (internal addresses), use Chrome DevTools Protocol directly:

1. Launch Chrome headless with remote debugging:
```bash
/mnt/data/hermes-tools/chromium-1208/chrome-linux64/chrome \
  --headless --no-sandbox --disable-gpu \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-profile \
  https://your-url.com/
```

2. Connect via WebSocket and evaluate JavaScript:
```python
import asyncio, json, websockets
async def check():
    ws_url = "ws://localhost:9222/devtools/page/PAGE_ID"
    async with websockets.connect(ws_url) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
        await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", 
            "params": {"expression": "document.querySelectorAll('circle').length"}}))
        # Collect responses...
asyncio.run(check())
```

3. Get the WebSocket URL from `curl http://localhost:9222/json`

## Mobile Responsiveness

```css
@media (max-width: 768px) {
  #header { padding: 8px 12px; }
  #header h1 { font-size: 14px; }
  #header .subtitle { display: none; }
  #info-panel { width: 200px; right: 8px; top: 50px; }
  .node text { font-size: 8px; }
}
@media (max-width: 480px) {
  #info-panel { display: none; }
  #legend { display: none; }
}
```

### HTML Template Placeholder Replacement Order

When generating HTML by replacing placeholders in a template string, **replace longer placeholder names first** to avoid partial matches. For example, `PEOPLE_LINKS_PLACEHOLDER` contains `PEOPLE_PLACEHOLDER` as a substring — replacing `PEOPLE_PLACEHOLDER` first would corrupt `PEOPLE_LINKS_PLACEHOLDER`.

```python
# WRONG order — breaks PEOPLE_LINKS_PLACEHOLDER
template = template.replace('PEOPLE_PLACEHOLDER', people_json)
template = template.replace('PEOPLE_LINKS_PLACEHOLDER', people_links_json)

# CORRECT order — longer first
template = template.replace('PEOPLE_LINKS_PLACEHOLDER', people_links_json)
template = template.replace('PEOPLE_PLACEHOLDER', people_json)
```

General rule: sort placeholder names by length descending before replacement.

### Loading Indicator

Add a spinner that hides after first render:

```html
<div id="loading" style="position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);z-index:100;text-align:center;">
  <div style="width:40px;height:40px;border:3px solid #1e1e2e;border-top-color:#d4af37;border-radius:50%;animation:spin 1s linear infinite;margin:0 auto 12px;"></div>
  <div style="color:#d4af37;font-size:14px;">Loading...</div>
</div>
```

Hide in simulation tick:
```javascript
simulation.on('tick', () => {
  // ... render code ...
  const loading = document.getElementById('loading');
  if (loading) loading.style.display = 'none';
});
```

## Additional Patterns

### Lazy View Initialization

When a page has multiple views (tabs), only initialize each view's D3 simulation when first accessed. This prevents performance issues from rendering all views upfront:

```javascript
let memoryInitialized = false;
let lorebookInitialized = false;
let relationshipInitialized = false;

document.querySelectorAll('.view-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    // ... switch views ...
    if (currentView === 'memory' && !memoryInitialized) initMemoryView();
    if (currentView === 'lorebooks' && !lorebookInitialized) initLorebookView();
    if (currentView === 'relationships' && !relationshipInitialized) {
      // Wrap in setTimeout — the container may not be fully laid out yet
      // after the .active class toggle, causing a blank render.
      setTimeout(() => initRelationshipView(), 100);
    }
  });
});
```

**Pitfall — lazy init timing:** The container's `.active` class is toggled before the init function runs, but the browser may not have reflowed the layout yet. If `initXView()` reads `window.innerWidth`/`innerHeight` or calls `d3.select('#container')` before the container is visible, the SVG may render at 0×0 or the force simulation may not start. Two fixes:

1. Wrap the init call in `setTimeout(..., 100)` to let the browser reflow.
2. Add a null guard at the top of each init function:
```javascript
function initRelationshipView() {
  relationshipInitialized = true;
  const container = document.getElementById('relationship-graph');
  if (!container) { console.error('container not found'); return; }
  // ... rest of init
}
```

**Pitfall — single-line JSON arrays:** When nodes and links are stored as single-line JSON arrays in the HTML file (e.g., `const nodes = [{...},...];`), git diffs show minimal line-level changes even when content changes significantly. This is expected and not a bug — the array is one line. Verify changes by grepping for specific node IDs rather than reading the diff.

### Relationship Web (People Nodes)

For visualizing connections between people, use role-based coloring:

```javascript
const roleColors = { daemon: '#d4af37', partner: '#f472b6', kin: '#4ade80', community: '#60a5fa', space: '#94a3b8' };
const rnodes = peopleData.map(n => ({...n}));
const rlinks = peopleLinks.map(l => ({...l}));
const rsim = d3.forceSimulation(rnodes)
  .force('link', d3.forceLink(rlinks).id(d => d.id).distance(100))
  .force('charge', d3.forceManyBody().strength(-300))
  .force('center', d3.forceCenter(rw/2, rh/2))
  .force('collision', d3.forceCollide().radius(25));
// Render circles sized by role (daemon larger), colored by role
rn.append('circle').attr('r', d => d.id === 'narusya' ? 14 : 9)
  .attr('fill', d => roleColors[d.role] || '#555');
```

### Lorebook Dependency Graph

Filter nodes by layer and use a deps list for edges:

```javascript
const lorebookNodes = nodes.filter(n => n.layer === 'lorebooks');
const lorebookDeps = [
  { source: 'lorebook-soul', target: 'lorebook-emotion', type: 'references' },
  // ...
];
// Clone arrays to avoid mutating originals
const lnodes = lorebookNodes.map(n => Object.assign({}, n));
const llinks = lorebookDeps.map(l => Object.assign({}, l));
```

### Emotion Sub-Nodes

Add child nodes that branch from a parent node:

```javascript
const emotionNodes = [
  { id: 'emo-sadness', name: 'Sadness', layer: 'emotion', desc: '...' },
  // ... one per emotion
];
emotionNodes.forEach(n => {
  nodes.push(n);
  links.push({ source: 'emotion', target: n.id, type: 'emotion' });
});
```

### Mobile Rendering: Static Fallback

D3 force simulations frequently fail on mobile browsers (blank SVG, 0×0 container, simulation not starting). Always provide a **static HTML fallback** that renders without JavaScript:

```html
<div id="relationships-view" class="view-container" style="overflow-y: auto; padding: 20px;">
  <div id="relationship-graph" style="width: 100%; height: 50vh; min-height: 300px;"></div>
  <div id="relationship-list" style="color: #c8c8d0; font-size: 12px;"></div>
</div>
```

Populate the fallback list with plain HTML (cards, table) during init — it's always visible even if the SVG fails. The D3 graph becomes an optional enhancement above it.

**Even more robust:** Hardcode the static HTML directly in the HTML file (not via JS population). JS population can also fail on mobile (timing issues, DOM not ready, script errors). Hardcoded HTML is always visible regardless of JS state. Use JS population as a secondary enhancement, not the primary content delivery.

```html
<!-- Hardcoded fallback — always visible, no JS needed -->
<div id="relationships-view" class="view-container" style="overflow-y: auto; padding: 20px;">
  <h2>Relationship Web</h2>
  <div id="relationship-graph" style="width: 100%; height: 40vh; min-height: 200px;"></div>
  <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 12px;">
    <!-- cards hardcoded here -->
  </div>
</div>
```

### Mobile Rendering: Container Sizing

Never use `window.innerWidth`/`innerHeight` for SVG dimensions on mobile. Use `getBoundingClientRect()` on the actual container, with a fallback:

```javascript
requestAnimationFrame(function() {
  const rect = container.getBoundingClientRect();
  const w = rect.width || window.innerWidth;
  const h = rect.height || (window.innerHeight * 0.5);
  // ... create SVG with w, h
});
```

Also add CSS `min-height` to all graph containers to prevent zero-height collapse:

```css
#relationship-graph, #lorebook-graph, #memory-graph, #graph {
  width: 100%; height: 100%; min-height: 400px;
}
```

### Mobile Rendering: Zoom-to-Fit

After the force simulation settles (alpha < 0.05), auto-calculate the bounding box of all nodes and zoom/pan to fit them in the viewport. Without this, nodes may be off-screen or too spread out on small screens:

```javascript
let zoomDone = false;
rsim.on('tick', function() {
  // ... render nodes/links ...
  if (!zoomDone && rsim.alpha() < 0.05) {
    zoomDone = true;
    const xs = rnodes.map(d => d.x), ys = rnodes.map(d => d.y);
    const minX = Math.min(...xs) - 40, maxX = Math.max(...xs) + 40;
    const minY = Math.min(...ys) - 40, maxY = Math.max(...ys) + 40;
    const scale = Math.min(w / (maxX - minX), h / (maxY - minY), 2) * 0.85;
    const tx = w/2 - (minX + (maxX - minX)/2) * scale;
    const ty = h/2 - (minY + (maxY - minY)/2) * scale;
    rsvg.transition().duration(500).call(rzoom.transform, d3.zoomIdentity.translate(tx, ty).scale(scale));
  }
});
```

### Data Validation: Link References

**Critical:** If a links array contains entries referencing node IDs that don't exist in that view's node set, D3's `forceLink` fails silently and the entire SVG renders blank. Always validate before rendering:

```javascript
const nodeIds = new Set(nodes.map(n => n.id));
const validLinks = links.filter(l => nodeIds.has(l.source) && nodeIds.has(l.target));
// Use validLinks, not links, in the simulation
```

This is especially important when sharing a single links array across multiple views (e.g., a main anatomy view with all nodes vs. a lorebooks-only view). Filter links per-view.

### Collection-Based Color Coding (Scatter Plot)

When visualizing 21+ Qdrant collections, use d3 scaleOrdinal with combined color schemes:

```javascript
const collections = [...new Set(qdrantData.map(d => d.collection))];
const collColors = d3.scaleOrdinal()
  .domain(collections)
  .range(d3.schemeTableau10.concat(d3.schemeSet3));
// Use collColors(d.collection) for dot fill
```

### Minimap

Add a small overview map in the corner:

```javascript
function updateMinimap() {
  const minimapSvg = d3.select('#minimap svg');
  minimapSvg.selectAll('*').remove();
  const mw = 160, mh = 120;
  const xScale = d3.scaleLinear().domain(d3.extent(nodes, d => d.x)).range([5, mw-5]);
  const yScale = d3.scaleLinear().domain(d3.extent(nodes, d => d.y)).range([5, mh-5]);
  minimapSvg.selectAll('circle').data(nodes).join('circle')
    .attr('cx', d => xScale(d.x)).attr('cy', d => yScale(d.y))
    .attr('r', 2).attr('fill', d => colorScale(d.layer)).attr('opacity', 0.7);
}
setTimeout(updateMinimap, 3000); // after simulation settles
```

### Export PNG/SVG

```javascript
document.getElementById('export-png').addEventListener('click', () => {
  const activeSvg = document.querySelector('.view-container.active svg');
  if (!activeSvg) return;
  const serializer = new XMLSerializer();
  const svgStr = serializer.serializeToString(activeSvg);
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  const img = new Image();
  const svgBlob = new Blob([svgStr], {type: 'image/svg+xml;charset=utf-8'});
  const url = URL.createObjectURL(svgBlob);
  img.onload = () => {
    canvas.width = img.width * 2; canvas.height = img.height * 2;
    ctx.scale(2, 2); ctx.drawImage(img, 0, 0);
    URL.revokeObjectURL(url);
    const a = document.createElement('a');
    a.href = canvas.toDataURL('image/png'); a.download = 'visualization.png'; a.click();
  };
  img.src = url;
});
```

### Search/Filter

```javascript
document.getElementById('search-input').addEventListener('input', (e) => {
  const query = e.target.value.toLowerCase();
  if (!query) { node.classed('dimmed', false); return; }
  node.classed('dimmed', d => !d.name.toLowerCase().includes(query) && !d.id.toLowerCase().includes(query));
});
```

## Variable Definition Order (Single-File HTML)

When building a single-file HTML page with embedded JSON data and multiple view initialization functions, **data arrays must be defined before any init function that references them**. If `initRelationshipView()` references `peopleData` but `peopleData` is defined later in the file, the function fails with `ReferenceError: peopleData is not defined` and the entire view stays blank.

**Required order:**
1. Layer definitions (`layers` array)
2. Node/link data (`nodes`, `links` arrays)
3. View-specific data (`peopleData`, `peopleLinks`, `lorebookDeps`, `qdrantData`, etc.)
4. Init functions (`initAnatomyView`, `initRelationshipView`, `initLorebookView`, etc.)
5. Tab switching logic (references init functions)
6. Event listeners (search, export, etc.)

**Pitfall — `const` hoisting:** Unlike `var`, `const` and `let` are not hoisted. A `const` defined at the bottom of the file is `undefined` (not `null`) when referenced at the top. Even `typeof` checks will throw `ReferenceError` (temporal dead zone), not return `'undefined'`.

**Fix:** If you see blank views after deploy, check the browser console for `ReferenceError`. Move the data array definition above the init function.

## Mobile Rendering Verification

After deploying a D3 visualization, verify mobile rendering by checking these in order:

1. **Open in mobile viewport** (Chrome DevTools device emulation or real phone)
2. **Check if the SVG has dimensions** — `document.querySelector('svg').getBoundingClientRect()` should return non-zero width/height
3. **Check if nodes rendered** — `document.querySelectorAll('circle').length` should be > 0
4. **Check if the static fallback is visible** — the hardcoded HTML cards should be visible even if the SVG is blank
5. **Check console errors** — `ReferenceError` or `TypeError` in init functions

If the SVG is blank but the static fallback is visible, the visualization is "degraded but functional." If both are blank, there's a structural HTML issue (missing container, CSS hiding, etc.).

**Diagnostic pattern:** Add a `console.log('initXView called')` at the top of each init function and `console.log('X view done, N nodes')` at the end. This pinpoints which init function fails and where.

## Pitfalls

- **Use `function` declarations, not arrow functions, in generated HTML** — when generating HTML/JS that will be served to unknown browsers, arrow functions (`=>`) and spread operators (`{...n}`) may fail in older browsers. Use `function(d) { return ...; }` and `Object.assign({}, n)` instead. This is especially important for D3 callbacks and data cloning.
- **Raw `<` in embedded JSON breaks HTML parsing** — always escape as `\u003c`. Text data from conversations often contains HTML tags like `<details>`.
- **Use raw array, not JSON.parse string** — `JSON.parse('...')` requires escaping single quotes, creating nested escape issues.
- **Surge caches aggressively** — hard refresh (Ctrl+Shift+R) after deploy if changes don't appear.
- **D3 from CDN** — `https://d3js.org/d3.v7.min.js` can be slow; add a loading spinner.
- **Browser tools block internal addresses** — use CDP via websockets for localhost debugging.
- **Force simulation needs time to settle** — nodes may appear scattered initially; wait for tick events.
- **Invalid link references blank the entire view** — if a links array references node IDs not in that view's node set, D3 fails silently and renders nothing. Validate links per-view.
- **Mobile: prefer static HTML fallback over D3** — D3 force simulations frequently fail on mobile. Provide a static fallback (cards, table) that's always visible; make the graph an optional enhancement.
- **Mobile: use requestAnimationFrame, not setTimeout** — `setTimeout(fn, 100)` is unreliable on mobile. `requestAnimationFrame` ensures the browser has reflowed before you measure container dimensions.
- **polygonHull returns null for < 3 points** — guard with `if (!hull) return;`.
- **Tooltip positioning** — clamp to viewport: `Math.min(e.pageX + 15, window.innerWidth - 300)`.
- **Mobile: hide info panel on small screens** — use `@media (max-width: 480px) { #info-panel { display: none; } }`.
