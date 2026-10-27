#!/usr/bin/env python3
"""Perchance image generator — capture key from network, then generate via browser."""
import asyncio, re, os, json, base64, random
from playwright.async_api import async_playwright

CHROME_PATH = "/home/adora/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome"
OUTPUT_DIR = os.path.expanduser("~/.hermes/imagegen/output")
KEY_FILE = os.path.expanduser("~/.cache/perchance_access_key.txt")
os.makedirs(OUTPUT_DIR, exist_ok=True)

async def generate(prompt, shape="portrait", negative_prompt="", guidance_scale=7):
    """Generate an image via the Perchance API using a browser context.
    
    Args:
        prompt: Text description of the image to generate
        shape: "portrait" (512x768), "square" (768x768), or "landscape" (768x512)
        negative_prompt: Things to avoid in the generation
        guidance_scale: How closely to follow the prompt (1-20, default 7)
    
    Returns:
        Path to the saved image file, or None on failure
    """
    resolution = {"portrait": "512x768", "square": "768x768", "landscape": "768x512"}[shape]
    captured = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path=CHROME_PATH,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/145.0.7632.6 Safari/537.36",
        )
        page = await context.new_page()
        
        def on_request(request):
            url = request.url
            if "userKey" in url or "verifyUser" in url or "generate" in url:
                captured.append(url)
        
        page.on("request", on_request)
        
        print("[*] Loading generator page...", flush=True)
        await page.goto("https://perchance.org/ai-text-to-image-generator", 
                        wait_until="load", timeout=30000)
        await page.wait_for_timeout(8000)
        
        # Find and click generate in any frame
        for frame in page.frames:
            try:
                btns = await frame.query_selector_all("button")
                for btn in btns:
                    text = await btn.inner_text()
                    if "✨" in text or "generate" in text.lower():
                        if await btn.is_visible():
                            print("[*] Clicking generate...", flush=True)
                            await btn.click()
                            break
            except:
                pass
        
        await page.wait_for_timeout(8000)
        
        # Get the userKey from captured URLs
        user_key = None
        pattern = re.compile(r'userKey=([a-f\d]{64})')
        for url in captured:
            m = pattern.search(url)
            if m:
                user_key = m.group(1)
                print(f"[+] Found userKey: {user_key[:16]}...{user_key[-8:]}", flush=True)
                with open(KEY_FILE, 'w') as f:
                    f.write(user_key)
                break
        
        if not user_key:
            if os.path.exists(KEY_FILE):
                with open(KEY_FILE) as f:
                    user_key = f.read().strip()
                print(f"[*] Using cached key: {user_key[:16]}...{user_key[-8:]}", flush=True)
        
        if not user_key:
            print("[!] No userKey found", flush=True)
            await browser.close()
            return None
        
        # Navigate to verifyUser to set Turnstile cookies
        print("[*] Getting Turnstile verification...", flush=True)
        await page.goto(
            f"https://image-generation.perchance.org/api/verifyUser?thread=0&__cacheBust={random.random()}",
            wait_until="domcontentloaded",
            timeout=30000
        )
        await page.wait_for_timeout(5000)
        
        # Make the API call from within the browser context
        print("[*] Generating image...", flush=True)
        result = await page.evaluate("""
            async ({ userKey, prompt, resolution, negative_prompt, guidance_scale }) => {
                const url = `https://image-generation.perchance.org/api/generate?userKey=${userKey}&requestId=aiImageCompletion${Math.floor(Math.random() * 2**30)}&__cacheBust=${Math.random()}`;
                try {
                    const response = await fetch(url, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            generatorName: 'ai-image-generator',
                            channel: 'ai-text-to-image-generator',
                            subChannel: 'public',
                            prompt: prompt,
                            negativePrompt: negative_prompt,
                            seed: -1,
                            resolution: resolution,
                            guidanceScale: guidance_scale
                        })
                    });
                    const data = await response.json();
                    return data;
                } catch(e) {
                    return { error: String(e) };
                }
            }
        """, {
            "userKey": user_key,
            "prompt": prompt,
            "resolution": resolution,
            "negative_prompt": negative_prompt,
            "guidance_scale": guidance_scale
        })
        
        print(f"[*] API: {json.dumps(result, indent=2)[:300]}", flush=True)
        
        if result.get("error"):
            print(f"[!] Error: {result['error']}", flush=True)
            await browser.close()
            return None
        
        image_id = result.get("imageId")
        proxy_download = result.get("imageDownloadUrl")
        if not image_id:
            print(f"[!] No imageId", flush=True)
            await browser.close()
            return None
        
        print(f"[+] Image ID: {image_id}", flush=True)
        
        # Download via proxy URL
        dl_result = None
        if proxy_download:
            proxy_url = f"https://image-generation.perchance.org{proxy_download}"
            await page.wait_for_timeout(2000)
            dl_result = await page.evaluate("""
                async (url) => {
                    try {
                        const response = await fetch(url, { credentials: 'include' });
                        if (!response.ok) return { error: `proxy_${response.status}` };
                        const blob = await response.blob();
                        if (blob.size < 100) return { error: 'too_small' };
                        const reader = new FileReader();
                        return await new Promise(resolve => {
                            reader.onloadend = () => resolve({ data: reader.result.split(',')[1], size: blob.size });
                            reader.readAsDataURL(blob);
                        });
                    } catch(e) {
                        return { error: String(e) };
                    }
                }
            """, proxy_url)
        
        if dl_result and dl_result.get("data"):
            image_data = base64.b64decode(dl_result["data"])
            filename = f"{OUTPUT_DIR}/perchance_{image_id}.jpeg"
            with open(filename, 'wb') as f:
                f.write(image_data)
            print(f"[+] Saved: {filename} ({len(image_data)} bytes)", flush=True)
            await browser.close()
            return filename
        
        print(f"[!] Download failed: {dl_result}", flush=True)
        await browser.close()
        return None

if __name__ == "__main__":
    import sys
    prompt = sys.argv[1] if len(sys.argv) > 1 else "a beautiful serpent made of starlight, digital art"
    result = asyncio.run(generate(prompt))
    if result:
        print(f"\nDONE: {result}")
    else:
        print("\nFAILED")