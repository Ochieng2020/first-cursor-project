from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Memory
from ..services.memory_service import get_memory_service


async def persist_memory_to_vector_store(db: AsyncSession, memory: Memory) -> None:
    memory_service = get_memory_service()
    memory_service.add_memory(user_id=memory.user_id, memory_id=memory.id, content=memory.content, metadata={"source": memory.source or ""})
