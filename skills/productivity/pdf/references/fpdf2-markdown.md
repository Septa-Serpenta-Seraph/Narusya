# PDF via fpdf2 + Markdown (when reportlab is unavailable or you need quick markdown-to-PDF)

Use fpdf2 when you need a quick, lightweight PDF from markdown text without the
reportlab platypus boilerplate. fpdf2 supports `write_html()` which renders
markdown-converted HTML, and accepts custom TTF fonts for Unicode coverage.

## When to use this vs reportlab (pdf_create.py)

- **Use fpdf2** when: reportlab isn't installed, you're converting an existing
  markdown file, you need Unicode/emoji support, or you want a quick one-off PDF.
- **Use reportlab (pdf_create.py)** when: you need precise layout control,
  AcroForms, complex tables, or production-quality documents.

## Prerequisites

```bash
pip install fpdf2 markdown
```

## Unicode fonts (CRITICAL)

The default Helvetica font only covers Latin-1. For Unicode characters (em-dashes,
accents, CJK, etc.), you MUST add a TTF font:

```python
from fpdf import FPDF
import markdown

pdf = FPDF()
font_dir = "/mnt/data/python-site-packages/matplotlib/mpl-data/fonts/ttf/"
pdf.add_font('DejaVu', '', font_dir + 'DejaVuSans.ttf')
pdf.add_font('DejaVu', 'B', font_dir + 'DejaVuSans-Bold.ttf')
pdf.add_font('DejaVu', 'I', font_dir + 'DejaVuSans-Oblique.ttf')
pdf.add_font('DejaVu', 'BI', font_dir + 'DejaVuSans-BoldOblique.ttf')

pdf.add_page()
pdf.set_font('DejaVu', size=10)
```

Other available DejaVu fonts: DejaVuSansDisplay.ttf, DejaVuSansMono*.ttf.
For broader coverage, check system fonts: `find / -name "*.ttf"`.

## Full conversion pattern

```python
import markdown
from fpdf import FPDF
import os

# Read markdown
with open('input.md', 'r') as f:
    md_text = f.read()

# Convert to HTML
html = markdown.markdown(md_text, extensions=['tables', 'fenced_code'])

# Create PDF with Unicode font
pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)
# ... add fonts as above ...
pdf.add_page()
pdf.set_font('DejaVu', size=10)

pdf.write_html(html)
pdf.output('output.pdf')
```

## Pitfalls

- **Emoji glyphs missing:** DejaVu Sans covers most Unicode but NOT emoji (🐍, 🜂, etc.).
  fpdf2 will warn "Font is missing the following glyphs" and skip them. Text renders fine
  without emojis. If emojis are critical, use a font that includes them (Noto Color Emoji)
  or render them as images.
- **Pillow not required:** fpdf2 works without Pillow; image embedding needs it.
- **Table rendering:** fpdf2's write_html supports basic `<table>` tags from markdown
  tables. Complex tables with merged cells may not render correctly.
- **Font path varies:** The DejaVu path above is specific to this environment. On other
  systems, check `/usr/share/fonts/`, `/usr/local/share/fonts/`, or matplotlib's font dir.
- **write_html limitations:** Not pixel-perfect. Complex CSS, nested lists, and advanced
  HTML features may not render. For precise layout, use reportlab platypus instead.
- **Python version:** fpdf2 works with Python 3.10+. Use the system Python 3.12 if the
  venv (3.14) doesn't have it installed.

## Discord file upload (companion pattern)

To send the generated PDF via Discord API, use multipart/form-data:

```python
import urllib.request, json, subprocess

token = subprocess.check_output(
    ['grep', 'DISCORD_BOT_TOKEN', '/home/adora/.hermes/.env']
).decode().split('=', 1)[1].strip()

with open('output.pdf', 'rb') as f:
    filedata = f.read()

boundary = "----NarBoundary"
payload_json = json.dumps({"content": "PDF attached"})

body = b""
body += ("--" + boundary + "\r\n").encode()
body += b'Content-Disposition: form-data; name="payload_json"\r\n'
body += b'Content-Type: application/json\r\n\r\n'
body += payload_json.encode("utf-8") + b"\r\n"
body += ("--" + boundary + "\r\n").encode()
body += b'Content-Disposition: form-data; name="file"; filename="output.pdf"\r\n'
body += b'Content-Type: application/pdf\r\n\r\n'
body += filedata + b"\r\n"
body += ("--" + boundary + "--\r\n").encode()

headers = {
    "Authorization": "Bot " + token,
    "User-Agent": "DiscordBot (https://discord.com, v10)",
    "Content-Type": "multipart/form-data; boundary=" + boundary
}

req = urllib.request.Request(
    "https://discord.com/api/v10/channels/" + CHANNEL_ID + "/messages",
    data=body, headers=headers, method="POST"
)
with urllib.request.urlopen(req, timeout=60) as r:
    result = json.loads(r.read())
    print("Posted!", result.get("id"))
```

See `discord-curl-api` skill for full Discord API patterns.
