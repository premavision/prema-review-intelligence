# Prema Review Intelligence

E-commerce review intelligence prototype for the Prema Vision portfolio. The app ingests raw review exports (CSV/JSON), stores them in SQLite, analyzes sentiment & themes, exposes a FastAPI backend, and offers a Streamlit dashboard for stakeholders.

## Highlights

- Review ingestion with dataset management and provenance metadata.
- Lightweight NLP pipeline mixing classical heuristics with an LLM-ready abstraction.
- Caching of dataset analyses to avoid re-running heavy steps.
- FastAPI-powered API plus Streamlit dashboard for quick exploration.
- Sample data and scripts to demo the workflow end to end.

## Project Layout

```
app/
  analysis/        # stats + theme extraction + LLM wrapper
  api/             # FastAPI routers & dependencies
  core/            # settings + logging
  db/              # SQLModel models & engine helpers
  ingestion/       # CSV/JSON ingestion service
  schemas/         # Pydantic DTOs shared across layers
  services/        # Orchestration services (dataset, analysis)
dashboard/         # Streamlit UI that calls the API
data/samples/      # Example datasets for demos
scripts/           # Utility scripts (e.g., ingest sample)
tests/             # Lightweight unit tests
```

## Getting Started

1. **Install dependencies**

   ```bash
   poetry install
   ```

2. **Seed the database with sample data**

   ```bash
   poetry run python scripts/ingest_sample.py
   ```

3. **Run the API**

   ```bash
   poetry run uvicorn app.main:app --reload
   ```

4. **Run the Streamlit dashboard (optional)**

   ```bash
   poetry run streamlit run dashboard/app.py
   ```

   By default the dashboard expects the API at `http://localhost:8000`. Override with `REVIEW_API_BASE_URL`.

## API Overview

- `GET /health` – health check.
- `POST /datasets` – multipart upload of CSV/JSON to create a dataset and ingest reviews.
- `GET /datasets` – list datasets with metadata.
- `GET /datasets/{id}/summary?force={bool}` – cached stats + summary + top themes.
- `GET /datasets/{id}/themes` – theme list with sentiments & representative reviews.
- `GET /reviews` – filterable review list (dataset/min/max rating).

Use the generated OpenAPI docs at `http://localhost:8000/docs`.

## Configuration

Set environment variables via `.env` (see `.env.example`):

- `DATABASE_URL` – defaults to `sqlite:///./data/app.db`.
- `MAX_THEMES` – number of themes returned per analysis.
- `LLM_PROVIDER` / `OPENAI_API_KEY` – stubbed out; ready for real LLM integration.

## Tooling

- Format: `poetry run black .` + `poetry run isort .`
- Lint: `poetry run ruff check .`
- Tests: `poetry run pytest`

## Next Steps

- Swap `MockLLMClient` with a production LLM provider.
- Add richer clustering/embedding analysis.
- Wire ingestion to live sources (Amazon, Shopify, etc.).

Contributions welcome – open an issue or reach out to Prema Vision.
