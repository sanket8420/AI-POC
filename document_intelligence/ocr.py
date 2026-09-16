"""
OCR extraction for scanned PDF pages and standalone images.

Uses Tesseract (via pytesseract) — open-source, runs entirely offline.
Chosen deliberately over a cloud OCR API (AWS Textract, Azure, Google)
to stay consistent with the no-external-API stance already established
for sensitive documents (see the earlier discussion about the SBI
banking test file).

Requires the `tesseract` binary installed on the system (not just the
pytesseract Python package) — e.g. `apt install tesseract-ocr` or
`brew install tesseract`. This is a real deployment requirement, not
optional — document it in the README.

Uses pytesseract's word-level bounding-box output (image_to_data), fed
into the SAME Y-coordinate clustering used for digital PDF text
(layout_reconstruction.py) — so a scanned table gets the same quality
reconstruction as a real-text-layer table, not a second, weaker path.
"""

from typing import Any

try:
    import pytesseract
    from pytesseract import Output
    _PYTESSERACT_AVAILABLE = True
except ImportError:
    _PYTESSERACT_AVAILABLE = False

from document_intelligence.layout_reconstruction import reconstruct_from_word_boxes


def _require_pytesseract() -> None:
    if not _PYTESSERACT_AVAILABLE:
        raise ImportError(
            "OCR fallback requires pytesseract AND the tesseract binary "
            "itself. Install with: pip install pytesseract pillow, plus "
            "the system binary (e.g. apt install tesseract-ocr on Linux, "
            "brew install tesseract on macOS). This is only needed for "
            "scanned/image-only PDF pages -- pages with a real text layer "
            "work without it."
        )


def ocr_image_to_layout_text(pil_image: Any) -> str:
    """pil_image: a PIL.Image.Image object."""
    _require_pytesseract()
    data = pytesseract.image_to_data(pil_image, output_type=Output.DICT)

    word_boxes = []
    n = len(data["text"])
    for i in range(n):
        text = data["text"][i].strip()
        if not text:
            continue
        x0 = float(data["left"][i])
        y0 = float(data["top"][i])
        x1 = x0 + float(data["width"][i])
        word_boxes.append((x0, y0, x1, y0, text))  # y1 unused by the clustering logic

    return reconstruct_from_word_boxes(word_boxes)


def ocr_pdf_page(fitz_page: Any, zoom: float = 2.0) -> str:
    """
    Renders a PyMuPDF page to an image and OCRs it. zoom=2.0 roughly
    doubles resolution, which meaningfully improves OCR accuracy over
    the default render size.
    """
    import fitz  # local import: only needed when this path is actually used
    from PIL import Image

    matrix = fitz.Matrix(zoom, zoom)
    pixmap = fitz_page.get_pixmap(matrix=matrix)
    image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
    return ocr_image_to_layout_text(image)


def ocr_image_file(path: str) -> str:
    from PIL import Image

    with Image.open(path) as image:
        return ocr_image_to_layout_text(image.convert("RGB"))
