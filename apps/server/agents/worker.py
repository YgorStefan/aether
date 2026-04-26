from pydantic import BaseModel

from agents.state import AgentState, Task
from core.events import EventType, RunEvent, RunEventEmitter
from core.llm_adapter import BaseLLMAdapter


class ThinkResult(BaseModel):
    approach: str


class ObserveResult(BaseModel):
    observations: str


class DecisionResult(BaseModel):
    is_complete: bool
    result: str


class SkillResult(BaseModel):
    output: str


class MockSkill:
    async def execute(self, approach: str) -> SkillResult:
        return SkillResult(output=f"Executado: {approach}")


async def worker_node(
    state: AgentState,
    *,
    adapter: BaseLLMAdapter,
    emitter: RunEventEmitter,
    skill: MockSkill,
) -> dict:
    idx = state["current_task_index"]
    task = state["tasks"][idx]

    await emitter.emit(RunEvent(
        run_id=state["run_id"],
        type=EventType.task_started,
        payload={"task": task.description, "index": idx},
    ))

    # Think
    think_prompt = (
        f"Tarefa: {task.description}\nObjetivo: {state['objective']}\n"
        f"Como você vai abordar esta tarefa?"
    )
    think_result, i1, o1 = await adapter.generate(think_prompt, ThinkResult, state)

    # Act
    skill_result = await skill.execute(think_result.approach)

    # Observe
    observe_prompt = (
        f"Tarefa: {task.description}\nResultado da ação: {skill_result.output}\n"
        f"Quais são suas observações?"
    )
    observe_result, i2, o2 = await adapter.generate(observe_prompt, ObserveResult, state)

    # Decide
    decide_prompt = (
        f"Tarefa: {task.description}\nObservações: {observe_result.observations}\n"
        f"A tarefa está completa?"
    )
    decision, i3, o3 = await adapter.generate(decide_prompt, DecisionResult, state)

    updated_status = "done" if decision.is_complete else "failed"
    updated_tasks = list(state["tasks"])
    updated_tasks[idx] = task.model_copy(update={"result": decision.result, "status": updated_status})

    return {
        "tasks": updated_tasks,
        "total_input_tokens": state["total_input_tokens"] + i1 + i2 + i3,
        "total_output_tokens": state["total_output_tokens"] + o1 + o2 + o3,
    }
