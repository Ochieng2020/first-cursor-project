import asyncio
import json
import os
import re

import pytest
from httpx import AsyncClient

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

from app.main import app  # noqa: E402
from app.db import Base, engine  # noqa: E402


@pytest.fixture(autouse=True, scope="session")
async def setup_db():
    async with engine.begin() as conn:  # type: ignore[call-arg]
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.mark.asyncio
async def test_user_register_login_and_memory_and_chat_stream():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Register
        r = await ac.post("/api/user/register", json={"email": "a@b.com", "password": "pass", "full_name": "Alice"})
        assert r.status_code == 200, r.text
        user = r.json()
        assert user["email"] == "a@b.com"
        user_id = user["id"]

        # Login
        r = await ac.post("/api/user/login", json={"email": "a@b.com", "password": "pass"})
        assert r.status_code == 200, r.text
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create memory
        r = await ac.post("/api/memory/", headers=headers, json={"content": "User likes hiking on weekends", "tags": "hobby"})
        assert r.status_code == 200, r.text

        # List memories
        r = await ac.get("/api/memory/", headers=headers)
        assert r.status_code == 200
        memories = r.json()
        assert any("hiking" in m["content"] for m in memories)

        # Chat streaming
        req = {"user_id": user_id, "message": "What do I like to do?"}
        r = await ac.post("/api/chat/", headers=headers, json=req)
        assert r.status_code == 200
        # Consume SSE-like stream
        text = r.text
        assert "data: [DONE]" in text or "token" in text
