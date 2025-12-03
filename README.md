# 🧠 Prema Review Intelligence  
### AI-powered E-commerce Review Analysis · FastAPI + Streamlit + SQLite

Prema Review Intelligence is a lightweight but production-ready prototype for **automated analysis of large e-commerce review datasets**.  
It ingests raw CSV/JSON exports, stores them in SQLite, computes sentiment & thematic insights, exposes a **FastAPI backend**, and ships with a **Streamlit dashboard** for interactive exploration.

This project is part of the **Prema Vision AI Automations** portfolio.

---

## 🔍 What It Does

- 📥 **Ingest raw review files** (CSV/JSON) with dataset metadata  
- 🧹 **Validate files** (size, type, row limits) for safe ingestion  
- 💾 **Store reviews in SQLite** using SQLModel  
- 🧠 **Analyze sentiment, themes, and summary statistics**  
- ⚡ **Cache heavy analyses** to avoid recomputation  
- 🔌 **Expose a clean API** with FastAPI  
- 📊 **Interactive dashboard** built with Streamlit  
- 🧪 **Testable architecture** with sample data and simple unit tests  

---

## 🏗 Architecture Overview

```
app/
  analysis/        # Stats + theme extraction + LLM abstraction
  api/             # FastAPI routes, dependencies, middleware
  core/            # Settings, logging, environment config
  db/              # SQLModel models and DB engine
  ingestion/       # CSV/JSON ingestion pipeline
  schemas/         # Pydantic DTOs for API transport
  services/        # Orchestrators for datasets & analyses

dashboard/
  app.py           # Streamlit UI powered by the API

data/samples/      # Example datasets for demos
scripts/           # Helper scripts (e.g., ingest sample data)
tests/             # Lightweight unit tests
```

---

## 🚀 Getting Started

### 1. Install dependencies

```bash
poetry install
```

### 2. Seed the database with sample data

```bash
poetry run python scripts/ingest_sample.py
```

### 3. Run the API

```bash
poetry run uvicorn app.main:app --reload
```

### 4. (Optional) Run the Streamlit dashboard

```bash
poetry run streamlit run dashboard/app.py
```

Default dashboard API target:  
`http://localhost:8000`  
Override via: `REVIEW_API_BASE_URL`

---

## 🔌 API Overview

### Health
- `GET /health`

### Datasets
- `POST /datasets` — upload CSV/JSON and ingest  
- `GET /datasets` — list datasets  
- `GET /datasets/{id}/summary?force={bool}` — stats, sentiment, themes  
- `GET /datasets/{id}/themes` — structured theme extraction

### Reviews
- `GET /reviews` — filterable review list  
  - params: dataset, rating range, paging

Interactive docs:  
**http://localhost:8000/docs**

---

## 🔐 Security Features

This project includes a practical security foundation:

- ✅ File type/size/content validation  
- ✅ DoS protection via row & size limits  
- ✅ CORS configuration via environment  
- ✅ Rate limiting for LLM calls  
- ✅ API key validation  
- ✅ Input sanitization (Pydantic)  
- ✅ Controlled DB access via SQLModel & engine pooling  

For full guidance and deployment notes, see:  
**`SECURITY.md`**

---

## ⚙️ Configuration

Defined via `.env` (see `.env.example`):

- `DATABASE_URL` — default `sqlite:///./data/app.db`
- `MAX_THEMES` — number of returned themes
- `LLM_PROVIDER` / `OPENAI_API_KEY` — optional LLM integration
- `CORS_ALLOWED_ORIGINS`
- `MAX_UPLOAD_SIZE` — default 10MB
- `MAX_INGESTION_ROWS` — DoS protection (default: 50,000)
- `LLM_RATE_LIMIT_RPM` — default: 60

---

## 🧪 Development Tooling

```bash
poetry run black .
poetry run isort .
poetry run ruff check .
poetry run pytest
```

---

## 🛣 Next Steps (Roadmap)

- Swap `MockLLMClient` for OpenAI/Anthropic  
- Improve clustering & embeddings  
- Add product-level insights (pricing, defect themes)  
- Connect ingestion to live sources (Amazon, Shopify)  
- Add multi-dataset comparison & trend analysis

---

## 🤝 Contributing

Issues and PRs welcome.  
Part of the **Prema Vision** internal AI automation suite.

MIT License.
