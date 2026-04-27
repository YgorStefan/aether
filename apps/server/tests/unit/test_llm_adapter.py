import pytest
from pydantic import BaseModel
from core.llm_adapter import MockLLMAdapter
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
async def test_mock_adapter_retorna_resposta_enfileirada():
    mock = MockLLMAdapter()
    mock.enqueue(_Answer, _Answer(text="hello"))
    result, input_tok, output_tok = await mock.generate("prompt", _Answer, _make_state())
    assert result.text == "hello"
    assert input_tok > 0
    assert output_tok > 0


@pytest.mark.asyncio
async def test_mock_adapter_suporta_multiplas_chamadas():
    mock = MockLLMAdapter()
    mock.enqueue(_Answer, _Answer(text="first"))
    mock.enqueue(_Answer, _Answer(text="second"))
    r1, _, _ = await mock.generate("p", _Answer, _make_state())
    r2, _, _ = await mock.generate("p", _Answer, _make_state())
    assert r1.text == "first"
    assert r2.text == "second"


@pytest.mark.asyncio
async def test_mock_adapter_levanta_se_fila_vazia():
    mock = MockLLMAdapter()
    with pytest.raises(ValueError, match="_Answer"):
        await mock.generate("p", _Answer, _make_state())
