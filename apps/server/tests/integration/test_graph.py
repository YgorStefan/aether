import pytest
from pydantic import BaseModel
from agents.graph import build_graph
from agents.state import AgentState
from agents.supervisor import TaskPlan
from agents.worker import DecisionResult, ObserveResult, SkillSelection
from core.budget import BudgetController
from core.events import RunEventEmitter
from core.llm_adapter import MockLLMAdapter
from skills.base import Skill, SkillResult
from skills.registry import SkillRegistry


class _SimpleParams(BaseModel):
    value: str


class _SimpleSkill(Skill):
    name = "simple_skill"
    description = "Skill simples de teste"
    parameters = _SimpleParams
    requires_approval = False

    async def execute(self, params: BaseModel) -> SkillResult:
        return SkillResult(success=True, output=f"ok:{params.value}")


def _make_registry() -> SkillRegistry:
    r = SkillRegistry()
    r.register(_SimpleSkill())
    return r


@pytest.mark.asyncio
async def test_graph_completa_run_com_uma_tarefa():
    mock = MockLLMAdapter()
    mock.enqueue(TaskPlan, TaskPlan(tasks=["Tarefa única"]))
    mock.enqueue(SkillSelection, SkillSelection(skill_name="simple_skill", rationale="única opção"))
    mock.enqueue(_SimpleParams, _SimpleParams(value="test"))
    mock.enqueue(ObserveResult, ObserveResult(observations="Funcionou"))
    mock.enqueue(DecisionResult, DecisionResult(is_complete=True, result="Pronto"))

    e = RunEventEmitter()
    e.create("run-1")
    budget = BudgetController(limit_tokens=10000)
    graph = build_graph(adapter=mock, budget=budget, emitter=e, registry=_make_registry())

    initial: AgentState = {
        "run_id": "run-1",
        "objective": "Objetivo simples",
        "tasks": [],
        "current_task_index": 0,
        "status": "running",
        "error": "",
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "skill_cache": {},
    }

    result = await graph.ainvoke(initial)

    assert result["status"] == "completed"
    assert len(result["tasks"]) == 1
    assert result["tasks"][0].status == "done"
    assert result["tasks"][0].result == "Pronto"


@pytest.mark.asyncio
async def test_graph_falha_se_budget_excedido():
    mock = MockLLMAdapter()
    mock.enqueue(TaskPlan, TaskPlan(tasks=["T1"]))
    mock.enqueue(SkillSelection, SkillSelection(skill_name="simple_skill", rationale="r"))
    mock.enqueue(_SimpleParams, _SimpleParams(value="x"))
    mock.enqueue(ObserveResult, ObserveResult(observations="Y"))
    mock.enqueue(DecisionResult, DecisionResult(is_complete=True, result="Z"))

    e = RunEventEmitter()
    e.create("run-1")
    budget = BudgetController(limit_tokens=1)  # impossível de satisfazer

    graph = build_graph(adapter=mock, budget=budget, emitter=e, registry=_make_registry())

    initial: AgentState = {
        "run_id": "run-1",
        "objective": "X",
        "tasks": [],
        "current_task_index": 0,
        "status": "running",
        "error": "",
        "total_input_tokens": 100,  # já começa acima do limite
        "total_output_tokens": 0,
        "skill_cache": {},
    }

    result = await graph.ainvoke(initial)
    assert result["status"] == "failed"
    assert "excedido" in result["error"].lower()
