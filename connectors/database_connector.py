"""
DatabaseConnector
=================
Implements BaseConnector for SQL databases (Postgres, MySQL, SQL Server,
SQLite -- anything SQLAlchemy supports via a connection URL).

AUTHENTICATION:
Credentials are NEVER hardcoded or passed as plain constructor arguments
in real use. The connection string is read from the DATABASE_URL
environment variable by default -- e.g.:
    postgresql://user:password@host:5432/dbname
    mysql+pymysql://user:password@host:3306/dbname
In real deployments, that environment variable should be populated from
a secrets manager (AWS Secrets Manager, Azure Key Vault, etc.) or a
.env file that is NOT committed to source control -- never from a
string literal in this file.

If no DATABASE_URL is set (e.g. running this POC with no real database
configured), this connector falls back to a local, credential-free
demo SQLite file so the POC still runs out of the box.

Connect  -> open a SQLAlchemy engine connection (or the local demo DB)
Extract  -> run a query, return rows as a list of dicts
Validate -> standard required-field check (shared with CSV/REST connectors)
Transform-> map into the platform's common AI-ready schema
"""

import os
from typing import Any, Dict, List, Optional

from connectors.base_connector import BaseConnector
from pipeline.validators import split_valid_invalid

DEMO_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "sample_data", "sample_database.db")


class DatabaseConnector(BaseConnector):
    def __init__(
        self,
        table_name: str,
        connection_string: Optional[str] = None,
        query: Optional[str] = None,
        required_fields: List[str] = None,
    ):
        super().__init__(source_name="database")
        self.table_name = table_name
        # NEVER hardcode a real connection string here -- always sourced
        # from the environment, with a credential-free local fallback
        # only for demo purposes.
        self.connection_string = connection_string or os.environ.get("DATABASE_URL")
        self.query = query or f"SELECT * FROM {table_name}"
        self.required_fields = required_fields or []
        self._using_demo_db = False

    def connect(self) -> None:
        if self.connection_string:
            try:
                from sqlalchemy import create_engine
            except ImportError as exc:
                raise ImportError(
                    "SQLAlchemy is required for DatabaseConnector against a "
                    "real database. Install it with: pip install sqlalchemy "
                    "(plus a driver, e.g. psycopg2-binary for Postgres)."
                ) from exc
            self.logger.info("Connecting using DATABASE_URL / provided connection string")
            self._connection = create_engine(self.connection_string)
        else:
            self.logger.info(
                "No DATABASE_URL set -- falling back to local demo SQLite "
                f"database at {DEMO_DB_PATH} (no credentials required)"
            )
            if not os.path.isfile(DEMO_DB_PATH):
                raise FileNotFoundError(f"Demo database not found: {DEMO_DB_PATH}")
            self._using_demo_db = True
            import sqlite3
            self._connection = sqlite3.connect(DEMO_DB_PATH)

    def extract(self) -> List[Dict[str, Any]]:
        if self._using_demo_db:
            self._connection.row_factory = self._sqlite_dict_factory
            cursor = self._connection.execute(self.query)
            rows = cursor.fetchall()
            self._connection.close()
            return rows
        else:
            from sqlalchemy import text
            with self._connection.connect() as conn:
                result = conn.execute(text(self.query))
                rows = [dict(row._mapping) for row in result]
            return rows

    @staticmethod
    def _sqlite_dict_factory(cursor, row):
        fields = [col[0] for col in cursor.description]
        return dict(zip(fields, row))

    def validate(self, raw_records: List[Dict[str, Any]]):
        return split_valid_invalid(raw_records, self.required_fields)

    def transform(self, valid_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        transformed = []
        for i, record in enumerate(valid_records):
            transformed.append({
                "record_id": f"db-{self.table_name}-{i}",
                "source_type": "database",
                "content": record,
                "metadata": {
                    "table_name": self.table_name,
                    "using_demo_db": self._using_demo_db,
                },
            })
        return transformed
