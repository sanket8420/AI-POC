"""
Lightweight, explainable field extraction using regular expressions.

For the POC we extract a handful of high-value, commonly-needed fields.
In a production system this function is the natural place to later plug
in a Named Entity Recognition model or an LLM extraction call — the rest
of the pipeline doesn't care how fields are extracted, only that this
function returns a flat dict.
"""

import re
from typing import Dict, Optional

DATE_PATTERN = r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b"
AMOUNT_PATTERN = r"(?:USD|\$)\s?[\d,]+\.\d{2}"
EMAIL_PATTERN = r"[\w.+-]+@[\w-]+\.[\w.-]+"
# Requires an explicit "number"/"no"/"#" marker AND a value containing at
# least one digit, so we don't accidentally match a document title like
# a standalone "INVOICE" heading.
INVOICE_NUMBER_PATTERN = r"invoice\s*(?:number|no\.?|#)\s*[:\-]?\s*([A-Z0-9\-]*\d[A-Z0-9\-]*)"


def _first_match(pattern: str, text: str, flags=re.IGNORECASE) -> Optional[str]:
    match = re.search(pattern, text, flags)
    return match.group(1) if match and match.groups() else (match.group(0) if match else None)


def extract_fields(text: str) -> Dict[str, Optional[str]]:
    """Extracts a small set of commonly useful fields from document text."""
    if not text:
        return {}

    return {
        "date_found": _first_match(DATE_PATTERN, text),
        "amount_found": _first_match(AMOUNT_PATTERN, text),
        "email_found": _first_match(EMAIL_PATTERN, text),
        "invoice_number": _first_match(INVOICE_NUMBER_PATTERN, text),
    }
