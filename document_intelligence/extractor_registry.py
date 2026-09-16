"""
Extractor registry
===================

This is the piece that makes the pipeline generic instead of an
if/elif chain per document type. `get_extractor()` looks up which
function should handle a given document_type; PDFConnector.transform()
never needs to know the list of supported types itself.

TO ADD A NEW DOCUMENT TYPE:
    1. Write document_intelligence/extractors/my_type_extractor.py
       with an extract(cleaned_text, lines_text) -> dict function.
    2. Add its keywords to classifier.py's CATEGORY_KEYWORDS.
    3. Add its required fields to schemas.py's REQUIRED_FIELDS_BY_TYPE.
    4. Register it in EXTRACTOR_REGISTRY below.
No other file changes needed — PDFConnector, the pipeline, and the UI
all stay exactly as they are.
"""

from typing import Any, Callable, Dict

from document_intelligence.extractors import (
    invoice_extractor,
    contract_extractor,
    restaurant_menu_extractor,
    student_record_extractor,
    policy_report_extractor,
    resume_extractor,
    unknown_extractor,
)

ExtractorFn = Callable[[str, str], Dict[str, Any]]

EXTRACTOR_REGISTRY: Dict[str, ExtractorFn] = {
    "invoice": invoice_extractor.extract,
    "contract": contract_extractor.extract,
    "restaurant_menu": restaurant_menu_extractor.extract,
    "student_records": student_record_extractor.extract,
    "policy_report": policy_report_extractor.extract,
    "resume": resume_extractor.extract,
}


def get_extractor(document_type: str) -> ExtractorFn:
    """Falls back to the generic unknown-document extractor if the type isn't registered."""
    return EXTRACTOR_REGISTRY.get(document_type, unknown_extractor.extract)
