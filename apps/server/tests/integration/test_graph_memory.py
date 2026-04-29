import pytest
from agents.graph import build_graph
from agents.state import AgentState, Task
from agents.supervisor import TaskPlan
from agents.nodes import FinalSynthesis
from agents.worker import SkillSelection, ObserveResult, DecisionResult
from core.budget import BudgetController
from core.events import RunEventEmitter
from core.hitl_store import HitlStore
from core.llm_adapter import MockLLMAdapter
from core.memory import MockMemoryRepository
from skills.registry import SkillRegistry
from skills.time_manager import TimeManager, TimeManagerParams


def _build_mock_graph(memory_repo: MockMemoryRepository):
    mock = MockLLMAdapter()
    # Supervisor: decompõe em 1 task
    mock.enqueue(TaskPlan, TaskPlan(tasks=["Verificar hora atual"]))
    # Worker Think step 1: seleciona skill
    mock.enqueue(SkillSelection, SkillSelection(skill_name="time_manager", rationale="precisa de hora"))
    # Worker Think step 2: gera parâmetros
    mock.enqueue(TimeManagerParams, TimeManagerParams(query="que horas são agora?"))
    # Worker Observe
    mock.enqueue(ObserveResult, ObserveResult(observations="Hora verificada com sucesso"))
    # Worker Decide
    mock.enqueue(DecisionResult, DecisionResult(is_complete=True, result="Hora verificada"))
    # Finalize synthesis
    mock.enqueue(FinalSynthesis, FinalSynthesis(summary="Run concluído: hora verificada"))

    registry = SkillRegistry()
    registry.register(TimeManager())

    emitter = RunEventEmitter()
    budget = BudgetController(limit_tokens=50000)
    hitl = HitlStore()

    graph = build_graph(
        adapter=mock,
        budget=budget,
        emitter=emitter,
        registry=registry,
        hitl_store=hitl,
        memory_repo=memory_repo,
    )
    return graph, emitter


@pytest.mark.asyncio
async def test_grafo_completo_com_memoria_vazia():
    memory_repo = MockMemoryRepository()
    graph, emitter = _build_mock_graph(memory_repo)

    initial_state: AgentState = {
        "run_id": "run-integration-1",
        "user_id": "user-1",
        "objective": "Verificar hora atual",
        "tasks": [],
        "current_task_index": 0,
        "status": "running",
        "error": "",
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "skill_cache": {},
        "budget_limit": 50000,
        "task_start_tokens": 0,
        "memory_context": "",
    }

    emitter.create("run-integration-1")
    final = await graph.ainvoke(initial_state)

    assert final["status"] == "completed"
    assert len(memory_repo.saved) == 1
    assert memory_repo.saved[0]["content"] == "Run concluído: hora verificada"


@pytest.mark.asyncio
async def test_grafo_completo_salva_memoria_e_context_disponivel():
    memory_repo = MockMemoryRepository(
        memories=["Run anterior: já verificamos a hora em Tokyo às 14h"]
    )
    graph, emitter = _build_mock_graph(memory_repo)

    initial_state: AgentState = {
        "run_id": "run-integration-2",
        "user_id": "user-1",
        "objective": "Verificar hora atual",
        "tasks": [],
        "current_task_index": 0,
        "status": "running",
        "error": "",
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "skill_cache": {},
        "budget_limit": 50000,
        "task_start_tokens": 0,
        "memory_context": "",
    }

    emitter.create("run-integration-2")
    final = await graph.ainvoke(initial_state)

    assert final["status"] == "completed"
    # memory_context foi preenchido pelo supervisor com a memória semeada
    assert "Tokyo" in final["memory_context"]
    # nova memória também salva
    assert len(memory_repo.saved) == 1
