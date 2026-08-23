"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.campaigns.router import router as campaigns_router
from app.catalog.router import router as catalog_router
from app.characters.router import router as characters_router
from app.combat.router import router as combat_router
from app.combat.ws_router import router as combat_ws_router
from app.sessions.router import router as sessions_router
from app.world.router import router as world_router

app = FastAPI(title="Anahita", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(campaigns_router)
app.include_router(catalog_router)
app.include_router(characters_router)
app.include_router(sessions_router)
app.include_router(combat_router)
app.include_router(combat_ws_router)
app.include_router(world_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Return a simple liveness check."""
    return {"status": "ok"}
