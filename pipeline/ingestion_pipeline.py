"""
IngestionPipeline
==================

This is the CORE of the platform's ingestion layer, and it is 100%
connector-agnostic. It only depends on the BaseConnector contract:

    connector.run() -> {
        "source_name", "records", "raw_record_count",
        "valid_record_count", "failed_records", "errors"
    }

This is why requirement #7 ("new connectors without changing core
pipeline code") holds: adding a connector never requires touching this
file. You just instantiate the new connector and pass it in.
"""

from typing import Any, Dict, List

from connectors.base_connector import BaseConnector
from utils.logger import get_logger

logger = get_logger("pipeline")


class IngestionPipeline:
    def __init__(self):
        self.run_history: List[Dict[str, Any]] = []

    def run(self, connector: BaseConnector) -> Dict[str, Any]:
        """
        Runs a single connector end-to-end and produces a normalized
        ingestion report. This is the method the Streamlit UI calls.
        """
        logger.info(f"=== Starting ingestion run for source: {connector.source_name} ===")

        result = connector.run()

        success_count = result["valid_record_count"]
        failed_count = len(result["failed_records"])
        total = result["raw_record_count"]

        status = "SUCCESS" if not result["errors"] else "FAILED"

        summary = {
            "source_name": result["source_name"],
            "status": status,
            "total_raw_records": total,
            "successful_records": success_count,
            "failed_records_count": failed_count,
            "records": result["records"],           # AI-ready output
            "failed_records": result["failed_records"],
            "errors": result["errors"],
        }

        if status == "SUCCESS":
            logger.info(
                f"Ingestion complete for '{connector.source_name}': "
                f"{success_count} succeeded, {failed_count} failed, out of {total} total"
            )
        else:
            logger.error(f"Ingestion FAILED for '{connector.source_name}': {result['errors']}")

        self.run_history.append(summary)
        return summary
