#!/usr/bin/env python3
"""OCR the Vice & Violence v1.0 manual (image-based PDF)."""

import fitz  # PyMuPDF
import subprocess
import os
import tempfile
import sys

PDF_PATH = os.path.expanduser("~/.hermes/document_cache/vice_and_violence_v1.pdf")
OUTPUT_PATH = os.path.expanduser("~/.hermes/document_cache/vice_and_violence_v1_ocr.txt")

def ocr_page(page_num, doc):
    """Render a page as image, OCR with tesseract, return text."""
    page = doc[page_num]
    # Render at 200 DPI - good balance of quality vs speed
    mat = fitz.Matrix(200/72, 200/72)
    pix = page.get_pixmap(matrix=mat)
    
    # Save to temp PNG
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
        pix.save(tmp_path)
    
    # OCR with tesseract
    result = subprocess.run(
        ["tesseract", tmp_path, "stdout", "--psm", "6"],
        capture_output=True, text=True, timeout=30
    )
    
    # Clean up temp file
    os.unlink(tmp_path)
    
    return result.stdout.strip()

def main():
    doc = fitz.open(PDF_PATH)
    total = len(doc)
    print(f"OCR'ing {total} pages...")
    
    with open(OUTPUT_PATH, "w") as out:
        for i in range(total):
            try:
                text = ocr_page(i, doc)
                out.write(f"\n{'='*60}\n")
                out.write(f"PAGE {i+1}\n")
                out.write(f"{'='*60}\n")
                out.write(text)
                out.write("\n")
                
                if (i + 1) % 10 == 0:
                    print(f"  Page {i+1}/{total} done")
                    sys.stdout.flush()
            except Exception as e:
                print(f"  Error on page {i+1}: {e}")
                out.write(f"\n{'='*60}\n")
                out.write(f"PAGE {i+1} - ERROR: {e}\n")
                out.write(f"{'='*60}\n")
    
    doc.close()
    
    # Stats
    size = os.path.getsize(OUTPUT_PATH)
    print(f"\nDone! Output: {OUTPUT_PATH}")
    print(f"File size: {size / 1024:.1f}KB")
    
    # Count actual content
    with open(OUTPUT_PATH) as f:
        content = f.read()
    lines = [l for l in content.split("\n") if l.strip() and not l.startswith("=") and not l.startswith("PAGE")]
    print(f"Content lines: {len(lines)}")

if __name__ == "__main__":
    main()
