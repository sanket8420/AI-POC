"""
Standalone verification for DatabaseConnector against a REAL database.
The demo-mode path (local SQLite, no DATABASE_URL) is already tested by
the project's own test suite -- this script is specifically for
confirming the SQLAlchemy path, which needs a real connection to check.

Usage:
    export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
    python3 verify_database_connector.py <table_name>
"""
import sys
sys.path.insert(0, ".")
from connectors.database_connector import DatabaseConnector
from pipeline.ingestion_pipeline import IngestionPipeline

if len(sys.argv) != 2:
    print("Usage: python3 verify_database_connector.py <table_name>")
    sys.exit(1)

pipeline = IngestionPipeline()
connector = DatabaseConnector(table_name=sys.argv[1])
summary = pipeline.run(connector)
print("Status:", summary["status"])
print("Total/Success/Failed:", summary["total_raw_records"], summary["successful_records"], summary["failed_records_count"])
if summary["records"]:
    print("First record:", summary["records"][0])
if summary["errors"]:
    print("Errors:", summary["errors"])
