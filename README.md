<<<<<<< HEAD
# Enterprise AI Data Integration — POC By Sanket

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
=======
# AI-POC



## Getting started

To make it easy for you to get started with GitLab, here's a list of recommended next steps.

Already a pro? Just edit this README.md and make it your own. Want to make it easy? [Use the template at the bottom](#editing-this-readme)!

## Add your files

* [Create](https://docs.gitlab.com/user/project/repository/web_editor/#create-a-file) or [upload](https://docs.gitlab.com/user/project/repository/web_editor/#upload-a-file) files
* [Add files using the command line](https://docs.gitlab.com/topics/git/add_files/#add-files-to-a-git-repository) or push an existing Git repository with the following command:

```
cd existing_repo
git remote add origin https://gitlab.com/fineshift/users/sanket-jadhav/ai-poc.git
git branch -M main
git push -uf origin main
```

## Integrate with your tools

* [Set up project integrations](https://gitlab.com/fineshift/users/sanket-jadhav/ai-poc/-/settings/integrations)

## Collaborate with your team

* [Invite team members and collaborators](https://docs.gitlab.com/user/project/members/)
* [Create a new merge request](https://docs.gitlab.com/user/project/merge_requests/creating_merge_requests/)
* [Automatically close issues from merge requests](https://docs.gitlab.com/user/project/issues/managing_issues/#closing-issues-automatically)
* [Enable merge request approvals](https://docs.gitlab.com/user/project/merge_requests/approvals/)
* [Set auto-merge](https://docs.gitlab.com/user/project/merge_requests/auto_merge/)

## Test and Deploy

Use the built-in continuous integration in GitLab.

* [Get started with GitLab CI/CD](https://docs.gitlab.com/ci/quick_start/)
* [Analyze your code for known vulnerabilities with Static Application Security Testing (SAST)](https://docs.gitlab.com/user/application_security/sast/)
* [Deploy to Kubernetes, Amazon EC2, or Amazon ECS using Auto Deploy](https://docs.gitlab.com/topics/autodevops/requirements/)
* [Use pull-based deployments for improved Kubernetes management](https://docs.gitlab.com/user/clusters/agent/)
* [Set up protected environments](https://docs.gitlab.com/ci/environments/protected_environments/)

***

# Editing this README

When you're ready to make this README your own, just edit this file and use the handy template below (or feel free to structure it however you want - this is just a starting point!). Thanks to [makeareadme.com](https://www.makeareadme.com/) for this template.

## Suggestions for a good README

Every project is different, so consider which of these sections apply to yours. The sections used in the template are suggestions for most open source projects. Also keep in mind that while a README can be too long and detailed, too long is better than too short. If you think your README is too long, consider utilizing another form of documentation rather than cutting out information.

## Name
Choose a self-explaining name for your project.

## Description
Let people know what your project can do specifically. Provide context and add a link to any reference visitors might be unfamiliar with. A list of Features or a Background subsection can also be added here. If there are alternatives to your project, this is a good place to list differentiating factors.

## Badges
On some READMEs, you may see small images that convey metadata, such as whether or not all the tests are passing for the project. You can use Shields to add some to your README. Many services also have instructions for adding a badge.

## Visuals
Depending on what you are making, it can be a good idea to include screenshots or even a video (you'll frequently see GIFs rather than actual videos). Tools like ttygif can help, but check out Asciinema for a more sophisticated method.

## Installation
Within a particular ecosystem, there may be a common way of installing things, such as using Yarn, NuGet, or Homebrew. However, consider the possibility that whoever is reading your README is a novice and would like more guidance. Listing specific steps helps remove ambiguity and gets people to using your project as quickly as possible. If it only runs in a specific context like a particular programming language version or operating system or has dependencies that have to be installed manually, also add a Requirements subsection.

## Usage
Use examples liberally, and show the expected output if you can. It's helpful to have inline the smallest example of usage that you can demonstrate, while providing links to more sophisticated examples if they are too long to reasonably include in the README.

## Support
Tell people where they can go to for help. It can be any combination of an issue tracker, a chat room, an email address, etc.

## Roadmap
If you have ideas for releases in the future, it is a good idea to list them in the README.

## Contributing
State if you are open to contributions and what your requirements are for accepting them.

For people who want to make changes to your project, it's helpful to have some documentation on how to get started. Perhaps there is a script that they should run or some environment variables that they need to set. Make these steps explicit. These instructions could also be useful to your future self.

You can also document commands to lint the code or run tests. These steps help to ensure high code quality and reduce the likelihood that the changes inadvertently break something. Having instructions for running tests is especially helpful if it requires external setup, such as starting a Selenium server for testing in a browser.

## Authors and acknowledgment
Show your appreciation to those who have contributed to the project.

## License
For open source projects, say how it is licensed.

## Project status
If you have run out of energy or time for your project, put a note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.
>>>>>>> ddc778611c71c93bfaf4d567072bd5fe740d119c
