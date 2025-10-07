from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import get_current_user
from ..db import get_db
from ..models import Memory, User
from .utils import persist_memory_to_vector_store
from ..schemas import MemoryCreate, MemoryOut, MemoryUpdate

router = APIRouter()


@router.get("/", response_model=List[MemoryOut])
async def list_memories(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Memory).where(Memory.user_id == current_user.id).order_by(Memory.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=MemoryOut)
async def create_memory(
    payload: MemoryCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    memory = Memory(user_id=current_user.id, content=payload.content, source="manual", tags=payload.tags)
    db.add(memory)
    await db.commit()
    await db.refresh(memory)
    await persist_memory_to_vector_store(db, memory)
    return memory


@router.put("/{memory_id}", response_model=MemoryOut)
async def update_memory(
    memory_id: str,
    payload: MemoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Memory).where(Memory.id == memory_id, Memory.user_id == current_user.id))
    memory = result.scalar_one_or_none()
    if memory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")

    if payload.content is not None:
        memory.content = payload.content
    if payload.tags is not None:
        memory.tags = payload.tags

    await db.commit()
    await db.refresh(memory)
    return memory


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Memory).where(Memory.id == memory_id, Memory.user_id == current_user.id))
    memory = result.scalar_one_or_none()
    if memory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")

    await db.delete(memory)
    await db.commit()
    return {"status": "deleted"}
