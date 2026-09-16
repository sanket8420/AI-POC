"""
ImageConnector
==============
Implements BaseConnector for standalone image files (.jpg, .png) —
e.g. a photographed receipt, a screenshot of a table, a scanned form
saved as an image rather than a PDF.

Connect  -> verify the file exists and opens as an image
Extract  -> OCR the whole image (Tesseract, offline — see document_intelligence/ocr.py)
Validate -> ensure OCR actually produced usable text
Transform-> shared classify + extract pipeline (document_intelligence/page_processor.py)
"""

import os
from typing import Any, Dict, List

from connectors.base_connector import BaseConnector
from document_intelligence.ocr import ocr_image_file
from document_intelligence.page_processor import process_text


class ImageConnector(BaseConnector):
    def __init__(self, file_path: str, min_text_length: int = 5):
        super().__init__(source_name="image")
        self.file_path = file_path
        self.min_text_length = min_text_length

    def connect(self) -> None:
        if not os.path.isfile(self.file_path):
            raise FileNotFoundError(f"Image file not found: {self.file_path}")

    def extract(self) -> List[Dict[str, Any]]:
        text = ocr_image_file(self.file_path)
        return [{"raw_text": text}]

    def validate(self, raw_records: List[Dict[str, Any]]):
        valid, failed = [], []
        for record in raw_records:
            text = (record.get("raw_text") or "").strip()
            if len(text) < self.min_text_length:
                failed_record = dict(record)
                failed_record["_error"] = "OCR produced insufficient text from this image"
                failed.append(failed_record)
            else:
                valid.append(record)
        return valid, failed

    def transform(self, valid_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        transformed = []
        for i, record in enumerate(valid_records):
            processed = process_text(record["raw_text"])
            transformed.append({
                "record_id": f"image-{i}",
                "source_type": "image",
                "content": processed,
                "metadata": {"origin_file": os.path.basename(self.file_path)},
            })
        return transformed
