"""
RESTAPIConnector
================
Implements BaseConnector for JSON REST APIs.

Connect  -> create an HTTP session (and validate the URL is reachable)
Extract  -> GET the endpoint and normalize the JSON body into a list of dicts
Validate -> ensure required fields exist per record
Transform-> map into the platform's common AI-ready schema

Note: for demo/offline use (no network), pass `mock_response` to skip the
real HTTP call and use sample data instead — this keeps the POC runnable
in any environment while showing exactly where the real call happens.
"""

from typing import Any, Dict, List, Optional

import requests

from connectors.base_connector import BaseConnector
from pipeline.validators import split_valid_invalid


class RESTAPIConnector(BaseConnector):
    def __init__(
        self,
        url: str,
        required_fields: List[str] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10,
        mock_response: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(source_name="rest_api")
        self.url = url
        self.required_fields = required_fields or []
        self.headers = headers or {}
        self.timeout = timeout
        self.mock_response = mock_response  # used only if provided (offline demo mode)

    def connect(self) -> None:
        self._connection = requests.Session()
        self._connection.headers.update(self.headers)

    def extract(self) -> List[Dict[str, Any]]:
        if self.mock_response is not None:
            self.logger.info("Using mock_response (offline demo mode) instead of a live HTTP call")
            return self.mock_response

        response = self._connection.get(self.url, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()

        # Normalize: APIs return either a raw list, or an object with a
        # nested list under a common key like "data"/"results"/"items".
        if isinstance(payload, list):
            return payload
        for key in ("data", "results", "items"):
            if isinstance(payload.get(key), list):
                return payload[key]
        # Fallback: treat the single JSON object as one record
        return [payload]

    def validate(self, raw_records: List[Dict[str, Any]]):
        return split_valid_invalid(raw_records, self.required_fields)

    def transform(self, valid_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        transformed = []
        for i, record in enumerate(valid_records):
            transformed.append({
                "record_id": f"api-{i}",
                "source_type": "rest_api",
                "content": record,
                "metadata": {
                    "origin_url": self.url,
                },
            })
        return transformed
