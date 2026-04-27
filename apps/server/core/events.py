import asyncio
from collections.abc import AsyncGenerator
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    agent_started = "agent_started"
    task_started = "task_started"
    task_completed = "task_completed"
    skill_called = "skill_called"
    hitl_required = "hitl_required"
    run_completed = "run_completed"
    run_failed = "run_failed"
    budget_warning = "budget_warning"


class RunEvent(BaseModel):
    run_id: str
    type: EventType
    payload: dict[str, Any] = Field(default_factory=dict)


class RunEventEmitter:
    def __init__(self) -> None:
        self._queues: dict[str, asyncio.Queue[RunEvent | None]] = {}

    def create(self, run_id: str) -> None:
        if run_id in self._queues:
            raise ValueError(f"Queue for run_id={run_id!r} already exists")
        self._queues[run_id] = asyncio.Queue()

    async def emit(self, event: RunEvent) -> None:
        q = self._queues.get(event.run_id)
        if q:
            await q.put(event)

    async def close(self, run_id: str) -> None:
        q = self._queues.pop(run_id, None)
        if q:
            await q.put(None)

    async def listen(self, run_id: str) -> AsyncGenerator[RunEvent, None]:
        """Single consumer per run_id. Producer must call create() before this is called."""
        q = self._queues.get(run_id)
        if not q:
            return
        while True:
            event = await q.get()
            if event is None:
                break
            yield event
        self._queues.pop(run_id, None)


emitter = RunEventEmitter()
