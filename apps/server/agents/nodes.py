from agents.state import AgentState
from core.budget import BudgetController, BudgetExceededException
from core.events import EventType, RunEvent, RunEventEmitter


async def evaluate_result_node(
    state: AgentState,
    *,
    emitter: RunEventEmitter,
) -> dict:
    idx = state["current_task_index"]
    task = state["tasks"][idx]

    await emitter.emit(RunEvent(
        run_id=state["run_id"],
        type=EventType.task_completed,
        payload={"task": task.description, "status": task.status, "index": idx},
    ))

    if task.status == "done":
        return {"current_task_index": idx + 1}
    return {"status": "failed", "error": f"Tarefa {idx} ({task.description}) falhou"}


async def budget_gate_node(
    state: AgentState,
    *,
    budget: BudgetController,
    emitter: RunEventEmitter,
) -> dict:
    try:
        budget.add_tokens(state["total_input_tokens"], state["total_output_tokens"])
    except BudgetExceededException as exc:
        return {"status": "failed", "error": str(exc)}

    if budget.is_warning(state["total_input_tokens"], state["total_output_tokens"]):
        await emitter.emit(RunEvent(
            run_id=state["run_id"],
            type=EventType.budget_warning,
            payload={
                "cost_usd": budget.cost_usd(
                    state["total_input_tokens"], state["total_output_tokens"]
                )
            },
        ))
    return {}


async def finalize_node(
    state: AgentState,
    *,
    emitter: RunEventEmitter,
) -> dict:
    is_failed = state["status"] == "failed"
    event_type = EventType.run_failed if is_failed else EventType.run_completed
    payload: dict = {"tasks_count": len(state["tasks"])}
    if is_failed:
        payload["error"] = state.get("error", "Erro desconhecido")
    await emitter.emit(RunEvent(
        run_id=state["run_id"],
        type=event_type,
        payload=payload,
    ))
    await emitter.close(state["run_id"])
    return {"status": "failed" if is_failed else "completed"}
