"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.catalog.router import router as catalog_router

app = FastAPI(title="Anahita", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(catalog_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Return a simple liveness check."""
    return {"status": "ok"}
