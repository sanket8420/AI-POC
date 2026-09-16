"""
PyMuPDF-specific word extraction, delegating actual row reconstruction
to layout_reconstruction.py (shared with OCR — see that module).
"""

from typing import Any

from document_intelligence.layout_reconstruction import reconstruct_from_word_boxes


def reconstruct_layout_text(page: Any) -> str:
    """page: a PyMuPDF (fitz) Page object."""
    words = page.get_text("words")  # (x0, y0, x1, y1, text, block_no, line_no, word_no)
    if not words:
        return page.get_text()

    word_boxes = [(w[0], w[1], w[2], w[3], w[4]) for w in words]
    return reconstruct_from_word_boxes(word_boxes)
