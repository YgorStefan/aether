from pydantic import BaseModel

from core.llm_adapter import BaseLLMAdapter
from core.memory import BaseMemoryRepository
from skills.base import Skill, SkillResult


class MemoryRecallParams(BaseModel):
    query: str
    top_k: int = 5


class MemoryRecall(Skill):
    name = "memory_recall"
    description = (
        "Busca memórias relevantes de runs anteriores do mesmo usuário. "
        "Use para aproveitar contexto e resultados de execuções passadas sobre o mesmo tópico."
    )
    parameters = MemoryRecallParams
    requires_approval = False

    def __init__(
        self,
        memory_repo: BaseMemoryRepository | None = None,
        user_id: str | None = None,
        adapter: BaseLLMAdapter | None = None,
    ) -> None:
        self._memory_repo = memory_repo
        self._user_id = user_id
        self._adapter = adapter

    async def execute(self, params: BaseModel) -> SkillResult:
        assert isinstance(params, MemoryRecallParams)
        try:
            if self._adapter is not None:
                embedding = await self._adapter.embed(params.query)
            else:
                embedding = [0.0] * 768

            memories = await self._memory_repo.search(
                user_id=self._user_id,
                embedding=embedding,
                top_k=params.top_k,
            )
            if not memories:
                return SkillResult(success=True, output="Nenhuma memória relevante encontrada.")
            output = "\n".join(f"- {m}" for m in memories)
            return SkillResult(success=True, output=output, metadata={"count": len(memories)})
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))
