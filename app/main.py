from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import datasets, health, reviews, themes
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.base import init_db

configure_logging()

app = FastAPI(
    title="Prema Review Intelligence",
    version="0.1.0",
    description="Portfolio-grade prototype for review intelligence and insights",
)

# Configure CORS based on environment
if settings.app_env == "local":
    # Local development: allow Streamlit and common local origins
    cors_origins = [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    allow_credentials = True
else:
    # Production/dev: use configured origins or deny all
    if settings.cors_allowed_origins:
        cors_origins = [origin.strip() for origin in settings.cors_allowed_origins.split(",")]
    else:
        cors_origins = []
    allow_credentials = True if cors_origins else False

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    expose_headers=["Content-Type", "Content-Length"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.include_router(health.router)
app.include_router(datasets.router)
app.include_router(themes.router)
app.include_router(reviews.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Prema Vision Review Intelligence API"}
