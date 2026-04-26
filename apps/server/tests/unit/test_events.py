import asyncio

import pytest
from core.events import EventType, RunEvent, RunEventEmitter


@pytest.mark.asyncio
async def test_emitter_recebe_e_entrega_eventos():
    e = RunEventEmitter()
    e.create("run-1")
    await e.emit(RunEvent(run_id="run-1", type=EventType.agent_started))
    await e.emit(RunEvent(run_id="run-1", type=EventType.run_completed))

    async def consume():
        return [evt async for evt in e.listen("run-1")]

    consumer = asyncio.create_task(consume())
    await asyncio.sleep(0)  # deixa listen() capturar referência antes de close() remover
    await e.close("run-1")
    events = await consumer

    assert len(events) == 2
    assert events[0].type == EventType.agent_started
    assert events[1].type == EventType.run_completed


@pytest.mark.asyncio
async def test_emitter_fila_desconhecida_nao_falha():
    e = RunEventEmitter()
    # listen em run_id sem create deve retornar imediatamente
    events = []
    async for event in e.listen("nao-existe"):
        events.append(event)
    assert events == []


def test_create_duplicado_lanca_value_error():
    e = RunEventEmitter()
    e.create("run-1")
    with pytest.raises(ValueError, match="run-1"):
        e.create("run-1")


@pytest.mark.asyncio
async def test_close_without_listen_cleans_up():
    from core.events import RunEventEmitter
    e = RunEventEmitter()
    e.create("run-x")
    await e.close("run-x")
    assert "run-x" not in e._queues
