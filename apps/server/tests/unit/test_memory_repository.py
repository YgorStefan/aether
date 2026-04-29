import pytest
from unittest.mock import MagicMock, patch

from core.memory import MemoryRepository, MockMemoryRepository


@pytest.mark.asyncio
async def test_mock_search_retorna_memorias_semeadas():
    repo = MockMemoryRepository(memories=["Resultado do run anterior sobre Python"])
    results = await repo.search("user-1", [0.1] * 768, top_k=5)
    assert results == ["Resultado do run anterior sobre Python"]


@pytest.mark.asyncio
async def test_mock_search_vazio_sem_memorias():
    repo = MockMemoryRepository()
    results = await repo.search("user-1", [0.1] * 768)
    assert results == []


@pytest.mark.asyncio
async def test_mock_insert_armazena_conteudo():
    repo = MockMemoryRepository()
    await repo.insert("user-1", "run-abc", "Aprendi sobre FastAPI", [0.1] * 768)
    assert len(repo.saved) == 1
    assert repo.saved[0]["content"] == "Aprendi sobre FastAPI"
    assert repo.saved[0]["user_id"] == "user-1"
    assert repo.saved[0]["run_id"] == "run-abc"


@pytest.mark.asyncio
async def test_mock_search_respeita_top_k():
    repo = MockMemoryRepository(memories=["A", "B", "C", "D"])
    results = await repo.search("user-1", [0.1] * 768, top_k=2)
    assert results == ["A", "B"]


@pytest.mark.asyncio
async def test_memory_repository_search_chama_rpc_supabase():
    mock_client = MagicMock()
    mock_client.rpc.return_value.execute.return_value = MagicMock(
        data=[{"content": "Resultado anterior sobre Python"}]
    )

    with patch("core.memory.create_client", return_value=mock_client):
        repo = MemoryRepository(url="http://test", service_key="key", threshold=0.7)
        results = await repo.search("user-1", [0.1] * 768, top_k=5)

    mock_client.rpc.assert_called_once_with(
        "match_memories",
        {
            "query_embedding": [0.1] * 768,
            "match_user_id": "user-1",
            "match_threshold": 0.7,
            "match_count": 5,
        },
    )
    assert results == ["Resultado anterior sobre Python"]


@pytest.mark.asyncio
async def test_memory_repository_insert_chama_supabase():
    mock_client = MagicMock()
    mock_client.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{}])

    with patch("core.memory.create_client", return_value=mock_client):
        repo = MemoryRepository(url="http://test", service_key="key", threshold=0.7)
        await repo.insert("user-1", "run-abc", "Aprendi sobre FastAPI", [0.1] * 768)

    mock_client.table.assert_called_once_with("memories")
    mock_client.table.return_value.insert.assert_called_once_with({
        "user_id": "user-1",
        "run_id": "run-abc",
        "content": "Aprendi sobre FastAPI",
        "embedding": [0.1] * 768,
    })


@pytest.mark.asyncio
async def test_memory_repository_search_retorna_vazio_se_rpc_falhar():
    mock_client = MagicMock()
    mock_client.rpc.side_effect = RuntimeError("connection error")

    with patch("core.memory.create_client", return_value=mock_client):
        repo = MemoryRepository(url="http://test", service_key="key", threshold=0.7)
        results = await repo.search("user-1", [0.1] * 768)

    assert results == []
