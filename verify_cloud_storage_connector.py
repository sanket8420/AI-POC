"""
Standalone verification for CloudStorageConnector against a REAL S3
bucket. The demo-mode path (local folder, no bucket_name) is already
tested by the project's own test suite -- this script is specifically
for confirming the boto3 path, which needs real AWS access to check.

Usage:
    # credentials via env vars, ~/.aws/credentials, or IAM role
    python3 verify_cloud_storage_connector.py <bucket_name> [prefix]
"""
import sys
sys.path.insert(0, ".")
from connectors.cloud_storage_connector import CloudStorageConnector
from pipeline.ingestion_pipeline import IngestionPipeline

if len(sys.argv) < 2:
    print("Usage: python3 verify_cloud_storage_connector.py <bucket_name> [prefix]")
    sys.exit(1)

bucket = sys.argv[1]
prefix = sys.argv[2] if len(sys.argv) > 2 else ""

pipeline = IngestionPipeline()
connector = CloudStorageConnector(bucket_name=bucket, prefix=prefix)
summary = pipeline.run(connector)
print("Status:", summary["status"])
print("Total/Success/Failed:", summary["total_raw_records"], summary["successful_records"], summary["failed_records_count"])
if summary["records"]:
    print("First record:", summary["records"][0])
if summary["errors"]:
    print("Errors:", summary["errors"])
