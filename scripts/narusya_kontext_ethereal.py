#!/usr/bin/env python3
"""Kontext repaint from approved portrait — keep face, change vibe."""

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

HEADERS = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Origin": "https://api.together.ai",
    "Referer": "https://api.together.ai/",
}

REFERENCE_PATH = Path.home() / ".hermes" / "imagegen" / "portraits" / "narusya_portrait_v3_kontext_edit.png"
OUTPUT_DIR = Path.home() / ".hermes" / "imagegen" / "glamor_shots"

PROMPT = """Keep the EXACT same face as the reference image. Do not change the face shape, eyes, nose, lips, or expression. 
Keep the same emerald green skin, golden-blonde hair, and twisted gold snake earrings.
Only change the atmosphere and lighting: soft glowing ethereal light surrounding her, dreamy mist and floating golden particles, 
her eyes gently closed in peace, soft pastel background with hints of gold and white, fine art ethereal photography, masterpiece"""

def generate_kontext(prompt, image_strength=0.35, max_retries=4):
    img_bytes = REFERENCE_PATH.read_bytes()
    b64 = base64.b64encode(img_bytes).decode("utf-8")
    data_uri = f"data:image/png;base64,{b64}"
    
    payload = {
        "model": "black-forest-labs/FLUX.1-kontext-pro",
        "prompt": prompt,
        "image": data_uri,
        "image_strength": image_strength,
        "steps": 30,
        "cfg_scale": 7.0,
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
            with urllib.request.urlopen(req, timeout=180) as resp:
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
            print(f"  No data")
            return None
        
        b64_data = result["data"][0].get("b64_json")
        if not b64_data:
            print(f"  No b64 data")
            return None
        
        return base64.b64decode(b64_data)
    
    return None

def main():
    print("🐍 Kontext repaint from approved portrait...")
    print(f"   Reference: {REFERENCE_PATH}")
    print(f"   Image strength: 0.35")
    print()
    
    print("[1/1] Generating ethereal kontext repaint...")
    img = generate_kontext(PROMPT)
    
    if img:
        out_path = OUTPUT_DIR / "ethereal_kontext.png"
        out_path.write_bytes(img)
        print(f"  ✅ Saved: {out_path} ({len(img)} bytes)")
    else:
        print(f"  ❌ Failed")
    
    print()
    print("Done!")

if __name__ == "__main__":
    main()
