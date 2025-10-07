from __future__ import annotations

import json
from typing import AsyncGenerator, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db import get_db
from ..deps import get_current_user
from ..models import Message, Memory, User
from ..schemas import ChatRequest
from ..services.llm_adapter import get_llm_adapter
from ..services.memory_service import get_memory_service

router = APIRouter()


async def _compose_messages(db: AsyncSession, user_id: str, user_input: str) -> List[dict[str, str]]:
    settings = get_settings()

    # Retrieve last 5 messages
    recent = await db.execute(
        select(Message).where(Message.user_id == user_id).order_by(Message.created_at.desc()).limit(5)
    )
    recent_messages = list(reversed(recent.scalars().all()))

    # Retrieve relevant memories
    memory_service = get_memory_service()
    relevant = memory_service.retrieve_relevant_memories(user_id, user_input, top_k=5)

    memory_context = "\n".join([f"- {content} (score: {score:.3f})" for content, score in relevant])

    messages: List[dict[str, str]] = [
        {"role": "system", "content": settings.system_prompt},
    ]

    if memory_context:
        messages.append(
            {
                "role": "system",
                "content": f"Relevant memories about the user (use only if helpful):\n{memory_context}",
            }
        )

    # Add chat history
    for m in recent_messages:
        messages.append({"role": m.role, "content": m.content})

    # Current user message
    messages.append({"role": "user", "content": user_input})

    return messages


@router.post("/", response_class=StreamingResponse)
async def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.id != payload.user_id:
        raise HTTPException(status_code=403, detail="Cannot chat as another user")

    messages = await _compose_messages(db, payload.user_id, payload.message)

    # Save user message
    msg_user = Message(user_id=payload.user_id, role="user", content=payload.message)
    db.add(msg_user)
    await db.commit()

    llm = get_llm_adapter()

    async def token_stream() -> AsyncGenerator[bytes, None]:
        reply_text_parts: List[str] = []
        async for token in llm.stream_chat(messages):
            reply_text_parts.append(token)
            yield f"data: {json.dumps({'token': token})}\n\n".encode()
        full_reply = "".join(reply_text_parts)

        # Save assistant message
        msg_assistant = Message(user_id=payload.user_id, role="assistant", content=full_reply)
        db.add(msg_assistant)
        await db.commit()

        yield b"data: [DONE]\n\n"

    return StreamingResponse(token_stream(), media_type="text/event-stream")
