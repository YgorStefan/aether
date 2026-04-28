import hashlib
import json

from pydantic import BaseModel

from agents.state import AgentState, Task
from core.events import EventType, RunEvent, RunEventEmitter
from core.hitl_store import HitlStore
from core.llm_adapter import BaseLLMAdapter
from skills.registry import SkillRegistry


class SkillSelection(BaseModel):
    skill_name: str
    rationale: str


class ObserveResult(BaseModel):
    observations: str


class DecisionResult(BaseModel):
    is_complete: bool
    result: str


def _cache_key(skill_name: str, params: BaseModel) -> str:
    params_json = json.dumps(params.model_dump(), sort_keys=True)
    digest = hashlib.sha256(params_json.encode()).hexdigest()[:16]
    return f"{skill_name}:{digest}"


async def worker_node(
    state: AgentState,
    *,
    adapter: BaseLLMAdapter,
    emitter: RunEventEmitter,
    registry: SkillRegistry,
    hitl_store: HitlStore,
) -> dict:
    idx = state["current_task_index"]
    task = state["tasks"][idx]

    await emitter.emit(RunEvent(
        run_id=state["run_id"],
        type=EventType.task_started,
        payload={"task": task.description, "index": idx},
    ))

    total_input = state["total_input_tokens"]
    total_output = state["total_output_tokens"]

    # Think step 1: selecionar skill
    skill_list = "\n".join(
        f"- {m.name}: {m.description}" for m in registry.list_all()
    )
    selection_prompt = (
        f"Skills disponíveis:\n{skill_list}\n\n"
        f"Objetivo: {state['objective']}\n"
        f"Tarefa atual: {task.description}\n\n"
        f"Escolha a skill mais adequada para executar esta tarefa."
    )
    selection, i1, o1 = await adapter.generate(selection_prompt, SkillSelection, state)
    total_input += i1
    total_output += o1

    skill = registry.get(selection.skill_name)

    # Think step 2: gerar parâmetros no schema da skill
    params_prompt = (
        f"Tarefa: {task.description}\n"
        f"Skill escolhida: {skill.name}\n"
        f"Gere os parâmetros necessários para executar esta skill."
    )
    params, i2, o2 = await adapter.generate(params_prompt, skill.parameters, state)
    total_input += i2
    total_output += o2

    # Cache check
    key = _cache_key(skill.name, params)
    updated_cache = dict(state["skill_cache"])

    if key in updated_cache:
        skill_output = updated_cache[key]
    else:
        if skill.requires_approval:
            await emitter.emit(RunEvent(
                run_id=state["run_id"],
                type=EventType.hitl_required,
                payload={"skill": skill.name, "params": params.model_dump()},
            ))

            decision = await hitl_store.wait_for_decision(state["run_id"])

            if decision == "reject":
                updated_tasks = list(state["tasks"])
                updated_tasks[idx] = task.model_copy(
                    update={"status": "failed", "result": "Usuário rejeitou a execução da skill"}
                )
                return {
                    "tasks": updated_tasks,
                    "total_input_tokens": total_input,
                    "total_output_tokens": total_output,
                    "skill_cache": updated_cache,
                }

        await emitter.emit(RunEvent(
            run_id=state["run_id"],
            type=EventType.skill_called,
            payload={"skill": skill.name},
        ))

        skill_result = await skill.execute(params)
        skill_output = skill_result.output
        updated_cache[key] = skill_output

    # Observe
    observe_prompt = (
        f"Tarefa: {task.description}\n"
        f"Resultado da skill '{skill.name}': {skill_output}\n"
        f"Quais são suas observações sobre o resultado?"
    )
    observe_result, i3, o3 = await adapter.generate(observe_prompt, ObserveResult, state)
    total_input += i3
    total_output += o3

    # Decide
    decide_prompt = (
        f"Tarefa: {task.description}\n"
        f"Observações: {observe_result.observations}\n"
        f"A tarefa está completa com base nessas observações?"
    )
    decision_result, i4, o4 = await adapter.generate(decide_prompt, DecisionResult, state)
    total_input += i4
    total_output += o4

    updated_status = "done" if decision_result.is_complete else "failed"
    updated_tasks = list(state["tasks"])
    updated_tasks[idx] = task.model_copy(
        update={"result": decision_result.result, "status": updated_status}
    )

    return {
        "tasks": updated_tasks,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "skill_cache": updated_cache,
    }
