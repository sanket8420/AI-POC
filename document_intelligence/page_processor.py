"""
Shared classify + extract pipeline, used by any connector that produces
plain text from a page/document (PDF pages, OCR'd images, DOCX prose).
Keeping this in one place means PDFConnector, ImageConnector, and
DocxConnector all get identical, consistent Document Intelligence
behavior instead of three separate implementations.
"""

from typing import Any, Dict

from document_intelligence.text_cleaner import clean_text, clean_text_lines
from document_intelligence.classifier import classify_document
from document_intelligence.generic_extractor import extract as generic_extract


def process_text(raw_text: str) -> Dict[str, Any]:
    cleaned = clean_text(raw_text)
    lines_text = clean_text_lines(raw_text)

    document_type, confidence = classify_document(cleaned)
    extraction = generic_extract(cleaned, lines_text)

    result = {
        "cleaned_text": cleaned,
        "document_type_guess": document_type,
        "classification_confidence": confidence,
        "extraction_method": extraction["extraction_method"],
        "item_count": extraction["item_count"],
        "items": extraction["items"],
    }
    # Present only for genuinely unstructured prose (see generic_extractor's
    # "prose_stats" path) -- not every extraction result has these.
    for optional_key in ("entities_found", "word_count", "sentence_count"):
        if optional_key in extraction:
            result[optional_key] = extraction[optional_key]
    return result
