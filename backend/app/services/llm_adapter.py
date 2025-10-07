from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncGenerator, List

import httpx

from ..config import get_settings


class LLMAdapter(ABC):
    @abstractmethod
    async def stream_chat(self, messages: list[dict[str, str]]) -> AsyncGenerator[str, None]:
        ...

    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        ...


class MockLLMAdapter(LLMAdapter):
    async def stream_chat(self, messages: list[dict[str, str]]):  # type: ignore[override]
        reply = " ".join(m["content"] for m in messages if m["role"] == "user")
        for chunk in [reply[i : i + 16] for i in range(0, len(reply), 16)]:
            yield chunk

    async def embed(self, texts: List[str]) -> List[List[float]]:  # type: ignore[override]
        return [[float(len(t))] for t in texts]


class OpenAILLMAdapter(LLMAdapter):
    async def stream_chat(self, messages: list[dict[str, str]]):  # type: ignore[override]
        settings = get_settings()
        model = settings.openai_model
        api_key = settings.openai_api_key
        headers = {"Authorization": f"Bearer {api_key}"}
        url = "https://api.openai.com/v1/chat/completions"
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                url,
                headers=headers,
                json={
                    "model": model,
                    "messages": messages,
                    "stream": True,
                },
            )
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line and line.startswith("data: "):
                    data = line[len("data: ") :]
                    if data == "[DONE]":
                        break
                    # naive parsing; in real impl, parse json and delta content
                    yield data

    async def embed(self, texts: List[str]) -> List[List[float]]:  # type: ignore[override]
        settings = get_settings()
        model = settings.openai_embedding_model
        api_key = settings.openai_api_key
        headers = {"Authorization": f"Bearer {api_key}"}
        url = "https://api.openai.com/v1/embeddings"
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, headers=headers, json={"model": model, "input": texts})
            resp.raise_for_status()
            data = resp.json()
            return [d["embedding"] for d in data["data"]]


def get_llm_adapter() -> LLMAdapter:
    settings = get_settings()
    if settings.llm_provider == "openai" and settings.openai_api_key:
        return OpenAILLMAdapter()
    return MockLLMAdapter()
