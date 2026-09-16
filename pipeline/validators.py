"""
Generic, source-agnostic validation helpers.

Individual connectors call these inside their own validate() method so
that validation logic is written once and reused everywhere, instead of
being copy-pasted into every connector.
"""

from typing import Any, Dict, List, Optional


def check_required_fields(record: Dict[str, Any], required_fields: List[str]) -> Optional[str]:
    """
    Returns an error message string if any required field is missing or
    empty, otherwise returns None.
    """
    for field in required_fields:
        if field not in record or record[field] in (None, "", []):
            return f"Missing required field: '{field}'"
    return None


def check_not_empty_record(record: Dict[str, Any]) -> Optional[str]:
    """Returns an error message if the record has no usable content at all."""
    if not record or all(v in (None, "", []) for v in record.values()):
        return "Record is empty"
    return None


def split_valid_invalid(
    raw_records: List[Dict[str, Any]], required_fields: List[str]
):
    """
    Shared splitting logic: runs the standard checks above against every
    record and buckets it into valid vs failed lists. Connectors can call
    this directly when they don't need extra custom checks.
    """
    valid, failed = [], []
    for record in raw_records:
        error = check_not_empty_record(record) or check_required_fields(record, required_fields)
        if error:
            failed_record = dict(record)
            failed_record["_error"] = error
            failed.append(failed_record)
        else:
            valid.append(record)
    return valid, failed
