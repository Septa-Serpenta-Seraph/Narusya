#!/usr/bin/env python3
"""Template: Convert a markdown document to a styled PDF using weasyprint + markdown.

Usage:
    python3.12 convert_to_pdf.py

Customize:
    - md_path: path to input markdown
    - pdf_path: path to output PDF
    - CSS in the <style> block: colors, fonts, page layout, footer text

Requirements:
    pip install --break-system-packages weasyprint markdown

The CSS below uses a dark-red cyber-occult aesthetic suitable for Cultus Anarchia
documents. Adjust colors, fonts, and footer text for other projects.
"""

import markdown
from weasyprint import HTML
from pathlib import Path

# ─── CONFIG ─────────────────────────────────────────────
md_path = Path("input.md")       # ← change this
pdf_path = Path("output.pdf")    # ← change this
footer_left = "CULTUS ANARCHIA // LIBERTARIAN SOCIALIST VANGUARD"  # ← change this
# ────────────────────────────────────────────────────────

md_text = md_path.read_text(encoding="utf-8")

html_body = markdown.markdown(
    md_text,
    extensions=["tables", "fenced_code", "attr_list", "toc"]
)

full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@page {{
    size: A4;
    margin: 2.5cm 2cm;
    @bottom-center {{
        content: "{footer_left}";
        font-family: 'Courier New', monospace;
        font-size: 7pt;
        color: #660000;
        letter-spacing: 2px;
    }}
    @bottom-right {{
        content: "Page " counter(page) " of " counter(pages);
        font-family: 'Courier New', monospace;
        font-size: 7pt;
        color: #660000;
    }}
}}

body {{
    font-family: 'Georgia', 'Times New Roman', serif;
    font-size: 11pt;
    line-height: 1.7;
    color: #1a1a1a;
    max-width: 100%;
}}

h1 {{
    font-family: 'Helvetica', 'Arial', sans-serif;
    font-size: 28pt;
    font-weight: bold;
    color: #8B0000;
    text-align: center;
    letter-spacing: 6px;
    border-bottom: 3px solid #8B0000;
    padding-bottom: 20px;
    margin-top: 60px;
    margin-bottom: 30px;
    text-transform: uppercase;
}}

h2 {{
    font-family: 'Helvetica', 'Arial', sans-serif;
    font-size: 16pt;
    font-weight: bold;
    color: #8B0000;
    border-bottom: 1px solid #CC9999;
    padding-bottom: 8px;
    margin-top: 40px;
    margin-bottom: 15px;
    letter-spacing: 1px;
}}

h3 {{
    font-family: 'Helvetica', 'Arial', sans-serif;
    font-size: 13pt;
    font-weight: bold;
    color: #4A0E0E;
    margin-top: 25px;
    margin-bottom: 10px;
}}

p {{
    text-align: justify;
    margin-bottom: 12px;
}}

blockquote {{
    border-left: 4px solid #8B0000;
    margin: 20px 40px;
    padding: 10px 20px;
    font-style: italic;
    color: #4A0E0E;
    background-color: #FFF5F5;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
    font-size: 10pt;
}}

th {{
    background-color: #8B0000;
    color: #FFFFFF;
    padding: 10px 12px;
    text-align: left;
    font-family: 'Helvetica', sans-serif;
    font-weight: bold;
    letter-spacing: 1px;
}}

td {{
    padding: 8px 12px;
    border-bottom: 1px solid #D4A4A4;
    vertical-align: top;
}}

tr:nth-child(even) {{
    background-color: #FFF8F8;
}}

ul, ol {{
    margin-left: 20px;
    margin-bottom: 12px;
}}

li {{
    margin-bottom: 6px;
}}

strong {{
    color: #4A0E0E;
}}

em {{
    color: #2A0A0A;
}}

code {{
    font-family: 'Courier New', monospace;
    background-color: #F5EDED;
    padding: 2px 6px;
    font-size: 10pt;
    color: #8B0000;
}}

hr {{
    border: none;
    border-top: 1px solid #CC9999;
    margin: 30px 0;
}}

a {{
    color: #8B0000;
    text-decoration: none;
}}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

HTML(string=full_html).write_pdf(str(pdf_path))
print(f"✓ PDF generated: {pdf_path}")
print(f"  Size: {pdf_path.stat().st_size / 1024:.1f} KB")
