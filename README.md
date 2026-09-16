# Enterprise AI Data Integration — POC

A modular proof-of-concept covering **Data Sources**, the **Ingestion &
Connector Layer**, and **Document Intelligence**, with a Streamlit UI for
demoing the flow end-to-end.

## 1. Setup

```bash
cd enterprise_ai_poc
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Run

```bash
streamlit run app.py
```

Then open the URL Streamlit prints (usually `http://localhost:8501`).

No configuration is required to try it out — sample data is included:
- `sample_data/sample_customers.csv` (CSV connector demo, includes 2
  intentionally invalid rows so you can see failed-record handling)
- `sample_data/sample_invoice.pdf` (PDF connector demo)
- REST API: defaults to the free public test API
  `https://jsonplaceholder.typicode.com/users`, or tick **"Offline demo
  mode"** in the sidebar to skip the live HTTP call entirely.

## 3. Architecture

```
Data Sources           Ingestion & Connector Layer         Document Intelligence
─────────────          ───────────────────────────         ─────────────────────
CSV file        ──┐
REST API        ──┼──► BaseConnector.run()          ──┐
PDF document    ──┘    (Connect→Extract→Validate      │
                         →Transform, same for all)     │
                                │                       │
                                ▼                       │
                        IngestionPipeline               │  (used internally by
                        (connector-agnostic;             │   PDFConnector.transform)
                         logs + aggregates results)      │
                                │                        ▼
                                ▼                clean_text() → classify_document()
                        AI-ready JSON records          → extract_fields()
                                │
                                ▼
                        Streamlit dashboard (app.py)
```

### Key design decisions

| Decision | Why |
|---|---|
| `BaseConnector` is an abstract class with a non-overridable `run()` | Guarantees every source follows the exact same 4-stage flow, so the pipeline can treat all sources identically. |
| `IngestionPipeline` only depends on `BaseConnector` | New connectors (S3, database, SFTP, etc.) can be added by writing a new class — **zero changes** to pipeline code. |
| Validation logic lives in `pipeline/validators.py` | Shared, reusable checks instead of duplicating logic per connector. |
| Document intelligence (`clean_text`, `classify_document`, `extract_fields`) lives outside `PDFConnector` | These are reusable utilities — a future DOCX or OCR connector can call the same functions. |
| Classification is rule-based keyword scoring, not ML | Keeps the POC transparent, dependency-light, and easy to explain — the interface (`classify_document(text) -> label, confidence`) is exactly what a real ML/LLM classifier would expose later, so swapping it in is a drop-in change. |
| No Kafka / Kubernetes / microservices | Out of scope for a POC per requirements — this is a single Python process with clear internal module boundaries, which already demonstrates the architecture without infra overhead. |

## 4. Folder structure

```
enterprise_ai_poc/
├── app.py                          # Streamlit UI (thin presentation layer)
├── requirements.txt
├── connectors/
│   ├── base_connector.py           # Abstract interface — the core contract
│   ├── csv_connector.py
│   ├── rest_api_connector.py
│   └── pdf_connector.py
├── document_intelligence/
│   ├── text_cleaner.py
│   ├── classifier.py
│   └── field_extractor.py
├── pipeline/
│   ├── validators.py
│   └── ingestion_pipeline.py       # Core, connector-agnostic orchestrator
├── utils/
│   └── logger.py
├── sample_data/
│   ├── sample_customers.csv
│   └── sample_invoice.pdf
└── logs/
    └── ingestion.log               # created at runtime
```

## 5. Adding a new connector (to demonstrate extensibility live)

1. Create `connectors/my_new_connector.py`.
2. Subclass `BaseConnector` and implement `connect()`, `extract()`,
   `validate()`, `transform()`.
3. In `app.py`, add it as a new sidebar option and instantiate it.

The `IngestionPipeline` and every other module require **no changes**.

## 6. Common AI-ready record schema

Every connector's `transform()` step outputs records in this shape,
regardless of source:

```json
{
  "record_id": "csv-0",
  "source_type": "csv",
  "content": { "...normalized fields..." },
  "metadata": { "...source-specific context..." }
}
```

This consistency is what allows the Streamlit UI (and any downstream AI
system) to consume data from any connector the same way.
