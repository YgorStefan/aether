import pytest
from agents.graph import build_graph
from agents.state import AgentState
from agents.supervisor import TaskPlan
from agents.worker import DecisionResult, ObserveResult, SkillSelection
from core.budget import BudgetController
from core.events import RunEventEmitter
from core.llm_adapter import MockLLMAdapter
from pydantic import BaseModel
from skills.base import Skill, SkillResult
from skills.registry import SkillRegistry


class _MockParams(BaseModel):
    value: str


class _MockSkill(Skill):
    name = "mock_skill"
    description = "Skill para testes de integração"
    parameters = _MockParams
    requires_approval = False

    async def execute(self, params: BaseModel) -> SkillResult:
        return SkillResult(success=True, output="resultado_mock")


def _make_registry() -> SkillRegistry:
    r = SkillRegistry()
    r.register(_MockSkill())
    return r


def _initial_state(run_id: str = "run-1") -> AgentState:
    return {
        "run_id": run_id,
        "objective": "Objetivo simples",
        "tasks": [],
        "current_task_index": 0,
        "status": "running",
        "error": "",
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "skill_cache": {},
    }


@pytest.mark.asyncio
async def test_graph_completa_run_com_uma_tarefa():
    mock = MockLLMAdapter()
    mock.enqueue(TaskPlan, TaskPlan(tasks=["Tarefa única"]))
    mock.enqueue(SkillSelection, SkillSelection(skill_name="mock_skill", rationale="OK"))
    mock.enqueue(_MockParams, _MockParams(value="x"))
    mock.enqueue(ObserveResult, ObserveResult(observations="Funcionou"))
    mock.enqueue(DecisionResult, DecisionResult(is_complete=True, result="Pronto"))

    e = RunEventEmitter()
    e.create("run-1")
    budget = BudgetController(limit_tokens=10000)
    registry = _make_registry()
    graph = build_graph(adapter=mock, budget=budget, emitter=e, registry=registry)

    result = await graph.ainvoke(_initial_state())

    assert result["status"] == "completed"
    assert len(result["tasks"]) == 1
    assert result["tasks"][0].status == "done"
    assert result["tasks"][0].result == "Pronto"


@pytest.mark.asyncio
async def test_graph_falha_se_budget_excedido():
    mock = MockLLMAdapter()
    mock.enqueue(TaskPlan, TaskPlan(tasks=["T1"]))

    e = RunEventEmitter()
    e.create("run-1")
    budget = BudgetController(limit_tokens=1)

    state = _initial_state()
    state["total_input_tokens"] = 100  # já começa acima do limite

    registry = _make_registry()
    graph = build_graph(adapter=mock, budget=budget, emitter=e, registry=registry)

    result = await graph.ainvoke(state)
    assert result["status"] == "failed"
    assert "excedido" in result["error"].lower()
