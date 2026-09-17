"""
Streamlit Dashboard — Enterprise AI Data Integration POC
=========================================================

This file is intentionally "thin": it only wires up the UI and calls into
the pipeline / connectors. All business logic lives in connectors/ and
pipeline/, so this file stays simple and easy to walk through live.
"""

import json
import os
import tempfile

import pandas as pd
import streamlit as st

from connectors.csv_connector import CSVConnector
from connectors.rest_api_connector import RESTAPIConnector
from connectors.pdf_connector import PDFConnector
from connectors.database_connector import DatabaseConnector
from connectors.cloud_storage_connector import CloudStorageConnector
from pipeline.ingestion_pipeline import IngestionPipeline

SAMPLE_CSV = os.path.join("sample_data", "sample_customers.csv")
SAMPLE_PDF = os.path.join("sample_data", "sample_invoice.pdf")

st.set_page_config(page_title="Enterprise AI Data Integration POC", layout="wide")

st.title("🔌 Enterprise AI Data Integration — POC BY SANKET JADHAV")
st.caption(
    "Data Sources → Ingestion & Connector Layer → Document Intelligence → AI-ready data"
)

pipeline = IngestionPipeline()

# --------------------------------------------------------------------- #
# Sidebar: source selection
# --------------------------------------------------------------------- #
st.sidebar.header("1. Select a Data Source")
source_type = st.sidebar.radio(
    "Connector type",
    options=["CSV", "REST API", "PDF Document", "Database", "Cloud Storage (S3)"],
)

connector = None

if source_type == "CSV":
    st.sidebar.write("Uses `BaseConnector` → `CSVConnector`")
    uploaded_csv = st.sidebar.file_uploader("Upload a CSV (optional)", type=["csv"])
    required_fields = st.sidebar.text_input(
        "Required fields (comma-separated)", value="customer_id,name,email"
    )
    required_fields_list = [f.strip() for f in required_fields.split(",") if f.strip()]

    if uploaded_csv is not None:
        tmp_path = os.path.join(tempfile.gettempdir(), uploaded_csv.name)
        with open(tmp_path, "wb") as f:
            f.write(uploaded_csv.getbuffer())
        csv_path = tmp_path
    else:
        st.sidebar.info(f"No file uploaded — using sample: `{SAMPLE_CSV}`")
        csv_path = SAMPLE_CSV

    connector = CSVConnector(file_path=csv_path, required_fields=required_fields_list)

elif source_type == "REST API":
    st.sidebar.write("Uses `BaseConnector` → `RESTAPIConnector`")
    api_url = st.sidebar.text_input(
        "API URL", value="https://jsonplaceholder.typicode.com/users"
    )
    required_fields = st.sidebar.text_input(
        "Required fields (comma-separated)", value="id,name,email"
    )
    required_fields_list = [f.strip() for f in required_fields.split(",") if f.strip()]
    offline_demo = st.sidebar.checkbox("Offline demo mode (no live HTTP call)", value=False)

    mock_response = None
    if offline_demo:
        mock_response = [
            {"id": 1, "name": "Jane Doe", "email": "jane@example.com"},
            {"id": 2, "name": "John Smith", "email": ""},  # will fail validation
            {"id": 3, "name": "Priya Sharma", "email": "priya@example.com"},
        ]

    connector = RESTAPIConnector(
        url=api_url, required_fields=required_fields_list, mock_response=mock_response
    )

elif source_type == "PDF Document":
    st.sidebar.write("Uses `BaseConnector` → `PDFConnector` → Document Intelligence")
    uploaded_pdf = st.sidebar.file_uploader("Upload a PDF (optional)", type=["pdf"])

    if uploaded_pdf is not None:
        tmp_path = os.path.join(tempfile.gettempdir(), uploaded_pdf.name)
        with open(tmp_path, "wb") as f:
            f.write(uploaded_pdf.getbuffer())
        pdf_path = tmp_path
    else:
        st.sidebar.info(f"No file uploaded — using sample: `{SAMPLE_PDF}`")
        pdf_path = SAMPLE_PDF

    connector = PDFConnector(file_path=pdf_path)

elif source_type == "Database":
    st.sidebar.write("Uses `BaseConnector` → `DatabaseConnector`")
    st.sidebar.caption(
        "Leave the connection string blank to use a local, credential-free "
        "demo SQLite database. To connect to a real database, set the "
        "**DATABASE_URL environment variable** before launching this app — "
        "never paste real credentials into this text box. The SQLAlchemy "
        "path (Postgres/MySQL/etc.) is unverified in this build environment "
        "(no network to install SQLAlchemy) — test with "
        "`verify_database_connector.py` before relying on it."
    )
    table_name = st.sidebar.text_input("Table name", value="customers")
    required_fields = st.sidebar.text_input(
        "Required fields (comma-separated)", value="customer_id,name,email"
    )
    required_fields_list = [f.strip() for f in required_fields.split(",") if f.strip()]

    connector = DatabaseConnector(table_name=table_name, required_fields=required_fields_list)

elif source_type == "Cloud Storage (S3)":
    st.sidebar.write("Uses `BaseConnector` → `CloudStorageConnector`")
    st.sidebar.caption(
        "Leave the bucket name blank to use a local folder as a stand-in "
        "bucket (no credentials required). Real S3 access uses **boto3's "
        "standard credential chain** (environment variables, "
        "~/.aws/credentials, or an IAM role) — never enter a raw access key "
        "here. The live S3 path is unverified in this build environment (no "
        "network access) — test with `verify_cloud_storage_connector.py` "
        "before relying on it."
    )
    use_real_bucket = st.sidebar.checkbox("Connect to a real S3 bucket", value=False)

    if use_real_bucket:
        bucket = st.sidebar.text_input("Bucket name")
        prefix = st.sidebar.text_input("Key prefix (optional)", value="")
        aws_profile = st.sidebar.text_input("Named AWS profile (optional)", value="")
        connector = CloudStorageConnector(
            bucket_name=bucket or None,
            prefix=prefix,
            aws_profile=aws_profile or None,
        )
    else:
        st.sidebar.info("Using local demo folder as a stand-in bucket — no credentials needed.")
        connector = CloudStorageConnector()

