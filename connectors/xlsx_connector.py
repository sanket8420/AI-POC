"""
XLSXConnector
=============
Implements BaseConnector for Excel files (.xlsx).

Connect  -> open workbook with openpyxl
Extract  -> read the first sheet's rows, using row 1 as headers
Validate -> reuse the shared required-field checks
Transform-> normalize into the common AI-ready schema
"""

import os
from typing import Any, Dict, List

import openpyxl

from connectors.base_connector import BaseConnector
from pipeline.validators import split_valid_invalid
from document_intelligence.table_parser import normalize_key


class XLSXConnector(BaseConnector):
    def __init__(self, file_path: str, required_fields: List[str] = None, sheet_name: str = None):
        super().__init__(source_name="xlsx")
        self.file_path = file_path
        self.required_fields = required_fields or []
        self.sheet_name = sheet_name

    def connect(self) -> None:
        if not os.path.isfile(self.file_path):
            raise FileNotFoundError(f"XLSX file not found: {self.file_path}")
        self._connection = openpyxl.load_workbook(self.file_path, data_only=True)

    def extract(self) -> List[Dict[str, Any]]:
        sheet = (
            self._connection[self.sheet_name]
            if self.sheet_name
            else self._connection.active
        )
        rows_iter = sheet.iter_rows(values_only=True)
        try:
            header_row = next(rows_iter)
        except StopIteration:
            return []

        headers = [normalize_key(str(h)) if h is not None else f"col_{i}" for i, h in enumerate(header_row)]
        records = []
        for row in rows_iter:
            if all(v is None for v in row):
                continue
            record = {headers[i]: row[i] for i in range(min(len(headers), len(row)))}
            records.append(record)
        return records

    def validate(self, raw_records: List[Dict[str, Any]]):
        return split_valid_invalid(raw_records, self.required_fields)

    def transform(self, valid_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        transformed = []
        for i, record in enumerate(valid_records):
            transformed.append({
                "record_id": f"xlsx-{i}",
                "source_type": "xlsx",
                "content": {k: (str(v) if v is not None else None) for k, v in record.items()},
                "metadata": {
                    "origin_file": os.path.basename(self.file_path),
                    "sheet_name": self.sheet_name or "active",
                },
            })
        return transformed
