"""
Shared word-position -> layout-preserved-text reconstruction.

This logic was originally written just for PyMuPDF's word output
(pdf_layout.py). It's actually source-agnostic: ANY source that can
give word-level bounding boxes (a digital PDF's text layer, or OCR
output from a scanned page/image) can use the exact same Y-coordinate
clustering to rebuild column-aligned text. Extracting it here means
OCR'd scanned pages get the SAME quality table reconstruction as
regular digital-text PDFs, via ocr.py, instead of a second, weaker
implementation.
"""

from typing import List, Tuple

Y_TOLERANCE = 6.0  # points; words within this y0 range are the same row.
# Was 3.0, tuned against precise digital-PDF coordinates. Real OCR testing
# (pytesseract) showed same-row words can differ by ~4pt in detected top
# position (font rendering/baseline jitter) -- e.g. "Starters" at top=70
# vs. "Paneer"/"280" at top=74 on the same visual row, incorrectly split
# into two rows at the old threshold. 6.0 accommodates that jitter while
# staying far below normal row-to-row spacing (~14pt+ in real documents).

# A "word box" is (x0, y0, x1, y1, text)
WordBox = Tuple[float, float, float, float, str]


def reconstruct_from_word_boxes(word_boxes: List[WordBox]) -> str:
    if not word_boxes:
        return ""

    sorted_words = sorted(word_boxes, key=lambda w: (w[1], w[0]))

    rows: List[List[Tuple[float, float, str]]] = []
    current_row: List[Tuple[float, float, str]] = []
    current_y = None

    for x0, y0, x1, y1, text in sorted_words:
        if current_y is None or abs(y0 - current_y) <= Y_TOLERANCE:
            current_row.append((x0, x1, text))
            if current_y is None:
                current_y = y0
        else:
            rows.append(sorted(current_row, key=lambda t: t[0]))
            current_row = [(x0, x1, text)]
            current_y = y0

    if current_row:
        rows.append(sorted(current_row, key=lambda t: t[0]))

    # Real word-gap data (digital PDF text): normal word-to-word spacing
    # within a cell is ~2-5pt. Real OCR word-gap data: normal spacing is
    # ~7-10pt (larger fonts, pixel-derived coordinates). Column gaps in
    # both sources measured 90pt+. A single threshold safely separates
    # "same cell" from "new column" across both sources -- the earlier
    # gap/4 ratio failed on OCR text specifically, where normal intra-cell
    # word gaps (~9pt) crossed its threshold and falsely split single
    # cell labels like "Product ID" into two cells.
    NORMAL_GAP_THRESHOLD = 20.0

    out_lines = []
    for row in rows:
        line_str = ""
        prev_x1 = None
        for x0, x1, text in row:
            if prev_x1 is None:
                # CRITICAL: use the word's actual absolute x0 to compute
                # leading spaces, not just start at character 0. Without
                # this, every line looks like it starts at the same
                # column regardless of where it really sits on the page
                # -- a real bug found via live testing, where a wrapped
                # continuation line under the "Description" column got
                # matched to the "Item" column instead, since both
                # reconstructed to start at character index 0.
                leading_spaces = max(0, min(int(x0 / 8), 200))
                line_str = (" " * leading_spaces) + text
            else:
                gap = x0 - prev_x1
                if gap < NORMAL_GAP_THRESHOLD:
                    num_spaces = 1
                else:
                    num_spaces = min(max(3, int(gap / 8)), 20)
                line_str += (" " * num_spaces) + text
            prev_x1 = x1
        out_lines.append(line_str)

    return "\n".join(out_lines)
