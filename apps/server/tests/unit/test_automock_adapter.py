import pytest
from pydantic import BaseModel

from agents.state import AgentState
from agents.supervisor import TaskPlan
from agents.worker import DecisionResult, ObserveResult, SkillSelection
from agents.nodes import FinalSynthesis
from core.llm_adapter import AutoMockLLMAdapter
from skills.file_writer import FileWriterParams
from skills.time_manager import TimeManagerParams


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
async def test_automock_gera_task_plan():
    adapter = AutoMockLLMAdapter()
    plan, i, o = await adapter.generate("prompt", TaskPlan, _make_state())
    assert isinstance(plan, TaskPlan)
    assert len(plan.tasks) >= 1
    assert i > 0 and o > 0


@pytest.mark.asyncio
async def test_automock_seleciona_skill_padrao_time_manager():
    adapter = AutoMockLLMAdapter()
    selection, _, _ = await adapter.generate("prompt", SkillSelection, _make_state())
    assert selection.skill_name == "time_manager"


@pytest.mark.asyncio
async def test_automock_seleciona_file_writer_quando_objetivo_menciona_arquivo():
    adapter = AutoMockLLMAdapter()
    state = _make_state()
    state["objective"] = "Crie um arquivo com um resumo"
    selection, _, _ = await adapter.generate("prompt", SkillSelection, state)
    assert selection.skill_name == "file_writer"


@pytest.mark.asyncio
async def test_automock_permite_skill_padrao_customizada():
    adapter = AutoMockLLMAdapter(default_skill_name="web_search")
    selection, _, _ = await adapter.generate("prompt", SkillSelection, _make_state())
    assert selection.skill_name == "web_search"


@pytest.mark.asyncio
async def test_automock_observe_e_decision_indicam_sucesso():
    adapter = AutoMockLLMAdapter()
    observe, _, _ = await adapter.generate("prompt", ObserveResult, _make_state())
    decision, _, _ = await adapter.generate("prompt", DecisionResult, _make_state())
    assert observe.observations
    assert decision.is_complete is True


@pytest.mark.asyncio
async def test_automock_final_synthesis():
    adapter = AutoMockLLMAdapter()
    synthesis, _, _ = await adapter.generate("prompt", FinalSynthesis, _make_state())
    assert synthesis.summary


@pytest.mark.asyncio
async def test_automock_preenche_params_de_skill_desconhecida_genericamente():
    adapter = AutoMockLLMAdapter()
    params, _, _ = await adapter.generate("prompt", TimeManagerParams, _make_state())
    assert isinstance(params, TimeManagerParams)
    assert isinstance(params.query, str) and params.query


@pytest.mark.asyncio
async def test_automock_preenche_params_com_defaults_respeitados():
    adapter = AutoMockLLMAdapter()
    params, _, _ = await adapter.generate("prompt", FileWriterParams, _make_state())
    assert isinstance(params, FileWriterParams)
    assert params.format == "md"  # default do modelo, não sobrescrito


@pytest.mark.asyncio
async def test_automock_embed_retorna_768_dims():
    adapter = AutoMockLLMAdapter()
    embedding = await adapter.embed("texto")
    assert len(embedding) == 768


@pytest.mark.asyncio
async def test_automock_generic_fill_com_tipos_variados():
    class _Generic(BaseModel):
        nome: str
        idade: int
        nota: float
        ativo: bool
        tags: list[str]

    adapter = AutoMockLLMAdapter()
    result, _, _ = await adapter.generate("p", _Generic, _make_state())
    assert isinstance(result, _Generic)
