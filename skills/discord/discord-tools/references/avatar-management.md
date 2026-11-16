# Avatar Management (Static + Animated)

Bots can carry animated GIF avatars. Discord enabled this for bot accounts (no Nitro needed). It is set through the same REST API as everything else.

## Set the avatar

`PATCH /users/@me` with a base64 data URI:

```python
import base64, json, urllib.request
gif = open("/path/avatar.gif", "rb").read()
payload = json.dumps({"avatar": "data:image/gif;base64," + base64.b64encode(gif).decode()}).encode()
req = urllib.request.Request(
    "https://discord.com/api/v10/users/@me",
    data=payload, method="PATCH",
    headers={"Authorization": "Bot " + token,
             "Content-Type": "application/json",
             "User-Agent": "DiscordBot (https://discord.com, v10)"},
)
print(urllib.request.urlopen(req, timeout=60).status)  # 200
```

Same token rules as every other call: User-Agent required, token from `/proc/*/environ` or `.env`.

## Verify it took, and that it is animated

- `GET /users/@me` returns the `avatar` hash. An animated avatar hash starts with `a_`; a static one does not.
- Fetch `https://cdn.discordapp.com/avatars/{id}/{hash}.gif?size=256` and check the magic bytes are `GIF89a`. A `.png` fetch also succeeds (Discord keeps a static fallback), so the extension alone proves nothing; check the bytes.

## mp4 to GIF

Discord avatars are PNG or GIF, never mp4. Convert and downsize; a 720p/24fps source otherwise becomes a multi-MB GIF:

```bash
ffmpeg -y -i in.mp4 -vf "fps=10,scale=288:288:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer" out.gif
```

Around 288px at 10fps is a good avatar size; keep the file near or under 2MB.

## Clear or dark background

Avatar art often arrives on a white background. Key it out before uploading; a white box reads badly at 128px.

Transparent (clear):
```bash
ffmpeg -y -i in.mp4 -vf "fps=10,scale=288:288:flags=lanczos,colorkey=0xffffff:0.25:0.05,split[s0][s1];[s0]palettegen=max_colors=128:reserve_transparent=1[p];[s1][p]paletteuse=alpha_threshold=128" -loop 0 out.gif
```

Dark background: overlay the transparent result on a colour source.
```bash
ffmpeg -y -f lavfi -i "color=c=0x0e1a12:s=288x288:r=10:d=5" -i out.gif \
  -filter_complex "[0:v][1:v]overlay=shortest=1:format=auto[out]" -map "[out]" -loop 0 dark.gif
```

## Pitfalls

- **A hard colour key eats bright character details.** Gold hair, jewellery highlights, and eye catchlights sit near white; an aggressive key punches holes in them. Use the lowest similarity that still clears the background, then pixel-check the face region (compare the green-dominant pixel fraction before and after) instead of trusting the filter.
- **Keying leaves a light fringe.** The anti-aliased edge between the character and a white background is part-white; a colour key at a safe similarity leaves those pixels opaque and light, so a transparent avatar shows a pale halo or outline. Fix: erode the alpha by 1-2 px (`ImageFilter.MinFilter(3)` or `(5)` on the alpha channel) and re-read the edge pixels, or raise the key similarity until the fringe goes. Verify by compositing the result on a mid-grey background and reading the edge pixels, not by eye.
- **PIL-only alpha key (no numpy needed).** Compute the per-pixel minimum channel with `ImageChops.darker` twice and ramp it through `.point()`:
  ```python
  r, g, b, a = img.split()
  mn = ImageChops.darker(ImageChops.darker(r, g), b)
  alpha = mn.point(lambda v: 255 - max(0, min(255, int((v - 232) * 255 / 18))))
  img.putalpha(alpha)
  ```
- **GIF transparency is a single palette index.** The transparent index can carry an arbitrary RGB (often `(0,255,0)`); that is normal. The alpha channel is what matters. Read the converted GIF back and confirm corner alpha is 0.
- **Changing the avatar is a visible, account-wide change.** Confirm before switching away from a working avatar, and keep the previous file so it can be restored.
