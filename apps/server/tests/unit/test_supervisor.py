import pytest
from agents.state import AgentState, Task
from agents.supervisor import TaskPlan, supervisor_node
from core.events import EventType, RunEventEmitter
from core.llm_adapter import MockLLMAdapter


def _make_state() -> AgentState:
    return {
        "run_id": "run-1",
        "objective": "Construir um blog",
        "tasks": [],
        "current_task_index": 0,
        "status": "running",
        "error": "",
        "total_input_tokens": 0,
        "total_output_tokens": 0,
    }


@pytest.mark.asyncio
async def test_supervisor_decompoe_objetivo():
    mock = MockLLMAdapter()
    mock.enqueue(TaskPlan, TaskPlan(tasks=["Criar estrutura", "Escrever conteúdo"]))
    e = RunEventEmitter()
    e.create("run-1")

    result = await supervisor_node(_make_state(), adapter=mock, emitter=e)

    assert len(result["tasks"]) == 2
    assert result["tasks"][0].description == "Criar estrutura"
    assert result["tasks"][1].description == "Escrever conteúdo"
    assert result["current_task_index"] == 0
    assert result["total_input_tokens"] == 100
    assert result["total_output_tokens"] == 50

    # Verify agent_started event was emitted
    async def consume():
        return [evt async for evt in e.listen("run-1")]

    import asyncio
    consumer = asyncio.create_task(consume())
    await asyncio.sleep(0)  # deixa listen() capturar referência antes de close() remover
    await e.close("run-1")
    events = await consumer
    assert len(events) == 1
    assert events[0].type == EventType.agent_started
    assert events[0].payload == {"agent": "supervisor"}


@pytest.mark.asyncio
async def test_supervisor_falha_apos_3_tentativas():
    class BrokenAdapter(MockLLMAdapter):
        async def generate(self, prompt, response_model, state):
            raise RuntimeError("LLM timeout")

    e = RunEventEmitter()
    e.create("run-1")
    result = await supervisor_node(_make_state(), adapter=BrokenAdapter(), emitter=e)

    assert result["status"] == "failed"
    assert "LLM timeout" in result["error"]
