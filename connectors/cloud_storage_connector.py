"""
CloudStorageConnector
======================
Implements BaseConnector for cloud object storage (AWS S3 by default;
the same pattern extends to Azure Blob Storage or GCS by swapping the
client library in connect()/extract()).

AUTHENTICATION:
This connector NEVER accepts or stores a raw access key/secret as a
constructor argument. It delegates entirely to boto3's standard
credential resolution chain, in priority order:
    1. Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
       (optionally AWS_SESSION_TOKEN)
    2. The shared credentials file (~/.aws/credentials), optionally
       selecting a named profile via the `aws_profile` argument
    3. An IAM role attached to the compute environment (EC2/ECS/Lambda),
       automatically, with no configuration needed
This is the standard, secure pattern -- credentials live in the
environment or the AWS credential chain, never in source code.

If no bucket_name is given (or boto3 isn't installed), this connector
falls back to a local folder standing in for a "bucket" -- no
credentials needed -- so the POC still runs out of the box.

Connect  -> create a boto3 S3 client (or resolve the local demo folder)
Extract  -> list objects and read each one's RAW BYTES (not decoded --
            decoding is a transform()-time decision based on file type)
Validate -> ensure each file's bytes were actually readable
Transform-> PDFs are opened directly from bytes (no temp file) and run
            through the SAME layout-aware extraction + generic document
            intelligence pipeline as PDFConnector -- one output record
            PER PAGE. JSON/text files are decoded and parsed as before,
            one record per object.

NOTE: an earlier version of this connector decoded every object as
UTF-8 text unconditionally, which for a binary PDF produced garbled
raw bytes as "content" instead of any real extraction -- found via a
live test against two real PDFs uploaded to an S3 bucket.
"""

import json
import os
from typing import Any, Dict, List, Optional

import fitz  # PyMuPDF -- required for the .pdf handling path

from connectors.base_connector import BaseConnector
from document_intelligence.pdf_layout import reconstruct_layout_text
from document_intelligence.page_processor import process_text

DEMO_FOLDER_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                 "sample_data", "cloud_storage_demo")


class CloudStorageConnector(BaseConnector):
    def __init__(
        self,
        bucket_name: Optional[str] = None,
        prefix: str = "",
        aws_profile: Optional[str] = None,
        min_pdf_text_length: int = 20,
    ):
        super().__init__(source_name="cloud_storage")
        self.bucket_name = bucket_name
        self.prefix = prefix
        self.aws_profile = aws_profile  # selects a NAMED profile only -- never a raw key
        self.min_pdf_text_length = min_pdf_text_length
        self._using_local_demo = False

    def connect(self) -> None:
        if self.bucket_name:
            try:
                import boto3
            except ImportError as exc:
                raise ImportError(
                    "boto3 is required for CloudStorageConnector against a "
                    "real S3 bucket. Install it with: pip install boto3"
                ) from exc
            session = boto3.Session(profile_name=self.aws_profile) if self.aws_profile else boto3.Session()
            self.logger.info(
                f"Connecting to S3 bucket '{self.bucket_name}' "
                f"(credentials resolved via boto3's standard chain)"
            )
            self._connection = session.client("s3")
        else:
            self.logger.info(
                f"No bucket_name given -- using local demo folder "
                f"{DEMO_FOLDER_PATH} as a stand-in bucket (no credentials required)"
            )
            if not os.path.isdir(DEMO_FOLDER_PATH):
                raise FileNotFoundError(f"Demo folder not found: {DEMO_FOLDER_PATH}")
            self._using_local_demo = True

    def extract(self) -> List[Dict[str, Any]]:
        objects = []
        if self._using_local_demo:
            for filename in sorted(os.listdir(DEMO_FOLDER_PATH)):
                full_path = os.path.join(DEMO_FOLDER_PATH, filename)
                if not os.path.isfile(full_path):
                    continue
                with open(full_path, "rb") as f:
                    raw_bytes = f.read()
                objects.append({
                    "key": filename,
                    "size_bytes": os.path.getsize(full_path),
                    "raw_bytes": raw_bytes,
                })
        else:
            paginator = self._connection.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=self.prefix):
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    response = self._connection.get_object(Bucket=self.bucket_name, Key=key)
                    raw_bytes = response["Body"].read()
                    objects.append({
                        "key": key,
                        "size_bytes": obj["Size"],
                        "raw_bytes": raw_bytes,
                    })
        return objects

    def validate(self, raw_records: List[Dict[str, Any]]):
        valid, failed = [], []
        for record in raw_records:
            if not record.get("raw_bytes"):
                failed_record = dict(record)
                failed_record["_error"] = f"Object '{record.get('key')}' is empty or unreadable"
                failed.append(failed_record)
            else:
                valid.append(record)
        return valid, failed

    def transform(self, valid_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        transformed = []
        record_counter = 0
        for record in valid_records:
            key = record["key"]
            raw_bytes = record["raw_bytes"]

            if key.lower().endswith(".pdf"):
                transformed.extend(self._transform_pdf(key, raw_bytes))
                continue

            # Non-PDF: decode as text, parse JSON where applicable.
            text_content = raw_bytes.decode("utf-8", errors="replace")
            parsed_content: Any = text_content
            if key.endswith(".json"):
                try:
                    parsed_content = json.loads(text_content)
                except json.JSONDecodeError:
                    parsed_content = text_content  # fall back to raw text

            transformed.append({
                "record_id": f"cloud-{record_counter}",
                "source_type": "cloud_storage",
                "content": parsed_content,
                "metadata": {
                    "bucket_or_folder": self.bucket_name or DEMO_FOLDER_PATH,
                    "key": key,
                    "size_bytes": record["size_bytes"],
                    "using_local_demo": self._using_local_demo,
                },
            })
            record_counter += 1
        return transformed

    def _transform_pdf(self, key: str, raw_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Opens a PDF directly from bytes (no temp file needed) and runs
        the SAME layout-aware extraction + document intelligence used
        by PDFConnector -- one output record per page.
        """
        results = []
        doc = fitz.open(stream=raw_bytes, filetype="pdf")
        for page_number, page in enumerate(doc, start=1):
            text = reconstruct_layout_text(page)
            if len(text.strip()) < self.min_pdf_text_length:
                self.logger.warning(
                    f"'{key}' page {page_number} has insufficient extractable "
                    f"text -- skipping (scanned/image-only pages need OCR, "
                    f"not currently wired into this connector)"
                )
                continue

            processed = process_text(text)
            results.append({
                "record_id": f"cloud-{key}-page-{page_number}",
                "source_type": "cloud_storage",
                "content": processed,
                "metadata": {
                    "bucket_or_folder": self.bucket_name or DEMO_FOLDER_PATH,
                    "key": key,
                    "page_number": page_number,
                    "using_local_demo": self._using_local_demo,
                },
            })
        doc.close()
        return results
