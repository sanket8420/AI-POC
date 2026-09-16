"""Extractor for document_type == "policy_report" (merges policy documents and reports)."""

from typing import Any, Dict

from document_intelligence.field_extractor import extract_fields


def extract(cleaned_text: str, lines_text: str) -> Dict[str, Any]:
    base = extract_fields(cleaned_text)
    lines = lines_text.splitlines()
    title = lines[0] if lines else None

    return {
        "document_type": "policy_report",
        "title": title,
        "date_found": base.get("date_found"),
    }
