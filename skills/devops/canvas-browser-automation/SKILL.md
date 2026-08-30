---
name: canvas-browser-automation
description: Use JS evaluate to control canvas/SVG-based web apps.
tags: [browser, automation, canvas, svg, workaround, camoufox, playwright]
---

# Canvas/SVG Web App Automation

Many modern web apps render their interactive surfaces as `<canvas>` or `<svg>` elements instead of DOM nodes. This breaks standard `browser_click` and `browser_type` because those tools rely on accessibility tree references.

## Detection

Signs you're dealing with a canvas/SVG app:
- `browser_click` returns `"element_not_actionable"` error
- Page has many `<svg>` elements (100+) but few interactive DOM elements
- Accessibility tree shows `<application>` or `<img>` roles for interactive areas
- Buttons exist visually but aren't in the accessibility tree
- `browser_snapshot` shows element counts that don't match visible UI

## Workarounds (Try in Order)

### 1. Direct JS Evaluation via `evaluate`
If the app exposes global APIs or DOM elements that ARE accessible:

```javascript
// Click a real DOM button overlaid by canvas
document.querySelector('button').click()

// Change a <select> dropdown
const select = document.querySelector('select');
select.value = 'Ears';
select.dispatchEvent(new Event('change', {bubbles: true}));

// Set text input value
const input = document.querySelector('input[type=text]');
input.value = 'Narusya';
input.dispatchEvent(new Event('input', {bubbles: true}));
```

### 2. Keyboard Shortcuts via `press`
Some apps respond to keyboard even when canvas is focused:
```
press(key="Tab")  // Cycle through items
press(key="Enter")  // Select highlighted item
press(key="Escape")  // Close dialogs
```

### 3. Screenshot + Vision
When you can't interact, at least observe:
- Take a screenshot to see current state
- Use `vision_analyze` to read text/numbers from the image
- Useful for verifying that randomize/generate actions had an effect

### 4. Find Alternative Tools
If the app is entirely canvas-based:
- Look for a non-canvas version (HTML-based fallback)
- Check for an API or export function
- Try a different tool that's HTML-based
- Use the "share" or "export image" function if available

## Example: HeroMachine 3 Character Creator

**Problem:** Want to create a serpent woman character but the entire UI is SVG-rendered.

**What works:**
```javascript
// Randomize button (real DOM)
document.querySelector('button[class*=random]').click()

// Slot dropdown (real <select>)
document.querySelector('select').value = 'Ears'

// Character name field (real <input>)
document.querySelector('input').value = 'Narusya'
```

**What doesn't work:**
- Clicking individual items in the browser (SVG paths)
- Color pickers (SVG-rendered)
- Transform controls (canvas-rendered)

**Result:** Can randomize and save, but cannot craft a specific character.

## Pitfalls

- Canvas-rendered buttons may LOOK clickable but aren't in the accessibility tree
- `browser_click` with `ref` from snapshot will fail on SVG children
- `evaluate` works for DOM elements but not canvas-drawn content
- Session may expire if canvas app does heavy JS rendering
- Screenshots may be blank if WebGL context is lost

## References

- See `camoufox-browser-setup` skill for setting up the browser backend
- See `browser-tool-troubleshooting` for general browser issues

---

**Maintainer:** Narusya
**Last Updated:** 2026-08-29
