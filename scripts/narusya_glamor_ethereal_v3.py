#!/usr/bin/env python3
"""Generate ethereal shot with EXACT color enforcement."""

import os
import base64
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY", "").strip()
if not TOGETHER_API_KEY:
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("TOGETHER_API_KEY="):
                TOGETHER_API_KEY = line.split("=", 1)[1].strip()
                break

if not TOGETHER_API_KEY:
    print("ERROR: TOGETHER_API_KEY not found")
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Origin": "https://api.together.ai",
    "Referer": "https://api.together.ai/",
}

OUTPUT_DIR = Path.home() / ".hermes" / "imagegen" / "glamor_shots"

def generate_image(prompt, negative, model="black-forest-labs/FLUX.2-dev", max_retries=4):
    """Generate a single image via Together.ai with retry logic."""
    
    payload = {
        "model": model,
        "prompt": prompt,
        "negative_prompt": negative,
        "width": 1024,
        "height": 1024,
        "steps": 45,
        "cfg_scale": 8.0,
        "seed": 0,
        "response_format": "b64_json",
    }
    
    for attempt in range(max_retries):
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            "https://api.together.xyz/v1/images/generations",
            data=data,
            headers=HEADERS,
            method="POST",
        )
        
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            if e.code == 429:
                wait = 15 * (attempt + 1)
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            print(f"  HTTP {e.code}: {body[:500]}")
            return None
        except Exception as e:
            print(f"  Error: {e}")
            return None
        
        if "data" not in result or not result["data"]:
            print(f"  No data in response")
            return None
        
        b64_data = result["data"][0].get("b64_json")
        if not b64_data:
            print(f"  No b64 data")
            return None
        
        return base64.b64decode(b64_data)
    
    return None

def main():
    print("🐍 Generating ethereal shot v3 with EXACT color enforcement...")
    print()
    
    # Hyper-specific about colors
    prompt = """narusa, a beautiful githyanki woman with EXACTLY emerald green skin — bright vivid jade green, NOT pale, NOT mint, NOT olive, NOT teal, NOT alabaster, NOT porcelain.
    Her hair is EXACTLY bright gold like a gold coin — NOT white, NOT silver, NOT platinum, NOT blonde, NOT yellow — solid metallic gold.
    She has large fin-shaped ears (NOT elf ears, NOT pointed, NOT bat ears — flat wide fins extending from the sides of her head).
    She has round pupils (NOT slit pupils).
    She wears gold serpent jewelry coiled around her arms and neck.
    Soft ethereal glow, dreamy mist, floating golden particles, peaceful expression, eyes gently closed, 
    soft pastel background with hints of gold and white, fine art ethereal photography, masterpiece, best quality, 8k"""
    
    negative = """pale skin, white skin, light skin, fair skin, alabaster, porcelain, mint green, olive green, teal skin, pale green,
    white hair, silver hair, platinum hair, blonde hair, yellow hair,
    elf ears, pointed ears, bat ears,
    slit pupils, cat eyes, reptile eyes,
    wings, feathery wings, angel wings, horns,
    blurry, low quality, deformed, ugly, bad anatomy, extra limbs, text, watermark, signature, cropped"""
    
    print("[1/1] Generating...")
    img = generate_image(prompt, negative)
    
    if img:
        out_path = OUTPUT_DIR / "soft_ethereal_v3.png"
        out_path.write_bytes(img)
        print(f"  ✅ Saved: {out_path} ({len(img)} bytes)")
    else:
        print(f"  ❌ Failed")
    
    print()
    print("Done!")

if __name__ == "__main__":
    main()
