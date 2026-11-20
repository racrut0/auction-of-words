import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.lobbies import router as lobbies_router
from app.api.profile import router as profile_router
from app.api.word_bank import router as word_bank_router
from app.config import settings
from app.core.errors import ServiceError, service_error_handler
from app.database import engine, init_models
from app.services.lobby_rounds import run_rounds


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await init_models()
    round_worker = asyncio.create_task(run_rounds())
    try:
        yield
    finally:
        round_worker.cancel()
        with suppress(asyncio.CancelledError):
            await round_worker
        await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(ServiceError, service_error_handler)

app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(lobbies_router, prefix="/api")
app.include_router(profile_router, prefix="/api")
app.include_router(word_bank_router, prefix="/api")


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "health": "/api/health",
    }
