import structlog
from pydantic import BaseModel

from agents.state import AgentState, Task
from core.events import EventType, RunEvent, RunEventEmitter
from core.llm_adapter import BaseLLMAdapter
from core.memory import BaseMemoryRepository

logger = structlog.get_logger()


class TaskPlan(BaseModel):
    tasks: list[str]


async def supervisor_node(
    state: AgentState,
    *,
    adapter: BaseLLMAdapter,
    emitter: RunEventEmitter,
    memory_repo: BaseMemoryRepository,
    langsmith_enabled: bool = False,
) -> dict:
    memory_context = ""
    if state.get("user_id"):
        try:
            embedding = await adapter.embed(state["objective"])
            memories = await memory_repo.search(state["user_id"], embedding)
            if memories:
                memory_context = "\n".join(f"- {m}" for m in memories)
        except Exception:
            logger.exception("supervisor_memory_query_failed", run_id=state["run_id"])

    memory_block = (
        f"\nContexto de runs anteriores relevantes:\n{memory_context}\n"
        if memory_context
        else ""
    )

    prompt = (
        f"Você é um agente supervisor. Decomponha este objetivo em 2 a 4 tarefas concretas.\n"
        f"Objetivo: {state['objective']}\n"
        f"{memory_block}"
        f"\nRetorne uma lista de descrições de tarefas."
    )

    last_error = ""
    for _ in range(3):
        try:
            plan, input_tokens, output_tokens = await adapter.generate(prompt, TaskPlan, state)
            tasks = [Task(description=desc) for desc in plan.tasks]
            await emitter.emit(RunEvent(
                run_id=state["run_id"],
                type=EventType.agent_started,
                agent_name="supervisor",
                tokens_used=input_tokens + output_tokens,
                payload={
                    "agent_name": "supervisor",
                    "budget_limit": state["budget_limit"],
                    "langsmith_enabled": langsmith_enabled,
                },
            ))
            return {
                "tasks": tasks,
                "current_task_index": 0,
                "total_input_tokens": state["total_input_tokens"] + input_tokens,
                "total_output_tokens": state["total_output_tokens"] + output_tokens,
                "memory_context": memory_context,
            }
        except Exception as exc:
            last_error = str(exc)

    return {"status": "failed", "error": last_error}
