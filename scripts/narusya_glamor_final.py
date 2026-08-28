#!/usr/bin/env python3
"""Generate final four Narusya glamor shots with refined face-first template."""

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

OUTPUT_DIR = Path.home() / ".hermes" / "imagegen" / "glamor_shots"

FACE_TEMPLATE = """A close-up portrait of a githyanki woman. Her face is the most important part, describe it first: heart-shaped face with high cheekbones, bright amber-orange eyes with vertical slit pupils, a small delicate upturned nose, full lips curved in a subtle knowing smile — calm, serene, mysterious. Her ears are long elegant points, slightly finned at the edges. Her skin is smooth vivid emerald green with subtle iridescent violet scale shimmer only on her temples, cheekbones, and sides of her neck. Her hair is golden-blonde, center-parted, falling past her shoulders in soft waves. She wears long twisted gold snake earrings that dangle past her jawline. Around her neck and arms are gold serpents coiled, detailed with scales."""

VIBES = [
    {
        "name": "ethereal_final",
        "suffix": "She is surrounded by soft glowing ethereal light, dreamy mist and floating golden particles, her eyes are gently closed in peace, soft pastel background with hints of gold and white, fine art ethereal photography, masterpiece",
    },
    {
        "name": "sultry_final",
        "suffix": "She is in a dark moody setting, golden light catching her jewelry and cheekbones, deep shadows, sultry expression, lips slightly parted, eyes half-lidded, luxurious dark background with subtle gold smoke, fine art portrait photography, 85mm lens, cinematic chiaroscuro, masterpiece",
    },
    {
        "name": "warrior_final",
        "suffix": "She is a fierce warrior, battle-ready expression, intense gaze, wearing dark leather and gold armor, serpent jewelry, dramatic side lighting, dark stormy background, warrior stance, hand on weapon, fierce and powerful, cinematic, masterpiece",
    },
    {
        "name": "cozy_final",
        "suffix": "She is cozy at home, wearing an oversized soft sweater, holding a warm mug, soft warm indoor lighting, bookshelf background with plants, comfortable and approachable, warm tones, intimate portrait, masterpiece",
    },
]

def generate_image(prompt, max_retries=4):
    """Generate a single image via Together.ai FLUX.2-dev with retry logic."""
    model = "black-forest-labs/FLUX.2-dev"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "negative_prompt": "blurry, low quality, deformed, ugly, bad anatomy, extra limbs, text, watermark, signature, cropped, worst quality, jpeg artifacts, pale skin, white skin, elf ears, bat ears, round pupils, horns, wings",
        "width": 1024,
        "height": 1024,
        "steps": 45,
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
    print("🐍 Generating FINAL four glamor shots with refined template...")
    print(f"   Face: heart-shaped, amber slit pupils, emerald skin, violet shimmer")
    print(f"   Model: black-forest-labs/FLUX.2-dev (Together.ai)")
    print(f"   Output: {OUTPUT_DIR}")
    print()
    
    results = {}
    for i, vibe in enumerate(VIBES, 1):
        prompt = f"{FACE_TEMPLATE} {vibe['suffix']}"
        print(f"[{i}/{len(VIBES)}] Generating: {vibe['name']}...")
        img = generate_image(prompt)
        
        if img:
            out_path = OUTPUT_DIR / f"{vibe['name']}.png"
            out_path.write_bytes(img)
            print(f"  ✅ Saved: {out_path} ({len(img)} bytes)")
            results[vibe["name"]] = str(out_path)
        else:
            print(f"  ❌ Failed")
            results[vibe["name"]] = None
        
        if i < len(VIBES):
            wait = 15
            print(f"  Waiting {wait}s...")
            time.sleep(wait)
        print()
    
    print("=" * 60)
    print("RESULTS:")
    for name, path in results.items():
        status = "✅" if path else "❌"
        print(f"  {status} {name}: {path or 'FAILED'}")
    
    manifest_path = OUTPUT_DIR / "manifest_final.json"
    manifest_path.write_text(json.dumps(results, indent=2))
    print(f"\nManifest saved: {manifest_path}")
    return results

if __name__ == "__main__":
    main()
