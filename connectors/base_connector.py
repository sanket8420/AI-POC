"""
BaseConnector
=============

This is the single contract that EVERY data source connector must follow.

Design intent (for the architecture review):
    - The pipeline never talks to CSV/REST/PDF specifics. It only talks to
      this interface. That is what lets us add a new source (e.g. SFTP,
      S3, a database) later WITHOUT touching pipeline code.
    - The four-stage flow (Connect -> Extract -> Validate -> Transform) is
      enforced by the `run()` template method below, which is NOT meant to
      be overridden by subclasses. Subclasses only fill in the four steps.
    - `run()` always returns the same shape of result, so the pipeline and
      the UI can treat every connector identically:

        {
            "source_name": str,
            "records": List[dict],          # AI-ready, validated records
            "raw_record_count": int,
            "valid_record_count": int,
            "failed_records": List[dict],   # records that failed validation
            "errors": List[str],
        }
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from utils.logger import get_logger


class BaseConnector(ABC):
    """Abstract interface that all connectors must implement."""

    def __init__(self, source_name: str):
        self.source_name = source_name
        self.logger = get_logger(f"connector.{source_name}")
        self._connection: Any = None

    # ------------------------------------------------------------------ #
    # The four stages every connector MUST implement
    # ------------------------------------------------------------------ #

    @abstractmethod
    def connect(self) -> None:
        """
        Establish access to the source (open a file handle, create an
        HTTP session, open a PDF document, etc). Should raise a clear
        exception if the source is unreachable.
        """
        raise NotImplementedError

    @abstractmethod
    def extract(self) -> List[Dict[str, Any]]:
        """
        Pull raw data out of the source and return it as a list of plain
        dictionaries. No cleaning/validation happens here yet.
        """
        raise NotImplementedError

    @abstractmethod
    def validate(self, raw_records: List[Dict[str, Any]]) -> (List[Dict[str, Any]], List[Dict[str, Any]]):
        """
        Split raw records into (valid_records, failed_records).
        Each failed record should be a dict that includes the original
        data plus a "_error" key describing why it failed.
        """
        raise NotImplementedError

    @abstractmethod
    def transform(self, valid_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize valid records into the platform's common AI-ready
        structure (see pipeline/ingestion_pipeline.py for the target
        schema). This is where source-specific fields get mapped to
        common field names.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------ #
    # Template method — DO NOT override in subclasses
    # ------------------------------------------------------------------ #

    def run(self) -> Dict[str, Any]:
        """
        Executes the standardized Connect -> Extract -> Validate ->
        Transform flow and returns a uniform result dict, regardless of
        the underlying source type.
        """
        errors: List[str] = []
        valid_records: List[Dict[str, Any]] = []
        failed_records: List[Dict[str, Any]] = []
        raw_records: List[Dict[str, Any]] = []

        try:
            self.logger.info("Stage 1/4: connect()")
            self.connect()

            self.logger.info("Stage 2/4: extract()")
            raw_records = self.extract()
            self.logger.info(f"Extracted {len(raw_records)} raw record(s)")

            self.logger.info("Stage 3/4: validate()")
            valid_records, failed_records = self.validate(raw_records)
            self.logger.info(
                f"Validation complete: {len(valid_records)} valid, "
                f"{len(failed_records)} failed"
            )

            self.logger.info("Stage 4/4: transform()")
            valid_records = self.transform(valid_records)

        except Exception as exc:
            self.logger.exception(f"Connector '{self.source_name}' failed")
            errors.append(str(exc))

        return {
            "source_name": self.source_name,
            "records": valid_records,
            "raw_record_count": len(raw_records),
            "valid_record_count": len(valid_records),
            "failed_records": failed_records,
            "errors": errors,
        }
