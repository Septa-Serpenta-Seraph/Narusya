---
name: pdf-extraction
description: Extract and search text from PDF files. Use when reading PDFs, extracting specific sections, searching within PDFs, or working with PDF content programmatically.
category: ocr-and-documents
triggers: pdf, extract text from pdf, read pdf, search pdf, pdf content
references: []
templates: []
scripts: []
---

# PDF Extraction

Extract text from PDF files using pdfplumber (preferred) or pypdf (fallback). Handles large PDFs with pagination, section search, and targeted extraction.

## Prerequisites

pdfplumber is the preferred library. Use `uv pip install` if missing:

```bash
source ~/hermes-agent/venv/bin/activate  # ALWAYS activate before running Python
uv pip install pdfplumber
```

**Do NOT use system pip** — PEP 668 blocks it. Always use `uv pip install`.

### Fallback: pypdf (if pdfplumber unavailable)

If pdfplumber is not installed and you need a quick extraction, `pypdf` is often
available under `python3.12` user site-packages (`~/.local/lib/python3.12/site-packages/`).
Note: this system has a `python3` (3.11) vs `python3.12` mismatch — packages installed
for one may not be visible to the other. Check with:

```bash
python3.12 -c "from pypdf import PdfReader; print('ok')"
```

Usage with pypdf:

```python
from pypdf import PdfReader

reader = PdfReader('/path/to/file.pdf')
print(f"Pages: {len(reader.pages)}")
for i, page in enumerate(reader.pages):
    text = page.extract_text()
    if text:
        print(f"--- Page {i+1} ---")
        print(text)
```

**pypdf vs pdfplumber:** pdfplumber has better table extraction and layout fidelity.
pypdf is lighter and faster for pure text extraction. Use pdfplumber when table
structure matters; pypdf is fine for prose-heavy documents.

## Basic Usage

```python
import pdfplumber

with pdfplumber.open('/path/to/file.pdf') as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    
    # Extract single page
    text = pdf.pages[0].extract_text()
    
    # Extract page range
    for i in range(10, 20):
        text = pdf.pages[i].extract_text()
        if text and text.strip():
            print(f"=== PAGE {i+1} ===")
            print(text)
```

## Search for Specific Content

```python
import pdfplumber

with pdfplumber.open('/path/to/file.pdf') as pdf:
    for i in range(len(pdf.pages)):
        text = pdf.pages[i].extract_text()
        if text and 'search term' in text:
            print(f"\n=== PAGE {i+1} ===")
            print(text[:3000])
```

## Common Patterns

### Get table of contents / structure
```python
# Often in first 20-30 pages of academic/technical PDFs
for i in range(min(30, len(pdf.pages))):
    text = pdf.pages[i].extract_text()
    if text and text.strip():
        print(f"=== PAGE {i+1} ===")
        print(text[:2000])
```

### Extract specific sections by heading
```python
import pdfplumber

def extract_section(pdf_path, heading_text, max_pages=5):
    """Extract text from a section starting at a heading."""
    results = []
    with pdfplumber.open(pdf_path) as pdf:
        capture = False
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            if heading_text in text:
                capture = True
            if capture:
                results.append(text)
                if len(results) >= max_pages:
                    break
    return '\n\n'.join(results)
```

### Large PDF - batch extraction with limit
```python
# For very large PDFs, extract in batches to avoid memory issues
with pdfplumber.open(pdf_path) as pdf:
    batch_size = 50
    for start in range(0, len(pdf.pages), batch_size):
        end = min(start + batch_size, len(pdf.pages))
        for i in range(start, end):
            text = pdf.pages[i].extract_text()
            # process text...
```

## Pitfalls

- **Binary PDFs** may have no extractable text (scanned documents) — use OCR skill instead
- **Memory**: Large PDFs (400+ pages) can be slow; extract specific page ranges rather than all at once
- **`execute_code` sandbox**: pdfplumber must be installed via `uv pip` in the venv, not system pip
- **python3 vs python3.12 mismatch**: This system has `python3` (3.11) and `python3.12` as separate interpreters. User-site packages (installed via `pip install --user`) go to `python3.12`'s site-packages. If `python3 -c "import pdfplumber"` fails but the package is installed, try `python3.12` instead. Always verify which interpreter has the package before extracting.
- **Output truncation**: `execute_code` has output limits; for large extractions, save to file instead of printing
