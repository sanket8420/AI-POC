"""
Extractor for document_type == "student_records".

Uses the generic table_parser (see table_parser.py / pdf_layout.py) —
NO hardcoded column list. Whatever columns the real table has (Student
ID, Student Name, Grade... or any other school system's naming) come
through as-is via normalize_key(). A pipe-delimited fallback is kept
for text that never came from a real layout-aware PDF extraction.
"""

import re
from typing import Any, Dict, List

from document_intelligence.table_parser import auto_detect_table

LEGACY_ROW_PATTERN = re.compile(
    r"^(?P<student_id>\S+)\s*\|\s*(?P<name>.+?)\s*\|\s*Grade\s*(?P<grade>\S+)\s*\|\s*"
    r"Section\s*(?P<section>\S+)\s*\|\s*(?P<status>\S+)$",
    re.IGNORECASE,
)


def _extract_legacy_pipe_format(lines_text: str) -> List[Dict[str, Any]]:
    records = []
    for line in lines_text.splitlines():
        match = LEGACY_ROW_PATTERN.match(line.strip())
        if match:
            records.append({
                "student_id": match.group("student_id"),
                "student_name": match.group("name"),
                "grade": match.group("grade"),
                "section": match.group("section"),
                "status": match.group("status"),
            })
    return records


def extract(cleaned_text: str, lines_text: str) -> Dict[str, Any]:
    lines = [l for l in lines_text.splitlines() if l.strip()]

    records = auto_detect_table(lines)
    if not records:
        records = _extract_legacy_pipe_format(lines_text)

    return {"document_type": "student_records", "records": records}
