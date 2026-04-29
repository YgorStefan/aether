import structlog
from pydantic import BaseModel

from agents.state import AgentState, Task
from core.budget import BudgetController, BudgetExceededException
from core.events import EventType, RunEvent, RunEventEmitter
from core.llm_adapter import BaseLLMAdapter
from core.memory import BaseMemoryRepository

logger = structlog.get_logger()


class FinalSynthesis(BaseModel):
    summary: str


async def evaluate_result_node(
    state: AgentState,
    *,
    emitter: RunEventEmitter,
    budget: BudgetController,
) -> dict:
    idx = state["current_task_index"]
    task = state["tasks"][idx]
    tokens_used = (state["total_input_tokens"] + state["total_output_tokens"]) - state["task_start_tokens"]

    await emitter.emit(RunEvent(
        run_id=state["run_id"],
        type=EventType.task_completed,
        agent_name=f"worker_{idx}",
        tokens_used=tokens_used,
        payload={
            "task": task.description,
            "status": task.status,
            "index": idx,
            "total_input_tokens": state["total_input_tokens"],
            "total_output_tokens": state["total_output_tokens"],
            "cost_usd": budget.cost_usd(state["total_input_tokens"], state["total_output_tokens"]),
        },
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
        total = state["total_input_tokens"] + state["total_output_tokens"]
        await emitter.emit(RunEvent(
            run_id=state["run_id"],
            type=EventType.budget_exceeded,
            payload={
                "total_tokens": total,
                "budget_limit": state["budget_limit"],
                "cost_usd": budget.cost_usd(state["total_input_tokens"], state["total_output_tokens"]),
                "error": str(exc),
            },
        ))
        return {"status": "failed", "error": str(exc)}

    if budget.is_warning(state["total_input_tokens"], state["total_output_tokens"]):
        await emitter.emit(RunEvent(
            run_id=state["run_id"],
            type=EventType.budget_warning,
            payload={
                "total_tokens": state["total_input_tokens"] + state["total_output_tokens"],
                "budget_limit": state["budget_limit"],
                "cost_usd": budget.cost_usd(
                    state["total_input_tokens"], state["total_output_tokens"]
                ),
            },
        ))
    return {"task_start_tokens": state["total_input_tokens"] + state["total_output_tokens"]}


async def finalize_node(
    state: AgentState,
    *,
    emitter: RunEventEmitter,
    budget: BudgetController,
    adapter: BaseLLMAdapter,
    memory_repo: BaseMemoryRepository,
) -> dict:
    is_failed = state["status"] == "failed"
    total_input = state["total_input_tokens"]
    total_output = state["total_output_tokens"]

    if not is_failed and state.get("user_id"):
        try:
            results_text = "\n".join(
                f"- {task.description}: {task.result}"
                for task in state["tasks"]
                if task.result
            )
            synthesis_prompt = (
                f"Objetivo original: {state['objective']}\n\n"
                f"Resultados das tarefas:\n{results_text}\n\n"
                f"Escreva um resumo final conciso do que foi alcançado."
            )
            synthesis, inp_tok, out_tok = await adapter.generate(synthesis_prompt, FinalSynthesis, state)
            total_input += inp_tok
            total_output += out_tok

            embedding = await adapter.embed(synthesis.summary)
            await memory_repo.insert(
                user_id=state["user_id"],
                run_id=state["run_id"],
                content=synthesis.summary,
                embedding=embedding,
            )
        except Exception:
            logger.exception("memory_save_failed", run_id=state["run_id"])

    event_type = EventType.run_failed if is_failed else EventType.run_completed
    payload: dict = {
        "tasks_count": len(state["tasks"]),
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "cost_usd": budget.cost_usd(total_input, total_output),
    }
    if is_failed:
        payload["error"] = state.get("error", "Erro desconhecido")

    await emitter.emit(RunEvent(
        run_id=state["run_id"],
        type=event_type,
        payload=payload,
    ))
    await emitter.close(state["run_id"])
    return {"status": "failed" if is_failed else "completed"}
