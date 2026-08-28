#!/usr/bin/env python3
"""Use Camoufox to upload image to free AI vision services."""

import asyncio
import base64
import os
from pathlib import Path

ENGINE = os.path.expanduser("~/.cache/camoufox/camoufox-bin")
IMG_PATH = Path.home() / "Downloads" / "narusya-play-hour.png"

async def main():
    from playwright.async_api import async_playwright
    from camoufox.async_api import AsyncCamoufox

    print("[*] Launching Camoufox...", flush=True)
    async with async_playwright() as p:
        async with AsyncCamoufox(headless=True, executable_path=ENGINE,
                                 args=["--no-sandbox"]) as browser:
            page = await browser.new_page()
            await page.set_viewport_size({"width": 1920, "height": 1080})

            # Try a free AI chat with vision
            services = [
                "https://www.perplexity.ai/",
                "https://claude.ai/",
                "https://gemini.google.com/",
                "https://chat.mistral.ai/",
            ]

            for service in services:
                print(f"[*] Trying {service}...", flush=True)
                await page.goto(service, wait_until="load", timeout=60000)
                await page.wait_for_timeout(5000)

                # Take screenshot
                screenshot_path = Path.home() / ".hermes" / "cache" / f"camoufox_{service.split('/')[2].split('.')[0]}.png"
                await page.screenshot(path=str(screenshot_path))

                # Check for login
                login_button = page.locator('button:has-text("Log in"), button:has-text("Sign in"), a:has-text("Log in")')
                login_count = await login_button.count()

                # Check for file upload
                file_inputs = page.locator('input[type="file"]')
                file_count = await file_inputs.count()

                print(f"  Login buttons: {login_count}, File inputs: {file_count}", flush=True)

                if file_count > 0 and login_count == 0:
                    print(f"  [*] Uploading image to {service}...", flush=True)
                    await file_inputs.first.set_input_files(str(IMG_PATH))
                    await page.wait_for_timeout(15000)

                    # Take screenshot of result
                    result_path = Path.home() / ".hermes" / "cache" / f"camoufox_{service.split('/')[2].split('.')[0]}_result.png"
                    await page.screenshot(path=str(result_path))
                    print(f"  [*] Result screenshot: {result_path}", flush=True)

                    # Get text
                    text = await page.inner_text("body")
                    print(f"  [*] Text: {text[:300]}")
                    break
                else:
                    print(f"  [!] Skipping (login required or no file input)")

if __name__ == "__main__":
    asyncio.run(main())
