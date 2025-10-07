# Echo

Echo is a cross-platform AI-powered personal conversational friend with shared memory across desktop and mobile.

## Stack
- Backend: FastAPI, PostgreSQL (SQLAlchemy), Redis, ChromaDB
- Desktop: Electron + React + Tailwind
- Mobile: React Native + Expo
- AI: OpenAI (modular adapter), with fallback mock
- Auth: JWT (with option to integrate Supabase Auth)

## Mono-Repo Structure
```
backend/
  app/
  tests/
  Dockerfile
  .env.example
frontend-electron/
mobile-expo/
shared/
```

## Backend: Getting Started

### 1) Environment
Copy env and set secrets:
```bash
cp backend/.env.example backend/.env
# Edit backend/.env
```

Generate AES key (base64 32 bytes):
```bash
python -c "import os,base64;print(base64.b64encode(os.urandom(32)).decode())"
```
Set `ECHO_ENCRYPTION_KEY` with that value.

### 2) Docker (recommended)
```bash
docker compose up --build
```
Backend: http://localhost:8000

### 3) Local (without Docker)
```bash
cd backend
pip install -e .[dev]
uvicorn app.main:app --reload
```

### 4) API Overview
- POST `/api/user/register` {email, password, full_name?}
- POST `/api/user/login` {email, password} -> {access_token}
- GET `/api/memory/` (auth)
- POST `/api/memory/` (auth) {content, tags?}
- PUT `/api/memory/{id}` (auth)
- DELETE `/api/memory/{id}` (auth)
- POST `/api/chat/` (auth, SSE) {user_id, message}

### 5) Notes
- Field-level AES-GCM encryption for PII and content.
- Vector memory via ChromaDB. Falls back to in-memory naive retrieval if Chroma is unavailable.
- LLM adapter supports OpenAI or mock (set `LLM_PROVIDER` and keys).

### 6) Tests
```bash
cd backend
pytest -q
```

## Frontend apps
Coming next: Electron (React + Tailwind) and Expo mobile app with shared UI components and JWT auth.
