import asyncio


class HitlStore:
    def __init__(self) -> None:
        self._events: dict[str, asyncio.Event] = {}
        self._decisions: dict[str, str] = {}

    def create(self, run_id: str) -> None:
        self._events[run_id] = asyncio.Event()

    async def wait_for_decision(self, run_id: str, timeout: float | None = None) -> str:
        event = self._events.get(run_id)
        if event is None:
            return "approve"
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            return "timeout"
        event.clear()
        return self._decisions.pop(run_id, "approve")

    def resolve(self, run_id: str, decision: str) -> None:
        self._decisions[run_id] = decision
        event = self._events.get(run_id)
        if event:
            event.set()

    def cleanup(self, run_id: str) -> None:
        self._events.pop(run_id, None)
        self._decisions.pop(run_id, None)


hitl_store = HitlStore()
