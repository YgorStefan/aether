import pytest
from agents.nodes import budget_gate_node, evaluate_result_node, finalize_node
from agents.state import AgentState, Task
from core.budget import BudgetController
from core.events import EventType, RunEventEmitter


def _make_state(**overrides) -> AgentState:
    base: AgentState = {
        "run_id": "run-1",
        "user_id": "user-1",
        "objective": "test",
        "tasks": [Task(description="T1", status="done")],
        "current_task_index": 0,
        "status": "running",
        "error": "",
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "skill_cache": {},
        "budget_limit": 10000,
        "task_start_tokens": 0,
        "memory_context": "",
    }
    return {**base, **overrides}


@pytest.mark.asyncio
async def test_evaluate_incrementa_indice_quando_done():
    e = RunEventEmitter()
    e.create("run-1")
    budget = BudgetController(limit_tokens=10000)
    result = await evaluate_result_node(_make_state(), emitter=e, budget=budget)
    assert result["current_task_index"] == 1


@pytest.mark.asyncio
async def test_evaluate_marca_failed_quando_tarefa_failed():
    e = RunEventEmitter()
    e.create("run-1")
    budget = BudgetController(limit_tokens=10000)
    state = _make_state(tasks=[Task(description="T1", status="failed")])
    result = await evaluate_result_node(state, emitter=e, budget=budget)
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
    budget = BudgetController(limit_tokens=10000)
    result = await finalize_node(_make_state(), emitter=e, budget=budget)
    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_finalize_emite_run_failed_quando_status_failed():
    e = RunEventEmitter()
    e.create("run-1")
    budget = BudgetController(limit_tokens=10000)
    state = _make_state(status="failed", error="algo deu errado")
    result = await finalize_node(state, emitter=e, budget=budget)
    assert result["status"] == "failed"


@pytest.mark.asyncio
async def test_budget_gate_emite_budget_exceeded_ao_exceder():
    e = RunEventEmitter()
    e.create("run-1")
    budget = BudgetController(limit_tokens=100)
    state = _make_state(total_input_tokens=80, total_output_tokens=50)  # 130 > 100
    result = await budget_gate_node(state, budget=budget, emitter=e)
    assert result["status"] == "failed"
    event = e._queues["run-1"].get_nowait()
    assert event.type == EventType.budget_exceeded
    assert "cost_usd" in event.payload
    assert "total_tokens" in event.payload


@pytest.mark.asyncio
async def test_evaluate_inclui_token_totals_no_task_completed():
    e = RunEventEmitter()
    e.create("run-1")
    budget = BudgetController(limit_tokens=10000)
    state = _make_state(total_input_tokens=200, total_output_tokens=100)
    await evaluate_result_node(state, emitter=e, budget=budget)
    event = e._queues["run-1"].get_nowait()
    assert event.type == EventType.task_completed
    assert event.agent_name == "worker_0"
    assert event.tokens_used == 300  # (200 + 100) - task_start_tokens(0)
    assert event.payload["total_input_tokens"] == 200
    assert event.payload["total_output_tokens"] == 100
    assert "cost_usd" in event.payload


@pytest.mark.asyncio
async def test_finalize_inclui_token_totals_no_run_completed():
    e = RunEventEmitter()
    e.create("run-1")
    # Captura referência à fila antes de finalize_node chamar close() (que remove a chave do dict)
    queue = e._queues["run-1"]
    budget = BudgetController(limit_tokens=10000)
    state = _make_state(total_input_tokens=500, total_output_tokens=250)
    await finalize_node(state, emitter=e, budget=budget)
    # O evento run_completed é o último antes do None
    events: list = []
    while not queue.empty():
        ev = queue.get_nowait()
        if ev is not None:
            events.append(ev)
    completed = next(ev for ev in events if ev.type == EventType.run_completed)
    assert completed.payload["total_input_tokens"] == 500
    assert completed.payload["total_output_tokens"] == 250
    assert "cost_usd" in completed.payload
