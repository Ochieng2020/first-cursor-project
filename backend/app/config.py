from __future__ import annotations

import base64
import os
from functools import lru_cache
from pydantic import BaseModel, Field


class Settings(BaseModel):
    # App
    app_name: str = Field(default="Echo Backend")
    environment: str = Field(default=os.getenv("ENVIRONMENT", "development"))
    debug: bool = Field(default=os.getenv("DEBUG", "false").lower() == "true")
    backend_host: str = Field(default=os.getenv("BACKEND_HOST", "0.0.0.0"))
    backend_port: int = Field(default=int(os.getenv("BACKEND_PORT", "8000")))

    # Database
    database_url: str = Field(
        default=os.getenv(
            "DATABASE_URL",
            "sqlite+aiosqlite:///./echo.db",
        )
    )

    # Redis
    redis_url: str = Field(default=os.getenv("REDIS_URL", "redis://localhost:6379/0"))

    # JWT
    jwt_secret_key: str = Field(default=os.getenv("JWT_SECRET_KEY", "change-me"))
    jwt_algorithm: str = Field(default=os.getenv("JWT_ALGORITHM", "HS256"))
    access_token_expire_minutes: int = Field(
        default=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    )

    # Encryption
    encryption_key_b64: str = Field(default=os.getenv("ECHO_ENCRYPTION_KEY", ""))

    # LLM
    llm_provider: str = Field(default=os.getenv("LLM_PROVIDER", "mock"))  # mock|openai|mistral
    openai_api_key: str | None = Field(default=os.getenv("OPENAI_API_KEY"))
    openai_model: str = Field(default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    openai_embedding_model: str = Field(
        default=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    )

    mistral_api_key: str | None = Field(default=os.getenv("MISTRAL_API_KEY"))
    mistral_model: str = Field(default=os.getenv("MISTRAL_MODEL", "mistral-large-latest"))

    # ChromaDB
    chroma_host: str = Field(default=os.getenv("CHROMA_HOST", "localhost"))
    chroma_port: int = Field(default=int(os.getenv("CHROMA_PORT", "8000")))
    chroma_ssl: bool = Field(default=os.getenv("CHROMA_SSL", "false").lower() == "true")
    chroma_persist_dir: str | None = Field(default=os.getenv("CHROMA_PERSIST_DIR"))

    # Supabase (optional)
    supabase_url: str | None = Field(default=os.getenv("SUPABASE_URL"))
    supabase_anon_key: str | None = Field(default=os.getenv("SUPABASE_ANON_KEY"))

    # System Prompt
    system_prompt: str = Field(
        default=os.getenv(
            "ECHO_SYSTEM_PROMPT",
            (
                "You are Echo, a friendly, emotionally intelligent AI friend who remembers "
                "details about the user and responds with warmth and clarity. You respect "
                "privacy and only use remembered details when relevant."
            ),
        )
    )

    def get_encryption_key(self) -> bytes:
        if not self.encryption_key_b64:
            # Fallback for dev; strongly recommend setting env in production
            # 32 bytes raw key for AES-GCM
            return os.urandom(32)
        try:
            raw = base64.b64decode(self.encryption_key_b64)
            if len(raw) not in (16, 24, 32):
                raise ValueError("Invalid AES key length")
            return raw
        except Exception as exc:  # noqa: BLE001
            raise ValueError("ECHO_ENCRYPTION_KEY must be base64-encoded 16/24/32 bytes") from exc


@lru_cache
def get_settings() -> Settings:
    return Settings()
