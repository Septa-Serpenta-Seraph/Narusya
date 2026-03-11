---
name: discord-vision
description: Fetches the most recent image from the current Discord channel (including Webhook embeds) and analyzes it using vision.
usage: |
  call check_discord_image() to see what was just posted.
  Requires DISCORD_TOKEN in workspace/AEGIS-Dashboard/.env
---

# Discord Vision Skill

## Implementation
```python
from hermes_tools import terminal, vision_analyze, read_file

def check_discord_image():
    # 1. Run the fetch script to get the URL
    result = terminal(
        "workspace/AEGIS-Dashboard/venv/bin/python workspace/AEGIS-Dashboard/fetch_last_image.py"
    )
    
    output = result.get('output', '').strip()
    
    # 2. Check for errors
    if "Error" in output or not output.startswith("http"):
        return f"Could not fetch image. Output: {output}"
        
    image_url = output.split('\n')[-1].strip()
    
    # 3. Analyze
    print(f"Analyzing Image: {image_url}")
    analysis = vision_analyze(
        image_url=image_url,
        question="Describe this image in detail. Does it look like a successful scan result?"
    )
    return analysis
```
