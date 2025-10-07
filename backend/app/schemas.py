from __future__ import annotations

import datetime as dt
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# User
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str]

    class Config:
        from_attributes = True


# Memory
class MemoryCreate(BaseModel):
    content: str
    tags: Optional[str] = None


class MemoryUpdate(BaseModel):
    content: Optional[str] = None
    tags: Optional[str] = None


class MemoryOut(BaseModel):
    id: str
    user_id: str
    content: str
    source: Optional[str] = None
    tags: Optional[str] = None
    created_at: dt.datetime

    class Config:
        from_attributes = True


# Message / Chat
class ChatRequest(BaseModel):
    user_id: str
    message: str
    stream: bool = Field(default=True)


class ChatResponse(BaseModel):
    reply: str


class MessageOut(BaseModel):
    id: str
    user_id: str
    role: str
    content: str
    created_at: dt.datetime

    class Config:
        from_attributes = True


class RetrievedMemory(BaseModel):
    content: str
    score: float
