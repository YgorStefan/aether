import hashlib
import json

import structlog
from pydantic import BaseModel

from agents.state import AgentState, Task
from core.config import settings
from core.events import EventType, RunEvent, RunEventEmitter
from core.hitl_store import HitlStore
from core.llm_adapter import BaseLLMAdapter
from skills.base import Skill
from skills.registry import SkillRegistry

logger = structlog.get_logger()


class SkillSelection(BaseModel):
    skill_name: str
    rationale: str


class ObserveResult(BaseModel):
    observations: str


class DecisionResult(BaseModel):
    is_complete: bool
    result: str


class _WorkerError(Exception):
    """Erro esperado de um passo do worker; vira uma tarefa `failed`."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class _Rejected(Exception):
    """Usuário rejeitou a execução da skill via HITL."""


class _TokenCounter:
    def __init__(self, input_tokens: int, output_tokens: int) -> None:
        self.input = input_tokens
        self.output = output_tokens

    def add(self, input_tokens: int, output_tokens: int) -> None:
        self.input += input_tokens
        self.output += output_tokens


def _cache_key(skill_name: str, params: BaseModel) -> str:
    params_json = json.dumps(params.model_dump(), sort_keys=True)
    digest = hashlib.sha256(params_json.encode()).hexdigest()[:16]
    return f"{skill_name}:{digest}"


def _fail(state: AgentState, idx: int, message: str, *, total_input: int, total_output: int) -> dict:
    logger.warning("worker_task_failed", run_id=state["run_id"], task_index=idx, reason=message)
    task = state["tasks"][idx]
    updated_tasks = list(state["tasks"])
    updated_tasks[idx] = task.model_copy(update={"status": "failed", "result": message})
    return {
        "tasks": updated_tasks,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "skill_cache": state["skill_cache"],
    }


def _finish(state: AgentState, idx: int, task: Task, status: str, result: str, tokens: _TokenCounter, cache: dict) -> dict:
    updated_tasks = list(state["tasks"])
    updated_tasks[idx] = task.model_copy(update={"status": status, "result": result})
    return {
        "tasks": updated_tasks,
        "total_input_tokens": tokens.input,
        "total_output_tokens": tokens.output,
        "skill_cache": cache,
    }


async def _select_skill(
    adapter: BaseLLMAdapter, registry: SkillRegistry, state: AgentState, task: Task, tokens: _TokenCounter
) -> Skill:
    skill_list = "\n".join(f"- {m.name}: {m.description}" for m in registry.list_all())
    prompt = (
        f"Skills disponíveis:\n{skill_list}\n\n"
        f"Objetivo: {state['objective']}\n"
        f"Tarefa atual: {task.description}\n\n"
        f"Escolha a skill mais adequada para executar esta tarefa."
    )
    try:
        selection, i, o = await adapter.generate(prompt, SkillSelection, state)
    except Exception as exc:
        raise _WorkerError(f"Erro ao selecionar skill: {exc}") from exc
    tokens.add(i, o)

    try:
        return registry.get(selection.skill_name)
    except KeyError as exc:
        raise _WorkerError(str(exc)) from exc


async def _generate_params(
    adapter: BaseLLMAdapter, skill: Skill, task: Task, state: AgentState, tokens: _TokenCounter
) -> BaseModel:
    prompt = (
        f"Tarefa: {task.description}\n"
        f"Skill escolhida: {skill.name}\n"
        f"Gere os parâmetros necessários para executar esta skill."
    )
    try:
        params, i, o = await adapter.generate(prompt, skill.parameters, state)
    except Exception as exc:
        raise _WorkerError(f"Erro ao gerar parâmetros para '{skill.name}': {exc}") from exc
    tokens.add(i, o)
    return params


async def _handle_hitl(
    emitter: RunEventEmitter, hitl_store: HitlStore, state: AgentState, skill: Skill, params: BaseModel
) -> None:
    await emitter.emit(RunEvent(
        run_id=state["run_id"],
        type=EventType.hitl_required,
        payload={"skill": skill.name, "params": params.model_dump()},
    ))

    decision = await hitl_store.wait_for_decision(state["run_id"], timeout=settings.hitl_timeout_seconds)

    if decision == "timeout":
        raise _WorkerError(
            f"Aprovação para a skill '{skill.name}' expirou após "
            f"{settings.hitl_timeout_seconds}s sem resposta do usuário"
        )
    if decision == "reject":
        raise _Rejected()


async def _resolve_skill_output(
    *,
    state: AgentState,
    skill: Skill,
    params: BaseModel,
    emitter: RunEventEmitter,
    hitl_store: HitlStore,
    cache: dict,
) -> str:
    key = _cache_key(skill.name, params)
    if key in cache:
        return cache[key]

    if skill.requires_approval:
        await _handle_hitl(emitter, hitl_store, state, skill, params)

    await emitter.emit(RunEvent(
        run_id=state["run_id"],
        type=EventType.skill_called,
        payload={"skill": skill.name},
    ))

    try:
        skill_result = await skill.execute(params)
    except Exception as exc:
        raise _WorkerError(f"Erro ao executar a skill '{skill.name}': {exc}") from exc

    if not skill_result.success:
        raise _WorkerError(f"A skill '{skill.name}' falhou: {skill_result.error or 'erro desconhecido'}")

    cache[key] = skill_result.output
    return skill_result.output


async def _observe(
    adapter: BaseLLMAdapter, task: Task, skill: Skill, skill_output: str, state: AgentState, tokens: _TokenCounter
) -> ObserveResult:
    prompt = (
        f"Tarefa: {task.description}\n"
        f"Resultado da skill '{skill.name}': {skill_output}\n"
        f"Quais são suas observações sobre o resultado?"
    )
    try:
        observe_result, i, o = await adapter.generate(prompt, ObserveResult, state)
    except Exception as exc:
        raise _WorkerError(f"Erro ao observar resultado: {exc}") from exc
    tokens.add(i, o)
    return observe_result


async def _decide(
    adapter: BaseLLMAdapter, task: Task, observe_result: ObserveResult, state: AgentState, tokens: _TokenCounter
) -> DecisionResult:
    prompt = (
        f"Tarefa: {task.description}\n"
        f"Observações: {observe_result.observations}\n"
        f"A tarefa está completa com base nessas observações?"
    )
    try:
        decision_result, i, o = await adapter.generate(prompt, DecisionResult, state)
    except Exception as exc:
        raise _WorkerError(f"Erro ao decidir conclusão da tarefa: {exc}") from exc
    tokens.add(i, o)
    return decision_result


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

    tokens = _TokenCounter(state["total_input_tokens"], state["total_output_tokens"])
    updated_cache = dict(state["skill_cache"])

    try:
        skill = await _select_skill(adapter, registry, state, task, tokens)
        params = await _generate_params(adapter, skill, task, state, tokens)
        skill_output = await _resolve_skill_output(
            state=state, skill=skill, params=params,
            emitter=emitter, hitl_store=hitl_store, cache=updated_cache,
        )
        observe_result = await _observe(adapter, task, skill, skill_output, state, tokens)
        decision_result = await _decide(adapter, task, observe_result, state, tokens)
    except _Rejected:
        return _finish(state, idx, task, "failed", "Usuário rejeitou a execução da skill", tokens, updated_cache)
    except _WorkerError as exc:
        return _fail(state, idx, exc.message, total_input=tokens.input, total_output=tokens.output)

    status = "done" if decision_result.is_complete else "failed"
    return _finish(state, idx, task, status, decision_result.result, tokens, updated_cache)
