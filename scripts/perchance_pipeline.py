#!/usr/bin/env python3
"""
Perchance text-to-image API — minimal reverse-engineered pipeline.
Captures access key from the AI Text-to-Image Generator page,
then hits the API directly for free, unlimited, uncensored generation.

Usage: python3 perchance_pipeline.py "your prompt here" [channel]
  channel: 'ai-text-to-image-generator' (default) or 'image-generator-professional'
"""

import asyncio, re, json, sys, os, random, time, urllib.request
from urllib.parse import quote, urlencode
from playwright.async_api import async_playwright

API_GENERATE = "https://image-generation.perchance.org/api/generate"
API_DOWNLOAD = "https://image-generation.perchance.org/api/downloadTemporaryImage"
API_VERIFY = "https://image-generation.perchance.org/api/checkVerificationStatus"
KEY_FILE = os.path.expanduser("~/.cache/perchance_access_key.txt")
os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)

DEFAULT_CHANNEL = "ai-text-to-image-generator"

async def get_fresh_key(max_wait=30):
    """Launch headless browser, navigate to generator, click generate, capture access key."""
    print("[*] Launching headless browser to capture access key...", flush=True)
    captured = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        )
        page = await ctx.new_page()
        page.on("request", lambda req: captured.append(req.url))
        await page.goto("https://perchance.org/ai-text-to-image-generator", wait_until="networkidle")
        await asyncio.sleep(2)
        # Try clicking generate button
        for attempt in range(3):
            try:
                # The generate button might be in an iframe or directly on the page
                btn = await page.query_selector("button#generateButtonEl")
                if not btn:
                    btns = await page.query_selector_all("button")
                    for b in btns:
                        txt = (await b.inner_text()).strip().lower()
                        if "generate" in txt or "✨" in txt:
                            btn = b
                            break
                if btn:
                    await btn.click()
                    print("[*] Clicked generate button", flush=True)
                    break
                else:
                    # Try iframe
                    for frame in page.frames:
                        if "perchance" in frame.url or "text-to-image" in frame.url:
                            btns = await frame.query_selector_all("button")
                            for b in btns:
                                txt = (await b.inner_text()).strip().lower()
                                if "generate" in txt:
                                    await b.click()
                                    print(f"[*] Clicked generate in iframe: {txt}", flush=True)
                                    break
                            break
            except Exception:
                pass
            await asyncio.sleep(2)
        # Wait for API call to appear
        deadline = time.time() + max_wait
        pattern = re.compile(r'userKey=([a-f\d]{64})')
        while time.time() < deadline:
            for url in captured:
                m = pattern.search(url)
                if m:
                    key = m.group(1)
                    print(f"[+] Captured access key: {key[:16]}...{key[-8:]}", flush=True)
                    await browser.close()
                    return key
            await asyncio.sleep(0.5)
        await browser.close()
    raise RuntimeError("Could not capture access key from browser traffic")

def load_key():
    """Load a cached key, check if still valid."""
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE) as f:
            key = f.read().strip()
        if key and len(key) == 64:
            # Check validity using urllib
            try:
                qs = urlencode({'userKey': key, '__cacheBust': random.random()})
                with urllib.request.urlopen(API_VERIFY + '?' + qs, timeout=10) as r:
                    body = r.read().decode()
                    if 'not_verified' not in body:
                        print(f"[+] Cached key valid: {key[:16]}...{key[-8:]}", flush=True)
                        return key
                print("[*] Cached key expired, getting fresh...", flush=True)
            except Exception as e:
                print(f"[*] Cache check failed ({e}), getting fresh...", flush=True)
    return None

def save_key(key):
    with open(KEY_FILE, 'w') as f:
        f.write(key)

def generate(prompt, negative_prompt="", style=None, shape="portrait",
             guidance_scale=7, channel=DEFAULT_CHANNEL, output_dir=None):
    """Generate image via Perchance API. Returns local filename or None."""
    key = load_key()
    if not key:
        key = asyncio.run(get_fresh_key())
        save_key(key)
    
    # Build resolution from shape
    res_map = {"square": "768x768", "portrait": "512x768", "landscape": "768x512"}
    resolution = res_map.get(shape, "512x768")
    
    # Prepare params
    prompt_query = quote(f"'{prompt}")
    neg_query = quote(f"'{negative_prompt}")
    
    params = {
        'prompt': prompt_query,
        'negativePrompt': neg_query,
        'userKey': key,
        '__cache_bust': random.random(),
        'seed': '-1',
        'resolution': resolution,
        'guidanceScale': str(guidance_scale),
        'channel': channel,
        'subChannel': 'public',
        'requestId': random.random(),
    }
    
    param_str = urlencode(params, safe=':%')
    
    print(f"[*] Generating: '{prompt[:60]}...'", flush=True)
    full_url = API_GENERATE + '?' + param_str
    try:
        with urllib.request.urlopen(full_url, timeout=30) as r:
            gen_body = r.read().decode()
    except urllib.error.HTTPError as e:
        gen_body = e.read().decode() if hasattr(e, 'read') else str(e)
    
    if 'invalid_key' in gen_body:
        print("[!] Invalid key, refreshing...", flush=True)
        key = asyncio.run(get_fresh_key())
        save_key(key)
        params['userKey'] = key
        param_str = urlencode(params, safe=':%')
        full_url = API_GENERATE + '?' + param_str
        with urllib.request.urlopen(full_url, timeout=30) as r:
            gen_body = r.read().decode()
    
    try:
        data = json.loads(gen_body)
        image_id = data.get('imageId')
        if not image_id:
            print(f"[!] No imageId in response: {data}", flush=True)
            return None
        print(f"[+] Got imageId: {image_id}", flush=True)
    except json.JSONDecodeError:
        print(f"[!] Bad response: {gen_body[:200]}", flush=True)
        return None
    
    # Wait and download
    for retry in range(5):
        time.sleep(2)
        dl_url = API_DOWNLOAD + '?' + urlencode({'imageId': image_id})
        try:
            with urllib.request.urlopen(dl_url, timeout=30) as r:
                dl_data = r.read()
            if len(dl_data) > 100:  # Likely valid image
                out_dir = output_dir or os.path.expanduser("~/.hermes/perchance_output")
                os.makedirs(out_dir, exist_ok=True)
                filename = f"{out_dir}/perchance_{image_id}.jpeg"
                with open(filename, 'wb') as f:
                    f.write(dl_data)
                print(f"[+] Saved: {filename} ({len(dl_data)} bytes)", flush=True)
                return filename
            else:
                print(f"[*] Image data too small ({len(dl_data)} bytes, attempt {retry+1}/5)...", flush=True)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"[*] Image not ready yet (attempt {retry+1}/5)...", flush=True)
            else:
                print(f"[!] Download error: {e.code}", flush=True)
                break
        except Exception as e:
            print(f"[!] Download failed: {e}", flush=True)
            break
    return None

if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else "a beautiful serpent coiled around an amethyst"
    channel = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_CHANNEL
    result = generate(prompt, channel=channel)
    if result:
        print(f"\nDONE: {result}")
    else:
        print("\nFAILED: could not generate image")