from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncEngine

from .config import get_settings
from .db import Base, engine
from .routers import chat, memory, user


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create DB tables
    settings = get_settings()
    async with engine.begin() as conn:  # type: ignore[call-arg]
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: nothing yet


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    app.include_router(user.router, prefix="/api/user", tags=["user"])
    app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

    return app


app = create_app()
