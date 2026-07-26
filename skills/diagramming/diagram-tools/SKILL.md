---
name: diagram-tools
description: "Create diagrams: hand-drawn style (Excalidraw) and dark-themed architecture SVG diagrams."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [diagram, architecture, flowchart, SVG, Excalidraw, visualization]
    related_skills: []
---

# Diagram Tools

Create hand-drawn style diagrams (Excalidraw) and dark-themed architecture diagrams (SVG/HTML).

---

## 1. Excalidraw (hand-drawn style diagrams)

Create diagrams by writing standard Excalidraw JSON format and saving as `.excalidraw` files. These files can be opened at excalidraw.com for viewing and editing.

### Workflow

1. Write the elements JSON — an array of Excalidraw element objects
2. Save the file using `write_file` to create a `.excalidraw` file
3. Optionally upload for a shareable link using `scripts/upload.py`

### File Format

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "hermes-agent",
  "elements": [ ...your elements... ],
  "appState": { "viewBackgroundColor": "#ffffff" }
}
```

### Element Types

**Rectangle:**
```json
{ "type": "rectangle", "id": "r1", "x": 100, "y": 100, "width": 200, "height": 100 }
```
- `roundness: { "type": 3 }` for rounded corners
- `backgroundColor: "#a5d8ff"`, `fillStyle: "solid"` for filled

**Text in container (REQUIRED approach):**
```json
{ "type": "rectangle", "id": "r1", "x": 100, "y": 100, "width": 200, "height": 80,
  "boundElements": [{ "id": "t_r1", "type": "text" }],
  "backgroundColor": "#a5d8ff", "fillStyle": "solid",
  "roundness": { "type": 3 } },
{ "type": "text", "id": "t_r1", "x": 105, "y": 110, "width": 190, "height": 25,
  "text": "Hello", "fontSize": 20, "fontFamily": 1, "strokeColor": "#1e1e1e",
  "textAlign": "center", "verticalAlign": "middle",
  "containerId": "r1", "originalText": "Hello", "autoResize": true }
```

**Arrow:**
```json
{ "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 200, "height": 0,
  "points": [[0,0],[200,0]], "endArrowhead": "arrow" }
```

**Arrow with container binding (labels):**
```json
{ "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 200, "height": 0,
  "points": [[0,0],[200,0]], "endArrowhead": "arrow",
  "boundElements": [{ "id": "t_a1", "type": "text" }] },
{ "type": "text", "id": "t_a1", "x": 370, "y": 130, "width": 60, "height": 20,
  "text": "connects", "fontSize": 16, "fontFamily": 1, "containerId": "a1" }
```

### Drawing Order (Z-Order)

Array order = z-order (first = back, last = front). Emit progressively:
- BAD: all rectangles, then all texts, then all arrows
- GOOD: shape → text_for_shape → arrows_from_shape → shape2 → text_for_shape2

### Sizing Guidelines

- Minimum `fontSize`: **16** for body, **20** for titles
- Minimum shape size: 120x60 for labeled rectangles/ellipses
- Leave 20-30px gaps between elements minimum

### Color Palette

| Use | Fill Color | Hex |
|-----|-----------|-----|
| Primary / Input | Light Blue | `#a5d8ff` |
| Success / Output | Light Green | `#b2f2bb` |
| Warning / External | Light Orange | `#ffd8a8` |
| Processing / Special | Light Purple | `#d0bfff` |
| Error / Critical | Light Red | `#ffc9c9` |
| Notes / Decisions | Light Yellow | `#fff3bf` |
| Storage / Data | Light Teal | `#c3fae8` |

### Uploading for Shareable Link

```bash
python ~/.hermes/skills/diagramming/diagram-tools/scripts/upload.py ~/diagrams/my_diagram.excalidraw
```

---

## 2. Architecture Diagrams (dark-themed SVG)

Create dark-themed SVG architecture/cloud/infrastructure diagrams as HTML.

### Approach

Generate self-contained HTML files with inline SVG that produce dark-themed architecture diagrams. These are good for documentation, READMEs, and presentations.

### Key Design Principles

- Dark background (`#1a1a2e` or similar)
- Clear component separation with borders or backgrounds
- Color-coded by component type (services, databases, external APIs)
- Clean typography and spacing
- Exportable as SVG for embedding in docs

### Typical Architecture Diagram Elements

- **Services**: Rounded rectangles with service names
- **Databases**: Cylinder shapes or rectangles with DB icons
- **External APIs**: Dashed outlines or distinct colors
- **Connections**: Arrows with labels
- **Containers/Clusters**: Larger containers grouping related services
