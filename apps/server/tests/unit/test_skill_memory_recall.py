import pytest
from unittest.mock import AsyncMock, MagicMock

from core.llm_adapter import MockLLMAdapter
from skills.memory_recall import MemoryRecall, MemoryRecallParams


@pytest.mark.asyncio
async def test_memory_recall_retorna_memorias_formatadas():
    mock_repo = MagicMock()
    mock_repo.search = AsyncMock(return_value=[
        "Run anterior: análise de mercado concluída",
        "Run anterior: relatório gerado em PDF",
    ])

    skill = MemoryRecall(memory_repo=mock_repo, user_id="user-1", adapter=MockLLMAdapter())
    params = MemoryRecallParams(query="análise de mercado", top_k=5)
    result = await skill.execute(params)

    assert result.success is True
    assert "análise de mercado" in result.output
    assert "relatório gerado" in result.output


@pytest.mark.asyncio
async def test_memory_recall_retorna_mensagem_quando_vazio():
    mock_repo = MagicMock()
    mock_repo.search = AsyncMock(return_value=[])

    skill = MemoryRecall(memory_repo=mock_repo, user_id="user-1", adapter=MockLLMAdapter())
    params = MemoryRecallParams(query="tópico desconhecido", top_k=3)
    result = await skill.execute(params)

    assert result.success is True
    assert result.output == "Nenhuma memória relevante encontrada."


@pytest.mark.asyncio
async def test_memory_recall_propaga_erro_como_skill_result():
    mock_repo = MagicMock()
    mock_repo.search = AsyncMock(side_effect=RuntimeError("conexão perdida"))

    skill = MemoryRecall(memory_repo=mock_repo, user_id="user-1", adapter=MockLLMAdapter())
    params = MemoryRecallParams(query="qualquer coisa", top_k=3)
    result = await skill.execute(params)

    assert result.success is False
    assert result.error is not None


def test_memory_recall_metadata():
    from core.memory import MockMemoryRepository
    skill = MemoryRecall(memory_repo=MockMemoryRepository(), user_id="user-1", adapter=MockLLMAdapter())
    meta = skill.metadata()
    assert meta.name == "memory_recall"
    assert meta.requires_approval is False
    assert "query" in meta.parameters_schema["properties"]
