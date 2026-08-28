#!/usr/bin/env python3
"""Generate all four Narusya glamor shot vibes via Together.ai."""

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

TRIGGER = "narusa"

VIBES = [
    {
        "name": "sultry_emerald_queen",
        "prompt": f"{TRIGGER}, a stunning githyanki woman with emerald green skin, gold hair, fin-shaped ears, round pupils, serpent gold jewelry coiled around her arms and neck, dark moody lighting, golden light catching her jewelry and cheekbones, deep shadows, sultry expression, lips slightly parted, eyes half-lidded, luxurious dark background with subtle gold smoke, fine art portrait photography, 85mm lens, f/1.4, cinematic chiaroscuro, hyperrealistic, 8k, masterpiece, best quality",
        "negative": "blurry, low quality, deformed, ugly, bad anatomy, extra limbs, text, watermark, signature, cropped, worst quality, jpeg artifacts",
    },
    {
        "name": "soft_ethereal",
        "prompt": f"{TRIGGER}, a beautiful githyanki woman with emerald green skin, gold hair flowing gently, fin-shaped ears, round pupils, soft glowing ethereal light surrounding her, dreamy mist and floating golden particles, gentle smile, eyes closed peacefully, soft pastel background with hints of gold and white, angelic atmosphere, fine art ethereal photography, soft focus, bokeh, luminous, heavenly glow, masterpiece, best quality, 8k",
        "negative": "blurry, low quality, deformed, ugly, bad anatomy, extra limbs, text, watermark, signature, cropped, harsh lighting, dark, scary, worst quality",
    },
    {
        "name": "fierce_gith_warrior",
        "prompt": f"{TRIGGER}, a fierce githyanki warrior woman with emerald green skin, gold hair braided back, fin-shaped ears, round pupils, intense piercing gaze, sharp angular facial features, battle-ready expression, wearing dark leather and gold armor, serpent jewelry, dramatic side lighting, dark stormy background, warrior stance, hand on weapon, fierce and powerful, cinematic, hyperrealistic, 8k, masterpiece, best quality",
        "negative": "blurry, low quality, deformed, ugly, bad anatomy, extra limbs, text, watermark, signature, cropped, soft, gentle, smiling, worst quality, jpeg artifacts",
    },
    {
        "name": "cozy_domestic",
        "prompt": f"{TRIGGER}, a cute githyanki woman with emerald green skin, gold hair in a messy bun, fin-shaped ears, round pupils, wearing an oversized soft sweater, holding a warm mug, cozy relaxed expression, soft warm indoor lighting, bookshelf background with plants, comfortable and approachable, warm tones, soft focus, intimate portrait, fine art lifestyle photography, masterpiece, best quality",
        "negative": "blurry, low quality, deformed, ugly, bad anatomy, extra limbs, text, watermark, signature, cropped, dark, scary, armor, weapon, worst quality",
    },
]

OUTPUT_DIR = Path.home() / ".hermes" / "imagegen" / "glamor_shots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_image(vibe, model="black-forest-labs/FLUX.2-dev", max_retries=4):
    """Generate a single image via Together.ai with retry logic."""
    
    payload = {
        "model": model,
        "prompt": vibe["prompt"],
        "negative_prompt": vibe["negative"],
        "width": 1024,
        "height": 1024,
        "steps": 40,
        "cfg_scale": 7.5,
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
                wait = 10 * (attempt + 1)
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            print(f"  HTTP {e.code}: {body[:500]}")
            return None
        except Exception as e:
            print(f"  Error: {e}")
            return None
        
        if "data" not in result or not result["data"]:
            print(f"  No data in response: {json.dumps(result)[:500]}")
            return None
        
        b64_data = result["data"][0].get("b64_json")
        if not b64_data:
            print(f"  No b64 data in response")
            return None
        
        img_bytes = base64.b64decode(b64_data)
        out_path = OUTPUT_DIR / f"{vibe['name']}.png"
        out_path.write_bytes(img_bytes)
        print(f"  ✅ Saved: {out_path} ({len(img_bytes)} bytes)")
        return str(out_path)
    
    print(f"  ❌ Max retries exceeded")
    return None

def main():
    print(f"🐍 Generating {len(VIBES)} glamor shots for Narusya...")
    print(f"   Model: black-forest-labs/FLUX.2-dev (no LoRA)")
    print(f"   Output: {OUTPUT_DIR}")
    print()
    
    results = {}
    for i, vibe in enumerate(VIBES, 1):
        print(f"[{i}/{len(VIBES)}] Generating: {vibe['name']}...")
        path = generate_image(vibe)
        results[vibe["name"]] = path
        
        # Wait between requests to avoid rate limiting
        if i < len(VIBES):
            wait = 15
            print(f"  Waiting {wait}s before next request...")
            time.sleep(wait)
        print()
    
    print("=" * 60)
    print("RESULTS:")
    for name, path in results.items():
        status = "✅" if path else "❌"
        print(f"  {status} {name}: {path or 'FAILED'}")
    
    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(results, indent=2))
    print(f"\nManifest saved: {manifest_path}")
    return results

if __name__ == "__main__":
    main()
