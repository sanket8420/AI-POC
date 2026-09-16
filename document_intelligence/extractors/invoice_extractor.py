"""
Extractor for document_type == "invoice".

Every extractor in this package follows the same signature:
    extract(cleaned_text: str, lines_text: str) -> dict

so the extractor_registry can call any of them interchangeably.
"""

import re
from typing import Any, Dict

from document_intelligence.field_extractor import extract_fields


def extract(cleaned_text: str, lines_text: str) -> Dict[str, Any]:
    base = extract_fields(cleaned_text)  # reuses date/amount/invoice_number regexes

    vendor = None
    for line in lines_text.splitlines():
        if line.strip().lower().startswith("bill to"):
            vendor = line.split(":", 1)[1].strip() if ":" in line else None
            break

    return {
        "document_type": "invoice",
        "invoice_number": base.get("invoice_number"),
        "vendor": vendor,
        "date": base.get("date_found"),
        "amount": base.get("amount_found"),
    }
