from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import datasets, health, reviews, themes
from app.core.logging import configure_logging
from app.db.base import init_db

configure_logging()

app = FastAPI(
    title="Prema Review Intelligence",
    version="0.1.0",
    description="Portfolio-grade prototype for review intelligence and insights",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
