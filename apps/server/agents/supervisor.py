from pydantic import BaseModel

from agents.state import AgentState, Task
from core.events import EventType, RunEvent, RunEventEmitter
from core.llm_adapter import BaseLLMAdapter


class TaskPlan(BaseModel):
    tasks: list[str]


async def supervisor_node(
    state: AgentState,
    *,
    adapter: BaseLLMAdapter,
    emitter: RunEventEmitter,
    langsmith_enabled: bool = False,
) -> dict:
    prompt = (
        f"Você é um agente supervisor. Decomponha este objetivo em 2 a 4 tarefas concretas.\n"
        f"Objetivo: {state['objective']}\n\n"
        f"Retorne uma lista de descrições de tarefas."
    )

    last_error = ""
    for _ in range(3):
        try:
            plan, input_tokens, output_tokens = await adapter.generate(prompt, TaskPlan, state)
            tasks = [Task(description=desc) for desc in plan.tasks]
            # Emite APÓS a chamada LLM para que tokens_used reflita o custo real
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
            }
        except Exception as exc:
            last_error = str(exc)

    return {"status": "failed", "error": last_error}
