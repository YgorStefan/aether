import pytest
from agents.nodes import budget_gate_node, evaluate_result_node, finalize_node
from agents.state import AgentState, Task
from core.budget import BudgetController
from core.events import EventType, RunEventEmitter


def _make_state(**overrides) -> AgentState:
    base: AgentState = {
        "run_id": "run-1",
        "objective": "test",
        "tasks": [Task(description="T1", status="done")],
        "current_task_index": 0,
        "status": "running",
        "error": "",
        "total_input_tokens": 0,
        "total_output_tokens": 0,
    }
    return {**base, **overrides}


@pytest.mark.asyncio
async def test_evaluate_incrementa_indice_quando_done():
    e = RunEventEmitter()
    e.create("run-1")
    result = await evaluate_result_node(_make_state(), emitter=e)
    assert result["current_task_index"] == 1


@pytest.mark.asyncio
async def test_evaluate_marca_failed_quando_tarefa_failed():
    e = RunEventEmitter()
    e.create("run-1")
    state = _make_state(tasks=[Task(description="T1", status="failed")])
    result = await evaluate_result_node(state, emitter=e)
    assert result["status"] == "failed"
    assert "T1" in result["error"] or "0" in result["error"]


@pytest.mark.asyncio
async def test_budget_gate_passa_dentro_do_limite():
    e = RunEventEmitter()
    e.create("run-1")
    budget = BudgetController(limit_tokens=10000)
    state = _make_state(total_input_tokens=100, total_output_tokens=50)
    result = await budget_gate_node(state, budget=budget, emitter=e)
    assert "status" not in result  # gate passed, no state mutation


@pytest.mark.asyncio
async def test_budget_gate_falha_quando_excede_limite():
    e = RunEventEmitter()
    e.create("run-1")
    budget = BudgetController(limit_tokens=100)
    state = _make_state(total_input_tokens=80, total_output_tokens=50)  # 130 > 100
    result = await budget_gate_node(state, budget=budget, emitter=e)
    assert result["status"] == "failed"


@pytest.mark.asyncio
async def test_budget_gate_emite_warning_proximo_do_limite():
    e = RunEventEmitter()
    e.create("run-1")
    budget = BudgetController(limit_tokens=200)
    state = _make_state(total_input_tokens=160, total_output_tokens=20)  # 180/200 = 90% > 80%
    await budget_gate_node(state, budget=budget, emitter=e)
    event = e._queues["run-1"].get_nowait()
    assert event.type == EventType.budget_warning
    assert "cost_usd" in event.payload


@pytest.mark.asyncio
async def test_finalize_emite_run_completed():
    e = RunEventEmitter()
    e.create("run-1")
    result = await finalize_node(_make_state(), emitter=e)
    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_finalize_emite_run_failed_quando_status_failed():
    e = RunEventEmitter()
    e.create("run-1")
    state = _make_state(status="failed", error="algo deu errado")
    result = await finalize_node(state, emitter=e)
    assert result["status"] == "failed"
