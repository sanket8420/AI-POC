"""
Text cleaning for raw text pulled out of PDFs by PyMuPDF.

PyMuPDF extraction is generally clean, but real-world PDFs still produce:
    - repeated whitespace / line breaks from column layouts
    - stray control characters
    - hyphenated line-wraps ("invoi-\\nce" -> "invoice")
    - leading/trailing junk whitespace

This module keeps that cleanup logic in ONE place so both the PDF
connector and any future document-based connector (e.g. DOCX, scanned
OCR output) can reuse it.
"""

import re


def clean_text(raw_text: str) -> str:
    """Cleans raw PDF-extracted text into a normalized, model-ready string."""
    if not raw_text:
        return ""

    text = raw_text

    # Remove non-printable / control characters (keep newlines for now)
    text = re.sub(r"[^\x20-\x7E\n]", " ", text)

    # Fix hyphenated line-wraps: "exam-\nple" -> "example"
    text = re.sub(r"-\n", "", text)

    # Collapse remaining newlines into spaces
    text = text.replace("\n", " ")

    # Collapse multiple spaces/tabs into a single space
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def clean_text_lines(raw_text: str) -> str:
    """
    Same cleanup as clean_text(), but PRESERVES line breaks AND internal
    multi-space runs.

    clean_text() collapses everything to one line and normalizes all
    whitespace to single spaces, which is fine for classification and
    single-value regex extraction (invoices, contracts) but destroys
    BOTH the row structure AND the column-alignment spacing that
    table_parser.auto_detect_table() depends on to tell columns apart
    (see pdf_layout.py — columns are distinguished by runs of 2+
    spaces). Use this variant for any extractor reading tabular or
    line-structured content.
    """
    if not raw_text:
        return ""

    text = raw_text
    text = re.sub(r"[^\x20-\x7E\n]", " ", text)
    text = re.sub(r"-\n", "", text)          # fix hyphenated line-wraps
    text = text.replace("\t", " ")           # normalize tabs only, NOT spaces
    text = re.sub(r"\n{2,}", "\n", text)     # collapse repeated blank lines

    lines = [line.rstrip() for line in text.split("\n")]  # trim trailing only — leading/internal spacing matters for column detection
    lines = [line for line in lines if line.strip()]       # drop lines that are blank once trimmed
    return "\n".join(lines)
