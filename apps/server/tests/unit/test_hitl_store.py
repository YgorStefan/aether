import asyncio
import pytest
from core.hitl_store import HitlStore


@pytest.mark.asyncio
async def test_wait_resolve_retorna_approve():
    store = HitlStore()
    store.create("run-1")

    async def _resolve():
        await asyncio.sleep(0.01)
        store.resolve("run-1", "approve")

    asyncio.create_task(_resolve())
    decision = await store.wait_for_decision("run-1")
    assert decision == "approve"


@pytest.mark.asyncio
async def test_wait_resolve_retorna_reject():
    store = HitlStore()
    store.create("run-1")

    async def _resolve():
        await asyncio.sleep(0.01)
        store.resolve("run-1", "reject")

    asyncio.create_task(_resolve())
    decision = await store.wait_for_decision("run-1")
    assert decision == "reject"


@pytest.mark.asyncio
async def test_dois_hits_sequenciais_no_mesmo_run():
    store = HitlStore()
    store.create("run-1")

    async def _resolve_first():
        await asyncio.sleep(0.01)
        store.resolve("run-1", "approve")

    asyncio.create_task(_resolve_first())
    d1 = await store.wait_for_decision("run-1")
    assert d1 == "approve"

    async def _resolve_second():
        await asyncio.sleep(0.01)
        store.resolve("run-1", "reject")

    asyncio.create_task(_resolve_second())
    d2 = await store.wait_for_decision("run-1")
    assert d2 == "reject"


@pytest.mark.asyncio
async def test_wait_sem_create_retorna_approve():
    store = HitlStore()
    decision = await store.wait_for_decision("run-inexistente")
    assert decision == "approve"


def test_cleanup_remove_run():
    store = HitlStore()
    store.create("run-1")
    store.cleanup("run-1")
    assert "run-1" not in store._events
