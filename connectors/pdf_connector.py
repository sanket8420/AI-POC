"""
PDFConnector
============
Implements BaseConnector for PDF documents, and demonstrates the
Document Intelligence responsibilities end-to-end:

Connect  -> open the PDF with PyMuPDF (fitz)
Extract  -> pull raw text per page
Validate -> ensure meaningful text was actually extracted (reject blank/scanned PDFs)
Transform-> clean text -> classify document TYPE (informational label only) ->
            ALWAYS attempt generic, schema-free item extraction (table detection,
            then price-anchored prose detection, then raw text) -> structured JSON

NOTE: classification no longer gates extraction. Earlier versions routed each
page to a hardcoded per-type extractor via a registry, so any document type
the classifier hadn't seen before (a new business domain) fell to "unknown"
and never even attempted table extraction, even when a perfectly good table
was right there. Now every page always tries to find structure, regardless
of what label the classifier guesses -- there is no required schema and no
document-type-specific field list.
"""

import os
from typing import Any, Dict, List

import fitz  # PyMuPDF

from connectors.base_connector import BaseConnector
from document_intelligence.pdf_layout import reconstruct_layout_text
from document_intelligence.ocr import ocr_pdf_page
from document_intelligence.page_processor import process_text


class PDFConnector(BaseConnector):
    def __init__(self, file_path: str, min_text_length: int = 20):
        super().__init__(source_name="pdf")
        self.file_path = file_path
        self.min_text_length = min_text_length

    def connect(self) -> None:
        if not os.path.isfile(self.file_path):
            raise FileNotFoundError(f"PDF file not found: {self.file_path}")
        self._connection = fitz.open(self.file_path)

    def extract(self) -> List[Dict[str, Any]]:
        """
        For a PDF, one "raw record" = one page of raw extracted text.
        Uses layout-preserving extraction (word positions, not plain
        reading-order text) so tables reconstruct correctly regardless
        of column count or labels — see document_intelligence/pdf_layout.py
        for why this replaced plain page.get_text().

        Pages with little to no extractable text (scanned/image-only
        pages, no real text layer) fall back to OCR (see
        document_intelligence/ocr.py) rather than being treated as
        empty. OCR uses the SAME layout-reconstruction logic as digital
        text, so scanned tables get equivalent treatment.
        """
        pages = []
        for page_number, page in enumerate(self._connection, start=1):
            text = reconstruct_layout_text(page)
            used_ocr = False

            if len(text.strip()) < self.min_text_length:
                try:
                    ocr_text = ocr_pdf_page(page)
                    if len(ocr_text.strip()) > len(text.strip()):
                        text = ocr_text
                        used_ocr = True
                except Exception as exc:
                    self.logger.warning(
                        f"OCR fallback failed for page {page_number}: {exc}"
                    )

            pages.append({
                "page_number": page_number,
                "raw_text": text,
                "used_ocr": used_ocr,
            })
        self._connection.close()
        return pages

    def validate(self, raw_records: List[Dict[str, Any]]):
        valid, failed = [], []
        for record in raw_records:
            text = (record.get("raw_text") or "").strip()
            if len(text) < self.min_text_length:
                failed_record = dict(record)
                failed_record["_error"] = (
                    f"Page {record.get('page_number')} has insufficient extractable "
                    f"text, even after an OCR fallback attempt — likely a blank page "
                    f"or an image OCR couldn't read"
                )
                failed.append(failed_record)
            else:
                valid.append(record)
        return valid, failed

    def transform(self, valid_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        transformed = []
        for record in valid_records:
            processed = process_text(record["raw_text"])
            transformed.append({
                "record_id": f"pdf-page-{record['page_number']}",
                "source_type": "pdf",
                "content": processed,
                "metadata": {
                    "origin_file": os.path.basename(self.file_path),
                    "page_number": record["page_number"],
                    "used_ocr": record.get("used_ocr", False),
                },
            })
        return transformed
