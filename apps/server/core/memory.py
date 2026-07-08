import asyncio
from abc import ABC, abstractmethod

import structlog

from core.supabase_client import get_service_client

logger = structlog.get_logger()


class BaseMemoryRepository(ABC):
    @abstractmethod
    async def search(self, user_id: str, embedding: list[float], top_k: int = 5) -> list[str]:
        """Retorna lista de conteúdos relevantes ordenados por similaridade."""
        ...

    @abstractmethod
    async def insert(self, user_id: str, run_id: str, content: str, embedding: list[float]) -> None:
        """Salva novo registro de memória com embedding."""
        ...


class MemoryRepository(BaseMemoryRepository):
    def __init__(self, threshold: float = 0.7) -> None:
        self._client = get_service_client()
        self._threshold = threshold

    async def search(self, user_id: str, embedding: list[float], top_k: int = 5) -> list[str]:
        try:
            client = self._client
            result = await asyncio.to_thread(
                lambda: client.rpc(
                    "match_memories",
                    {
                        "query_embedding": embedding,
                        "match_user_id": user_id,
                        "match_threshold": self._threshold,
                        "match_count": top_k,
                    },
                ).execute()
            )
            return [row["content"] for row in (result.data or [])]
        except Exception:
            logger.exception("memory_search_failed", user_id=user_id)
            return []

    async def insert(self, user_id: str, run_id: str, content: str, embedding: list[float]) -> None:
        client = self._client
        await asyncio.to_thread(
            lambda: client.table("memories").insert({
                "user_id": user_id,
                "run_id": run_id,
                "content": content,
                "embedding": embedding,
            }).execute()
        )


class MockMemoryRepository(BaseMemoryRepository):
    def __init__(self, memories: list[str] | None = None) -> None:
        self._memories: list[str] = memories or []
        self.saved: list[dict] = []

    async def search(self, user_id: str, embedding: list[float], top_k: int = 5) -> list[str]:
        return self._memories[:top_k]

    async def insert(self, user_id: str, run_id: str, content: str, embedding: list[float]) -> None:
        self.saved.append({"user_id": user_id, "run_id": run_id, "content": content})
