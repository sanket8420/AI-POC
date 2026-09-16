"""Extractor for document_type == "resume"."""

from typing import Any, Dict

from document_intelligence.field_extractor import extract_fields


def extract(cleaned_text: str, lines_text: str) -> Dict[str, Any]:
    base = extract_fields(cleaned_text)
    lines = lines_text.splitlines()
    name = lines[0] if lines else None

    return {
        "document_type": "resume",
        "name": name,
        "email": base.get("email_found"),
    }
