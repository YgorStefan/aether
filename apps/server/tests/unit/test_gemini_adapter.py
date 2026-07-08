import pytest
from pydantic import BaseModel
from unittest.mock import AsyncMock, MagicMock, patch

from agents.state import AgentState


class _Answer(BaseModel):
    text: str


def _make_state() -> AgentState:
    return {
        "run_id": "r1",
        "objective": "test",
        "tasks": [],
        "current_task_index": 0,
        "status": "running",
        "error": "",
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "skill_cache": {},
    }


@pytest.mark.asyncio
async def test_gemini_adapter_generate_retorna_parsed_e_tokens():
    with patch("langchain_google_genai.ChatGoogleGenerativeAI") as mock_llm_cls, \
         patch("langchain_google_genai.GoogleGenerativeAIEmbeddings"):
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_raw_msg = MagicMock()
        mock_raw_msg.usage_metadata = {"input_tokens": 42, "output_tokens": 7}
        mock_structured.ainvoke = AsyncMock(
            return_value={"parsed": _Answer(text="ok"), "raw": mock_raw_msg}
        )
        mock_llm.with_structured_output.return_value = mock_structured
        mock_llm_cls.return_value = mock_llm

        from core.llm_adapter import GeminiAdapter
        adapter = GeminiAdapter(api_key="fake-key")
        result, input_tokens, output_tokens = await adapter.generate("prompt", _Answer, _make_state())

    assert result.text == "ok"
    assert input_tokens == 42
    assert output_tokens == 7


@pytest.mark.asyncio
async def test_gemini_adapter_embed_delega_ao_embedder():
    with patch("langchain_google_genai.ChatGoogleGenerativeAI"), \
         patch("langchain_google_genai.GoogleGenerativeAIEmbeddings") as mock_embedder_cls:
        mock_embedder = MagicMock()
        mock_embedder.aembed_query = AsyncMock(return_value=[0.1, 0.2, 0.3])
        mock_embedder_cls.return_value = mock_embedder

        from core.llm_adapter import GeminiAdapter
        adapter = GeminiAdapter(api_key="fake-key")
        result = await adapter.embed("texto")

    assert result == [0.1, 0.2, 0.3]
