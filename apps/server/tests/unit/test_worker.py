import pytest
from agents.state import AgentState, Task
from agents.worker import (
    DecisionResult,
    MockSkill,
    ObserveResult,
    ThinkResult,
    worker_node,
)
from core.events import EventType, RunEventEmitter
from core.llm_adapter import MockLLMAdapter


def _make_state(tasks: list[Task] | None = None) -> AgentState:
    return {
        "run_id": "run-1",
        "objective": "...",
        "tasks": tasks or [Task(description="Fazer algo")],
        "current_task_index": 0,
        "status": "running",
        "error": "",
        "total_input_tokens": 0,
        "total_output_tokens": 0,
    }


@pytest.mark.asyncio
async def test_worker_completa_tarefa_com_sucesso():
    mock = MockLLMAdapter()
    mock.enqueue(ThinkResult, ThinkResult(approach="Pesquisar X"))
    mock.enqueue(ObserveResult, ObserveResult(observations="Encontrei X"))
    mock.enqueue(DecisionResult, DecisionResult(is_complete=True, result="Concluído"))

    e = RunEventEmitter()
    e.create("run-1")
    result = await worker_node(_make_state(), adapter=mock, emitter=e, skill=MockSkill())

    assert result["tasks"][0].status == "done"
    assert result["tasks"][0].result == "Concluído"
    assert result["total_input_tokens"] == 300  # 3 chamadas × 100
    assert result["total_output_tokens"] == 150  # 3 chamadas × 50

    # Verify task_started event was emitted
    assert not e._queues["run-1"].empty()
    event = e._queues["run-1"].get_nowait()
    assert event.type == EventType.task_started
    assert event.payload["index"] == 0


@pytest.mark.asyncio
async def test_worker_marca_failed_se_nao_completo():
    mock = MockLLMAdapter()
    mock.enqueue(ThinkResult, ThinkResult(approach="Tentar X"))
    mock.enqueue(ObserveResult, ObserveResult(observations="Falhou"))
    mock.enqueue(DecisionResult, DecisionResult(is_complete=False, result="Incompleto"))

    e = RunEventEmitter()
    e.create("run-1")
    result = await worker_node(_make_state(), adapter=mock, emitter=e, skill=MockSkill())

    assert result["tasks"][0].status == "failed"
    assert result["tasks"][0].result == "Incompleto"
    assert result["total_input_tokens"] == 300
    assert result["total_output_tokens"] == 150
