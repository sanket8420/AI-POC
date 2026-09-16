"""
Fallback extractor for document_type == "unknown".

Runs the same generic regex field-finder used before this feature
existed, so an unrecognized document still yields SOMETHING useful
(a date, an amount, an email) rather than nothing at all.
"""

from typing import Any, Dict

from document_intelligence.field_extractor import extract_fields


def extract(cleaned_text: str, lines_text: str) -> Dict[str, Any]:
    return {
        "document_type": "unknown",
        "generic_fields": extract_fields(cleaned_text),
    }
