"""
Document schemas
=================

This is the single source of truth for "what fields matter for this
document type." It doesn't enforce structure by itself — it just lists
which keys an extractor's output must include for a page to be
considered fully valid. document_validator.py reads this table.

Adding a new document type: add one entry here, plus one extractor
function registered in extractor_registry.py. Nothing else changes.
"""

from typing import Dict, List

REQUIRED_FIELDS_BY_TYPE: Dict[str, List[str]] = {
    "invoice": ["invoice_number", "vendor", "date", "amount"],
    "contract": ["party_a", "party_b", "effective_date"],
    "restaurant_menu": ["restaurant_name", "categories"],
    "student_records": ["records"],
    "policy_report": ["title"],
    "resume": [],   # kept lenient — resumes vary too much for hard requirements
    "unknown": [],  # nothing is "required" for an unrecognized document
}
