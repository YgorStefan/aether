import pytest
from core.events import EventType, RunEvent, RunEventEmitter


@pytest.mark.asyncio
async def test_subscriber_e_chamado_para_cada_evento():
    e = RunEventEmitter()
    e.create("run-persist")

    captured: list[RunEvent] = []

    async def capture(event: RunEvent) -> None:
        captured.append(event)

    e.add_subscriber("run-persist", capture)
    await e.emit(RunEvent(run_id="run-persist", type=EventType.agent_started, agent_name="supervisor"))
    await e.emit(RunEvent(run_id="run-persist", type=EventType.task_started))

    assert len(captured) == 2
    assert captured[0].agent_name == "supervisor"
    assert captured[1].type == EventType.task_started


@pytest.mark.asyncio
async def test_subscriber_nao_e_chamado_apos_close():
    e = RunEventEmitter()
    e.create("run-close-sub")

    captured: list = []

    async def capture(event: RunEvent) -> None:
        captured.append(event)

    e.add_subscriber("run-close-sub", capture)
    await e.close("run-close-sub")

    # Tentar emitir após close não deve acionar subscriber (fila removida)
    await e.emit(RunEvent(run_id="run-close-sub", type=EventType.run_completed))
    assert len(captured) == 0
