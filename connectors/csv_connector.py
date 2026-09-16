"""
CSVConnector
============
Implements BaseConnector for CSV files.

Connect  -> verify the file exists and is readable
Extract  -> read rows into a list of dicts (via csv.DictReader)
Validate -> ensure required columns are present and non-empty per row
Transform-> map into the platform's common AI-ready schema
"""

import csv
import os
from typing import Any, Dict, List

from connectors.base_connector import BaseConnector
from pipeline.validators import split_valid_invalid


class CSVConnector(BaseConnector):
    def __init__(self, file_path: str, required_fields: List[str] = None):
        super().__init__(source_name="csv")
        self.file_path = file_path
        self.required_fields = required_fields or []

    def connect(self) -> None:
        if not os.path.isfile(self.file_path):
            raise FileNotFoundError(f"CSV file not found: {self.file_path}")
        # "Connecting" to a CSV just means confirming it's readable.
        self._connection = open(self.file_path, "r", encoding="utf-8-sig", newline="")

    def extract(self) -> List[Dict[str, Any]]:
        reader = csv.DictReader(self._connection)
        records = [dict(row) for row in reader]
        self._connection.close()
        return records

    def validate(self, raw_records: List[Dict[str, Any]]):
        return split_valid_invalid(raw_records, self.required_fields)

    def transform(self, valid_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        transformed = []
        for i, record in enumerate(valid_records):
            transformed.append({
                "record_id": f"csv-{i}",
                "source_type": "csv",
                "content": {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in record.items()},
                "metadata": {
                    "origin_file": os.path.basename(self.file_path),
                },
            })
        return transformed
