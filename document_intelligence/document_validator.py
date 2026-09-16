"""
Validates an extractor's output against the required fields for its
document type (see schemas.py). This is a SEPARATE concern from
BaseConnector.validate() (which only checks whether a page had enough
raw text to bother processing at all) — this checks whether the
STRUCTURED extraction actually produced what that document type needs.
"""

from typing import Any, Dict, List, Tuple

from document_intelligence.schemas import REQUIRED_FIELDS_BY_TYPE


def validate_extracted(document_type: str, extracted: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Returns (is_valid, errors). A field counts as missing if it's absent
    OR present but empty (None, "", [], {}).
    """
    required_fields = REQUIRED_FIELDS_BY_TYPE.get(document_type, [])
    errors = []

    for field in required_fields:
        value = extracted.get(field)
        if value in (None, "", [], {}):
            errors.append(f"Missing or empty required field: '{field}'")

    return (len(errors) == 0, errors)