# --------------------------------------------------------------------- #
# Main panel: run + results
# --------------------------------------------------------------------- #
st.sidebar.header("2. Run Ingestion")
run_clicked = st.sidebar.button("▶ Run Connector", type="primary")

if run_clicked and connector is not None:
    with st.spinner(f"Running {source_type} connector through the ingestion pipeline..."):
        summary = pipeline.run(connector)

    st.session_state["last_summary"] = summary

summary = st.session_state.get("last_summary")

if summary is None:
    st.info("Select a source in the sidebar and click **Run Connector** to begin.")
else:
    status_color = "🟢" if summary["status"] == "SUCCESS" else "🔴"
    st.subheader(f"{status_color} Ingestion Status: {summary['status']}  —  source: `{summary['source_name']}`")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Raw Records", summary["total_raw_records"])
    col2.metric("✅ Successful Records", summary["successful_records"])
    col3.metric("❌ Failed Records", summary["failed_records_count"])

    if summary["errors"]:
        st.error("Connector-level errors:\n\n" + "\n".join(summary["errors"]))

    is_doc_intel_run = summary["source_name"] == "pdf"
    tab_labels = ["AI-Ready Data", "Failed Records", "Raw JSON"]
    if is_doc_intel_run:
        tab_labels.append("Document Intelligence View")
    tabs = st.tabs(tab_labels)
    tab1, tab2, tab3 = tabs[0], tabs[1], tabs[2]
    tab4 = tabs[3] if is_doc_intel_run else None

    with tab1:
        if summary["records"]:
            # Flatten for a friendly table view; full structure still
            # available in the "Raw JSON" tab.
            flat_rows = []
            for r in summary["records"]:
                row = {"record_id": r["record_id"], "source_type": r["source_type"]}
                if isinstance(r["content"], dict):
                    for k, v in r["content"].items():
                        row[k] = v if not isinstance(v, dict) else json.dumps(v)
                flat_rows.append(row)
            st.dataframe(pd.DataFrame(flat_rows), use_container_width=True)
        else:
            st.warning("No successful AI-ready records produced.")

    with tab2:
        if summary["failed_records"]:
            st.dataframe(pd.DataFrame(summary["failed_records"]), use_container_width=True)
        else:
            st.success("No failed records 🎉")

    with tab3:
        st.json(summary["records"])

    if tab4 is not None:
        with tab4:
            st.caption(
                "Per-page breakdown: extraction is schema-free — every page is "
                "attempted regardless of document type. Table detection runs "
                "first, then a price-anchored fallback for prose listings."
            )
            for r in summary["records"]:
                content = r["content"]
                meta = r["metadata"]
                doc_type_guess = content.get("document_type_guess", "unknown")
                confidence = content.get("classification_confidence", 0.0)
                method = content.get("extraction_method", "raw_text")
                item_count = content.get("item_count", 0)

                header = (
                    f"📄 {meta.get('origin_file')} — page {meta.get('page_number')} "
                    f"— {item_count} item(s) via {method}"
                )
                with st.expander(header, expanded=(item_count == 0)):
                    if item_count == 0:
                        st.warning(
                            "⚠️ No structured items found on this page — showing "
                            "raw extracted text instead."
                        )

                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("Extraction method", method)
                    col_b.metric("Items found", item_count)
                    col_c.metric("Type guess (informational)", doc_type_guess)

                    if content.get("items"):
                        st.markdown("**Extracted items** (fields are whatever the source itself used — no fixed schema):")
                        st.dataframe(pd.DataFrame(content["items"]), use_container_width=True)
                    else:
                        st.text(content.get("cleaned_text", ""))

                    with st.popover("View full extracted text"):
                        st.text(content.get("cleaned_text", ""))

    st.download_button(
        "⬇ Download AI-ready data (JSON)",
        data=json.dumps(summary["records"], indent=2),
        file_name=f"{summary['source_name']}_ai_ready_data.json",
        mime="application/json",
    )

with st.expander("ℹ️ Architecture notes"):
    st.markdown(
        """
- **Data Sources**: CSV files, REST APIs, PDF documents, SQL databases, and
  cloud object storage (S3) — each represented by its own connector.
- **Ingestion & Connector Layer**: every connector implements `BaseConnector`'s
  `connect → extract → validate → transform` flow, and `IngestionPipeline`
  runs *any* connector identically, without knowing its internals.
- **Authentication**: the Database and Cloud Storage connectors never accept
  or store raw credentials. Database access reads a connection string from
  the `DATABASE_URL` environment variable; Cloud Storage access uses boto3's
  standard credential chain (env vars, `~/.aws/credentials`, or an IAM
  role). Both fall back to a local, credential-free demo (a sample SQLite
  file; a local folder standing in for a bucket) when no real
  source is configured, so the POC runs with zero setup.
- **Document Intelligence**: for PDFs, extraction is schema-free — every
  page always attempts table detection, then key-value field detection,
  then a price-anchored fallback for prose listings, merging whatever
  structures are found rather than requiring a pre-defined schema per
  document type.
- **Extensibility (connectors)**: to add a new data source, implement a new
  class extending `BaseConnector` — no other file changes. This POC went
  from 3 to 5 connectors (Database, Cloud Storage) with zero changes to
  `IngestionPipeline` or `BaseConnector`.
        """
    )
