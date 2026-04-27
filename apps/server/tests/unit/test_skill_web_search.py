import pytest
from unittest.mock import MagicMock, patch
from skills.web_search import WebSearch, WebSearchParams


@pytest.mark.asyncio
async def test_web_search_retorna_resultados():
    mock_response = {
        "results": [
            {"title": "Título A", "content": "Conteúdo A"},
            {"title": "Título B", "content": "Conteúdo B"},
        ]
    }
    with patch("skills.web_search.TavilyClient") as MockClient:
        MockClient.return_value.search.return_value = mock_response
        skill = WebSearch()
        result = await skill.execute(WebSearchParams(query="Python LangGraph", max_results=2))

    assert result.success is True
    assert "Título A" in result.output
    assert "Título B" in result.output
    assert result.metadata["results_count"] == 2


@pytest.mark.asyncio
async def test_web_search_sem_resultados():
    with patch("skills.web_search.TavilyClient") as MockClient:
        MockClient.return_value.search.return_value = {"results": []}
        skill = WebSearch()
        result = await skill.execute(WebSearchParams(query="xyz_inexistente_abc"))

    assert result.success is True
    assert "Nenhum resultado" in result.output


@pytest.mark.asyncio
async def test_web_search_falha_de_api():
    with patch("skills.web_search.TavilyClient") as MockClient:
        MockClient.return_value.search.side_effect = Exception("API Error")
        skill = WebSearch()
        result = await skill.execute(WebSearchParams(query="teste"))

    assert result.success is False
    assert result.error is not None


def test_web_search_metadados():
    skill = WebSearch()
    meta = skill.metadata()
    assert meta.name == "web_search"
    assert meta.requires_approval is False
    assert "query" in meta.parameters_schema["properties"]
