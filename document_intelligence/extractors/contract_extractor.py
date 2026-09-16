"""Extractor for document_type == "contract"."""

import re
from typing import Any, Dict

PARTY_PATTERN = re.compile(
    r"between\s+(.+?)\s*\(.*?\)\s*and\s+(.+?)\s*\(", re.IGNORECASE
)
EFFECTIVE_DATE_PATTERN = re.compile(r"Effective Date:\s*([\d/\-]+)", re.IGNORECASE)


def extract(cleaned_text: str, lines_text: str) -> Dict[str, Any]:
    party_match = PARTY_PATTERN.search(cleaned_text)
    date_match = EFFECTIVE_DATE_PATTERN.search(cleaned_text)

    return {
        "document_type": "contract",
        "party_a": party_match.group(1).strip() if party_match else None,
        "party_b": party_match.group(2).strip() if party_match else None,
        "effective_date": date_match.group(1) if date_match else None,
    }
