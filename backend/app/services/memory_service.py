from __future__ import annotations

from typing import Any, List, Tuple

from ..config import get_settings


class MemoryService:
    def __init__(self) -> None:
        settings = get_settings()
        # Lazy import chromadb so tests can run without the package
        try:
            from chromadb import PersistentClient, HttpClient  # type: ignore
            from chromadb.utils.embedding_functions import DefaultEmbeddingFunction  # type: ignore

            if settings.chroma_persist_dir:
                self.client = PersistentClient(path=settings.chroma_persist_dir)
            else:
                self.client = HttpClient(
                    host=settings.chroma_host, port=settings.chroma_port, ssl=settings.chroma_ssl
                )
            # Use generic embedding; in production, plug in OpenAI embeddings by providing vectors externally
            self.embedding_fn = DefaultEmbeddingFunction()
            self._collections: dict[str, Any] = {}
            self._enabled = True
        except Exception:
            # Fallback no-op client when chromadb is unavailable
            self.client = None
            self.embedding_fn = None
            self._collections = {}
            self._enabled = False

    def _get_collection(self, user_id: str):
        if user_id not in self._collections:
            if not self._enabled:
                # Minimal in-memory collection stub
                self._collections[user_id] = {"docs": {}, "order": []}
            else:
                self._collections[user_id] = self.client.get_or_create_collection(
                    name=f"echo_mem_{user_id}", embedding_function=self.embedding_fn
                )
        return self._collections[user_id]

    def add_memory(self, user_id: str, memory_id: str, content: str, metadata: dict | None = None):
        col = self._get_collection(user_id)
        if not self._enabled:
            col["docs"][memory_id] = {"content": content, "metadata": metadata or {}}
            col["order"].append(memory_id)
        else:
            col.add(documents=[content], ids=[memory_id], metadatas=[metadata or {}])

    def delete_memory(self, user_id: str, memory_id: str):
        col = self._get_collection(user_id)
        if not self._enabled:
            col["docs"].pop(memory_id, None)
            if memory_id in col["order"]:
                col["order"].remove(memory_id)
        else:
            col.delete(ids=[memory_id])

    def retrieve_relevant_memories(self, user_id: str, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        col = self._get_collection(user_id)
        if not self._enabled:
            # naive string containment scoring for fallback
            docs: list[tuple[str, float]] = []
            for mid in col["order"][-100:]:
                content = col["docs"][mid]["content"]
                score = 1.0 if query.lower() in content.lower() else 0.5
                docs.append((content, score))
            docs.sort(key=lambda x: x[1], reverse=True)
            return docs[:top_k]
        results = col.query(query_texts=[query], n_results=top_k)
        docs = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]
        if not docs:
            return []
        scored = list(zip(docs, distances))
        return [(doc, float(score)) for doc, score in scored]


_memory_service: MemoryService | None = None


def get_memory_service() -> MemoryService:
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
