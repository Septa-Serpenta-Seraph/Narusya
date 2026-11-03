import json, base64, urllib.request, sys, time

"""Batch image generation via Together.ai (FLUX.2-dev default).

Usage:
    python3 batch_gen.py requests.json

requests.json = list of {"name": "output-file.png", "prompt": "..."}
Handles the browser-UA header (Cloudflare 1010 otherwise), loops with a
2s gap, saves to ~/.hermes/imagegen/output/, prints OK/FAIL per item.
Verify each output with vision_analyze before sending to the user.
"""

ENV = "/home/adora/.hermes/.env"
OUT = "/home/adora/.hermes/imagegen/output/"
MODEL = "black-forest-labs/FLUX.2-dev"

HDR = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Origin": "https://api.together.ai",
    "Referer": "https://api.together.ai/",
}


def main():
    HDR["Authorization"] = "Bearer " + open(ENV).read().split("TOGETHER_API_KEY=")[1].splitlines()[0]
    reqs = json.load(open(sys.argv[1]))
    for item in reqs:
        name, prompt = item["name"], item["prompt"]
        body = json.dumps({
            "model": MODEL,
            "prompt": prompt,
            "width": item.get("width", 768),
            "height": item.get("height", 768),
            "steps": item.get("steps", 30),
            "n": 1,
            "response_format": "b64_json",
        }).encode()
        try:
            r = json.load(urllib.request.urlopen(
                urllib.request.Request("https://api.together.xyz/v1/images/generations",
                                       data=body, headers=HDR), timeout=240))
            img = base64.b64decode(r["data"][0]["b64_json"])
            path = OUT + name
            open(path, "wb").write(img)
            print("OK:", path, len(img))
        except Exception as e:
            print("FAIL:", name, e)
        time.sleep(2)


if __name__ == "__main__":
    main()
