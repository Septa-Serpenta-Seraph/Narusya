---
name: ocr-and-documents
description: Extract text from PDFs and scanned documents. Use web_extract for remote URLs, pymupdf for local text-based PDFs, marker-pdf for OCR/scanned docs. For DOCX use python-docx, for PPTX see the powerpoint skill.
version: 2.3.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [PDF, Documents, Research, Arxiv, Text-Extraction, OCR]
    related_skills: [powerpoint]
---

# PDF & Document Extraction

For DOCX: use `python-docx` (parses actual document structure, far better than OCR).
For PPTX: see the `powerpoint` skill (uses `python-pptx` with full slide/notes support).
This skill covers **PDFs and scanned documents**.

## Step 1: Remote URL Available?

If the document has a URL, **always try `web_extract` first**:

```
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])
web_extract(urls=["https://example.com/report.pdf"])
```

This handles PDF-to-markdown conversion via Firecrawl with no local dependencies.

Only use local extraction when: the file is local, web_extract fails, or you need batch processing.

## Step 2: Choose Local Extractor

| Feature | pymupdf (~25MB) | marker-pdf (~3-5GB) |
|---------|-----------------|---------------------|
| **Text-based PDF** | ✅ | ✅ |
| **Scanned PDF (OCR)** | ❌ | ✅ (90+ languages) |
| **Tables** | ✅ (basic) | ✅ (high accuracy) |
| **Equations / LaTeX** | ❌ | ✅ |
| **Code blocks** | ❌ | ✅ |
| **Forms** | ❌ | ✅ |
| **Headers/footers removal** | ❌ | ✅ |
| **Reading order detection** | ❌ | ✅ |
| **Images extraction** | ✅ (embedded) | ✅ (with context) |
| **Images → text (OCR)** | ❌ | ✅ |
| **EPUB** | ✅ | ✅ |
| **Markdown output** | ✅ (via pymupdf4llm) | ✅ (native, higher quality) |
| **Install size** | ~25MB | ~3-5GB (PyTorch + models) |
| **Speed** | Instant | ~1-14s/page (CPU), ~0.2s/page (GPU) |

**Decision**: Use pymupdf unless you need OCR, equations, forms, or complex layout analysis.

If the user needs marker capabilities but the system lacks ~5GB free disk:
> "This document needs OCR/advanced extraction (marker-pdf), which requires ~5GB for PyTorch and models. Your system has [X]GB free. Options: free up space, provide a URL so I can use web_extract, or I can try pymupdf which works for text-based PDFs but not scanned documents or equations."

---

## pymupdf (lightweight)

```bash
# Try standard install first
pip install pymupdf pymupdf4llm
# If "externally-managed-environment" error occurs:
pip install --break-system-packages pymupdf pymupdf4llm
```
*Note: The `--break-system-packages` flag is often required in the Hermes sandbox due to PEP 668 (externally-managed-environment).*

**Via helper script**:
```bash
python scripts/extract_pymupdf.py document.pdf              # Plain text
python scripts/extract_pymupdf.py document.pdf --markdown    # Markdown
python scripts/extract_pymupdf.py document.pdf --tables      # Tables
python scripts/extract_pymupdf.py document.pdf --images out/ # Extract images
python scripts/extract_pymupdf.py document.pdf --metadata    # Title, author, pages
python scripts/extract_pymupdf.py document.pdf --pages 0-4   # Specific pages
```

**Inline**:
```bash
python3 -c "
import pymupdf
doc = pymupdf.open('document.pdf')
for page in doc:
    print(page.get_text())
"
```

---

## marker-pdf (high-quality OCR)

```bash
# Check disk space first
python scripts/extract_marker.py --check

pip install marker-pdf
```

**Via helper script**:
```bash
python scripts/extract_marker.py document.pdf                # Markdown
python scripts/extract_marker.py document.pdf --json         # JSON with metadata
python scripts/extract_marker.py document.pdf --output_dir out/  # Save images
python scripts/extract_marker.py scanned.pdf                 # Scanned PDF (OCR)
python scripts/extract_marker.py document.pdf --use_llm      # LLM-boosted accuracy
```

