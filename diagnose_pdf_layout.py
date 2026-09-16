"""
Standalone diagnostic — does NOT touch the app. Run this directly to
see exactly what your real PyMuPDF install produces, so the actual fix
can be based on real evidence instead of another guess.

Usage:
    python3 diagnose_pdf_layout.py <path_to_pdf> <page_number>

Example:
    python3 diagnose_pdf_layout.py sample_data/synthetic_restaurant_document_10_pages.pdf 3
"""

import sys

import fitz

from document_intelligence.pdf_layout import reconstruct_layout_text
from document_intelligence.table_parser import auto_detect_table, split_row


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 diagnose_pdf_layout.py <path_to_pdf> <page_number>")
        sys.exit(1)

    path = sys.argv[1]
    page_num = int(sys.argv[2])

    print(f"PyMuPDF (fitz) version: {fitz.__doc__}")
    print()

    doc = fitz.open(path)
    page = doc[page_num - 1]

    words = page.get_text("words")
    print(f"=== Raw word count on page {page_num}: {len(words)} ===")
    print("First 15 word tuples (x0, y0, x1, y1, text, block_no, line_no, word_no):")
    for w in words[:15]:
        print(" ", w)
    print()

    layout_text = reconstruct_layout_text(page)
    print("=== reconstruct_layout_text() output (first 20 lines) ===")
    for line in layout_text.splitlines()[:20]:
        print(repr(line))  # repr() shows exact spacing, including how many spaces
    print()

    lines = [l for l in layout_text.splitlines() if l.strip()]
    print("=== split_row() on each of the first 10 non-empty lines ===")
    for line in lines[:10]:
        print(f"  {len(split_row(line))} cells: {split_row(line)}")
    print()

    rows = auto_detect_table(lines)
    print(f"=== auto_detect_table() result: {len(rows)} rows ===")
    if rows:
        print("First row:", rows[0])

    doc.close()


if __name__ == "__main__":
    main()
