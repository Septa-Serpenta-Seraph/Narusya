---
name: playwright-video-record
description: Record headless browser walkthrough videos using Playwright. Perfect for dashboard demos, UI walkthroughs, and hackathon recordings. No OBS/display needed.
tags: [playwright, video, recording, headless, dashboard]
---

# Playwright Video Recording

Record full walkthrough videos of web apps without any display server. Playwright records everything the browser does to a video file.

## Setup
- Playwright must be installed with browsers: `python3 -m playwright install chromium`
- Works headless — no X server, GPU, or display needed

## Quick Start

```python
import asyncio
from playwright.async_api import async_playwright

async def record():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir="./recordings",
            record_video_size={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        # Do your walkthrough
        await page.goto("http://localhost:5000", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        await page.locator("text=Tab Name").click()
        await page.wait_for_timeout(2000)
        
        # Get video before closing context
        video_path = await page.video.path()
        await context.close()
        await browser.close()
        
        # Rename to useful name
        import os
        os.rename(video_path, "./recordings/output.webm")

asyncio.run(record())
```

## Converting to MP4

Playwright outputs `.webm` by default. Convert with ffmpeg:

```bash
ffmpeg -i input.webm -c:v libx264 -preset fast -crf 23 -c:a aac output.mp4 -y
```

## Tips
- Use `page.wait_for_timeout(ms)` to control pacing
- Click tabs/buttons with `page.locator("text=TabName").click()`
- Scroll with `page.evaluate("window.scrollTo(0, 500)")`
- Record at 1920x1080 for best quality

## Used For
- AEGIS Dashboard hackathon video (Scenes 2 & 3)
