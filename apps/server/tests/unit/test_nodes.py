import pytest
from agents.nodes import budget_gate_node, evaluate_result_node, finalize_node
from agents.state import AgentState, Task
from core.budget import BudgetController
from core.events import EventType, RunEventEmitter
from core.llm_adapter import MockLLMAdapter
from core.memory import MockMemoryRepository


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
    # user_id="" skips memory synthesis path (no FinalSynthesis enqueued)
    result = await finalize_node(
        _make_state(user_id=""), emitter=e, budget=budget,
        adapter=MockLLMAdapter(), memory_repo=MockMemoryRepository()
    )
    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_finalize_emite_run_failed_quando_status_failed():
    e = RunEventEmitter()
    e.create("run-1")
    budget = BudgetController(limit_tokens=10000)
    # user_id="" skips memory synthesis path
    state = _make_state(status="failed", error="algo deu errado", user_id="")
    result = await finalize_node(
        state, emitter=e, budget=budget,
        adapter=MockLLMAdapter(), memory_repo=MockMemoryRepository()
    )
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
    from agents.nodes import FinalSynthesis
    e = RunEventEmitter()
    e.create("run-1")
    # Captura referência à fila antes de finalize_node chamar close()
    queue = e._queues["run-1"]
    budget = BudgetController(limit_tokens=10000)
    # user_id="user-1" (default) → enters synthesis path → MockAdapter returns (FinalSynthesis, 100, 50)
    # final tokens: input=500+100=600, output=250+50=300
    mock_adapter = MockLLMAdapter()
    mock_adapter.enqueue(FinalSynthesis, FinalSynthesis(summary="Resumo"))
    state = _make_state(total_input_tokens=500, total_output_tokens=250)
    await finalize_node(
        state, emitter=e, budget=budget,
        adapter=mock_adapter, memory_repo=MockMemoryRepository()
    )
    events: list = []
    while not queue.empty():
        ev = queue.get_nowait()
        if ev is not None:
            events.append(ev)
    completed = next(ev for ev in events if ev.type == EventType.run_completed)
    assert completed.payload["total_input_tokens"] == 600   # 500 + 100 (síntese)
    assert completed.payload["total_output_tokens"] == 300  # 250 + 50 (síntese)
    assert "cost_usd" in completed.payload


@pytest.mark.asyncio
async def test_finalize_salva_memoria_em_run_bem_sucedido():
    from agents.nodes import FinalSynthesis

    e = RunEventEmitter()
    e.create("run-1")

    mock_adapter = MockLLMAdapter()
    mock_adapter.enqueue(FinalSynthesis, FinalSynthesis(summary="Blog criado com sucesso"))

    memory_repo = MockMemoryRepository()
    budget = BudgetController(limit_tokens=10000)

    state = _make_state(
        user_id="user-1",
        tasks=[Task(description="T1", result="Artigo escrito", status="done")],
    )
    await finalize_node(state, emitter=e, budget=budget, adapter=mock_adapter, memory_repo=memory_repo)

    assert len(memory_repo.saved) == 1
    assert memory_repo.saved[0]["user_id"] == "user-1"
    assert memory_repo.saved[0]["content"] == "Blog criado com sucesso"


@pytest.mark.asyncio
async def test_finalize_nao_salva_memoria_em_run_falho():
    e = RunEventEmitter()
    e.create("run-1")

    mock_adapter = MockLLMAdapter()
    memory_repo = MockMemoryRepository()
    budget = BudgetController(limit_tokens=10000)

    state = _make_state(status="failed", error="algo deu errado", user_id="")
    await finalize_node(state, emitter=e, budget=budget, adapter=mock_adapter, memory_repo=memory_repo)

    assert len(memory_repo.saved) == 0


@pytest.mark.asyncio
async def test_finalize_continua_mesmo_se_memoria_falhar():
    from agents.nodes import FinalSynthesis

    e = RunEventEmitter()
    e.create("run-1")

    class FailingMemoryRepo(MockMemoryRepository):
        async def insert(self, *args, **kwargs):
            raise RuntimeError("Supabase offline")

    mock_adapter = MockLLMAdapter()
    mock_adapter.enqueue(FinalSynthesis, FinalSynthesis(summary="Resumo"))

    budget = BudgetController(limit_tokens=10000)
    state = _make_state(user_id="user-1")
    result = await finalize_node(
        state, emitter=e, budget=budget, adapter=mock_adapter, memory_repo=FailingMemoryRepo()
    )

    assert result["status"] == "completed"