**CLI** (installed with marker-pdf):
```bash
marker_single document.pdf --output_dir ./output
marker /path/to/folder --workers 4    # Batch
```

---

## Arxiv Papers

```
# Abstract only (fast)
web_extract(urls=["https://arxiv.org/abs/2402.03300"])

# Full paper
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])

# Search
web_search(query="arxiv GRPO reinforcement learning 2026")
```

## Lightweight OCR Fallback (fitz + tesseract)

When marker-pdf can't be installed (disk space constraints, no sudo), use PyMuPDF to render pages as images and tesseract to OCR each page. Much lighter (~25MB for fitz, tesseract is usually pre-installed).

```bash
# Install (no sudo needed)
uv pip install PyMuPDF
# tesseract is usually already on the system
```

**Script pattern:**
```python
import fitz  # PyMuPDF
import subprocess, tempfile, os

doc = fitz.open("scanned.pdf")
with open("output.txt", "w") as out:
    for i in range(len(doc)):
        page = doc[i]
        mat = fitz.Matrix(200/72, 200/72)  # 200 DPI
        pix = page.get_pixmap(matrix=mat)
        
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            pix.save(tmp.name)
            result = subprocess.run(
                ["tesseract", tmp.name, "stdout", "--psm", "6"],
                capture_output=True, text=True, timeout=30
            )
            os.unlink(tmp.name)
        
        out.write(f"\n=== PAGE {i+1} ===\n{result.stdout}\n")
        if (i + 1) % 10 == 0:
            print(f"Page {i+1}/{len(doc)} done")
```

**Tips:**
- Use `--psm 6` for uniform text blocks (default for most books)
- Use `--psm 3` for fully automatic page segmentation if layout is complex
- 200 DPI is a good balance; 300 DPI for fine print but slower
- Run as background process for large documents (100+ pages)
- For large PDFs (>500MB), memory can spike during page rendering — process in batches if needed

**Speed:** ~2-3 seconds per page at 200 DPI. 200 pages ≈ 10-15 minutes.

## Tesseract Limitations (IMPORTANT)

Tesseract frequently **fails silently** on:
- **Blurry or dark screenshots** — returns empty string or garbled output
- **Tall/narrow mobile screenshots** — Discord DM screenshots (1800x4000+) often fail
- **Text over images** — Discord message text over backgrounds
- **Stylized fonts** — custom fonts, emoji, special characters

**When tesseract fails:**
1. Try `vision_analyze` tool (requires a vision-capable model — currently none free on OpenRouter)
2. Ask user to **copy-paste** the text directly from Discord (highlight messages, Ctrl+C) — this is the MOST RELIABLE fallback. Say: "I can't see the image — vision is broken on this model and OCR can't read it. Can you highlight the messages and copy-paste the text?"
3. User can screenshot smaller sections at higher contrast

**Do NOT** repeatedly retry tesseract on the same image — if it fails once, it will keep failing. Move to an alternative approach immediately.

### vision_analyze 404 Pattern
When `vision_analyze` returns `Error code: 404 - No endpoints found that support image input`, the active model is text-only. This is common with OWL Alpha and most free OpenRouter models. Do NOT retry vision_analyze in the same session — ask user to copy-paste instead.

## Notes

- `web_extract` is always first choice for URLs
- pymupdf is the safe default — instant, no models, works everywhere
- marker-pdf is for OCR, scanned docs, equations, complex layouts — install only when needed
- **fitz + tesseract** is the lightweight OCR fallback when marker can't be installed
- All three helper scripts accept `--help` for full usage
- marker-pdf downloads ~2.5GB of models to `~/.cache/huggingface/` on first use
- For Word docs: `pip install python-docx` (better than OCR — parses actual structure)
- For PowerPoint: see the `powerpoint` skill (uses python-pptx)
