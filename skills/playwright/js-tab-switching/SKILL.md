---
name: js-tab-switching
description: Use JavaScript evaluate to switch tabs instead of click() when CSS overlap issues block pointer events. Works around Tailwind .hidden/.flex conflicts where hidden views still intercept clicks.
tags: [playwright, css, workaround, tabs]
---

# JS Tab Switching Pattern

When Playwright's `page.click()` fails with "subtree intercepts pointer events" — typically caused by hidden `absolute` positioned divs still blocking clicks — use JavaScript to trigger tab switches instead.

## The Problem

When tab views use `absolute inset-0` positioning with `hidden` class toggling:
```html
<div id="vision-view" class="absolute inset-0 ...">
<div id="chat-view" class="absolute inset-0 hidden flex-col">
```

Tailwind's `.hidden` sets `display: none`, but if any inline style or JS sets `display: flex`, the hidden view overlays other content and intercepts pointer events.

Playwright error:
```
TimeoutError: Page.click: Timeout 30000ms exceeded.
  <div id="chat-history">... from <div id="chat-view" ...> subtree intercepts pointer events
```

## The Fix

Instead of clicking the button element, call the tab-switching JavaScript function directly:

```python
# DON'T do this when CSS overlap exists:
page.click("#tab-autonomy")  # May timeout if another view overlaps

# DO this instead:
page.evaluate("switchTab('autonomy')")
page.wait_for_timeout(1000)  # Wait for transition
```

## Helper Function

```python
def switch_tab(page, tab_name):
    """Switch tabs via JavaScript to avoid CSS pointer event blocking."""
    page.evaluate(f"switchTab('{tab_name}')")
    page.wait_for_timeout(1000)
```

## Usage in Recording Scripts

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        record_video_dir="./recordings",
        record_video_size={"width": 1920, "height": 1080}
    )
    page = context.new_page()
    page.goto("http://localhost:5000")
    
    # Navigate tabs via JS
    page.evaluate("switchTab('autonomy')")
    page.wait_for_timeout(3000)
    
    page.evaluate("switchTab('vision')")
    page.wait_for_timeout(2000)
    
    page.evaluate("switchTab('persistence')")
    page.wait_for_timeout(2000)
    
    page.evaluate("switchTab('chat')")
    page.wait_for_timeout(2000)
```

## Prerequisites

The page must have a `switchTab(tab)` JavaScript function defined. For AEGIS Dashboard, this function:
1. Hides all view divs
2. Shows the target view div
3. Updates button highlighting
4. Loads tab-specific data (persistence, autonomy metrics)

## Related Issues

- **AEGIS Dashboard**: Chat-view (`#chat-view`) with `hidden flex-col` class was blocking clicks on tab buttons after supervisor chat response
- **Root cause**: Tailwind's `.hidden` class was being overridden by inline `display: flex` from the chat response rendering

## Used For

- AEGIS Dashboard video recordings (post-fix code review demo)
- Any Playwright automation where `absolute` positioned overlays block clicks
