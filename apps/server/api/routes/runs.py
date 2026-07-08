import asyncio
import json
import uuid
from typing import Annotated, Literal

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from agents.graph import build_graph
from agents.state import AgentState
from api.deps import registry
from api.middleware.auth import get_current_user
from api.middleware.rate_limit import limiter
from core.budget import BudgetController
from core.config import settings
from core.crypto import decrypt
from core.events import EventType, RunEvent, emitter
from core.hitl_store import hitl_store
from core.llm_adapter import AutoMockLLMAdapter, GeminiAdapter
from core.memory import MemoryRepository
from core.security import InjectionDetected, check_prompt
from core.supabase_client import get_service_client
from skills.memory_recall import MemoryRecall

logger = structlog.get_logger()

router = APIRouter(tags=["runs"])

_background_tasks: set[asyncio.Task] = set()

_RUN_NOT_FOUND = "Run não encontrada"
_NOT_FOUND_RESPONSES = {404: {"description": _RUN_NOT_FOUND}}

CurrentUser = Annotated[dict, Depends(get_current_user)]


class RunRequest(BaseModel):
    objective: str = Field(..., min_length=10, max_length=500)


class ApproveRequest(BaseModel):
    decision: Literal["approve", "reject"]


def _validate_objective(objective: str) -> None:
    try:
        check_prompt(objective)
    except InjectionDetected:
        raise HTTPException(status_code=400, detail="Prompt injection detectado")


async def _insert_run(run_id: str, user_id: str, objective: str) -> None:
    try:
        supabase = get_service_client()
        await asyncio.to_thread(
            lambda: supabase.table("runs")
            .insert({"id": run_id, "user_id": user_id, "objective": objective, "status": "RUNNING"})
            .execute()
        )
    except Exception as exc:
        logger.exception("run_insert_failed", run_id=run_id)
        raise HTTPException(status_code=500, detail="Erro ao criar run") from exc


def _make_event_persister(sb):
    async def _persist_event(event: RunEvent) -> None:
        try:
            row = {
                "run_id": event.run_id,
                "type": event.type.value,
                "agent_name": event.agent_name,
                "payload": event.payload,
                "tokens_used": event.tokens_used,
            }
            await asyncio.to_thread(lambda: sb.table("run_events").insert(row).execute())
        except Exception:
            logger.exception("event_persist_failed", run_id=event.run_id, type=event.type.value)

    return _persist_event


def _build_initial_state(run_id: str, user_id: str, objective: str) -> AgentState:
    return {
        "run_id": run_id,
        "user_id": user_id,
        "objective": objective,
        "tasks": [],
        "current_task_index": 0,
        "status": "running",
        "error": "",
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "skill_cache": {},
        "budget_limit": settings.default_budget_limit,
        "task_start_tokens": 0,
        "memory_context": "",
    }


async def _update_run_status_safe(run_id: str, fields: dict) -> None:
    try:
        sb = get_service_client()
        await asyncio.to_thread(
            lambda: sb.table("runs").update(fields).eq("id", run_id).execute()
        )
    except Exception:
        logger.exception("run_status_update_failed", run_id=run_id)


async def _resolve_adapter(run_id: str, user_id: str):
    """Retorna o adapter LLM a usar, ou None se o run já foi encerrado (ex.: sem API key)."""
    if settings.use_mock_llm:
        # Somente para testes locais (E2E, carga, UAT) — nunca em produção.
        logger.warning("use_mock_llm_active", run_id=run_id)
        return AutoMockLLMAdapter()

    sb_keys = get_service_client()
    key_result = await asyncio.to_thread(
        lambda: sb_keys.table("user_settings")
        .select("provider, api_key")
        .eq("user_id", user_id)
        .execute()
    )
    if not key_result.data:
        await emitter.emit(RunEvent(
            run_id=run_id,
            type=EventType.run_failed,
            payload={"error": "Configure sua API key nas configurações antes de criar um run."},
        ))
        sb = get_service_client()
        await asyncio.to_thread(
            lambda: sb.table("runs").update({"status": "FAILED"}).eq("id", run_id).execute()
        )
        return None

    key_row = key_result.data[0]
    if key_row["provider"] != "gemini":
        raise ValueError(f"Provider não suportado: {key_row['provider']}")
    return GeminiAdapter(api_key=decrypt(key_row["api_key"]))


async def _execute_graph(run_id: str, user_id: str, initial_state: AgentState, adapter) -> None:
    budget = BudgetController(limit_tokens=settings.default_budget_limit)
    memory_repo = MemoryRepository(threshold=settings.memory_similarity_threshold)

    run_registry = registry.clone()
    memory_skill = MemoryRecall(memory_repo=memory_repo, user_id=user_id, adapter=adapter)
    run_registry.register(memory_skill)

    graph = build_graph(
        adapter=adapter, budget=budget, emitter=emitter,
        registry=run_registry, hitl_store=hitl_store,
        memory_repo=memory_repo,
        langsmith_enabled=bool(settings.langsmith_api_key),
    )
    final_state = await graph.ainvoke(initial_state)
    db_status = "FAILED" if final_state.get("status") == "failed" else "COMPLETED"
    total_input = final_state.get("total_input_tokens", 0)
    total_output = final_state.get("total_output_tokens", 0)
    cost = budget.cost_usd(total_input, total_output)
    await _update_run_status_safe(run_id, {
        "status": db_status,
        "total_tokens": total_input + total_output,
        "cost_usd": float(cost),
    })


async def _run_graph_in_background(run_id: str, user_id: str, initial_state: AgentState) -> None:
    try:
        adapter = await _resolve_adapter(run_id, user_id)
        if adapter is None:
            return
        await _execute_graph(run_id, user_id, initial_state, adapter)
    except Exception:
        logger.exception("run_failed", run_id=run_id)
        await _update_run_status_safe(run_id, {"status": "FAILED"})
    finally:
        hitl_store.cleanup(run_id)


@router.post(
    "/runs",
    status_code=202,
    responses={
        400: {"description": "Prompt injection detectado"},
        500: {"description": "Erro ao criar run"},
    },
)
@limiter.limit("5/minute")
async def create_run(
    request: Request,
    body: RunRequest,
    user: CurrentUser,
) -> dict:
    _validate_objective(body.objective)

    run_id = str(uuid.uuid4())
    await _insert_run(run_id, user["sub"], body.objective)

    emitter.create(run_id)
    hitl_store.create(run_id)
    emitter.add_subscriber(run_id, _make_event_persister(get_service_client()))

    initial_state = _build_initial_state(run_id, user["sub"], body.objective)

    task = asyncio.create_task(_run_graph_in_background(run_id, user["sub"], initial_state))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    return {"run_id": run_id}


@router.get("/runs/{run_id}/stream", responses=_NOT_FOUND_RESPONSES)
async def stream_run(
    run_id: str,
    user: CurrentUser,
) -> EventSourceResponse:
    supabase = get_service_client()
    result = await asyncio.to_thread(
        lambda: supabase.table("runs").select("id").eq("id", run_id).eq("user_id", user["sub"]).execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail=_RUN_NOT_FOUND)

    async def event_generator():
        if not emitter.is_active(run_id):
            # A run já terminou (e a fila em memória foi encerrada) antes desta conexão
            # SSE começar — comum quando a execução é muito rápida (ex.: modo mock).
            # Sem isso, o cliente ficaria esperando eventos que nunca chegariam.
            history = await asyncio.to_thread(
                lambda: supabase.table("run_events")
                .select("run_id, type, agent_name, tokens_used, payload")
                .eq("run_id", run_id)
                .order("created_at")
                .execute()
            )
            for row in history.data:
                yield {"event": row["type"], "data": json.dumps(row)}
            return

        async for event in emitter.listen(run_id):
            yield {"event": event.type.value, "data": event.model_dump_json()}

    return EventSourceResponse(event_generator())


@router.post("/runs/{run_id}/approve", status_code=200, responses=_NOT_FOUND_RESPONSES)
@limiter.limit("20/minute")
async def approve_run(
    request: Request,
    run_id: str,
    body: ApproveRequest,
    user: CurrentUser,
) -> dict:
    supabase = get_service_client()
    result = await asyncio.to_thread(
        lambda: supabase.table("runs").select("id").eq("id", run_id).eq("user_id", user["sub"]).execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail=_RUN_NOT_FOUND)

    await emitter.emit(RunEvent(
        run_id=run_id,
        type=EventType.hitl_resolved,
        payload={"decision": body.decision},
    ))
    hitl_store.resolve(run_id, body.decision)

    return {"ok": True}


@router.get("/runs/{run_id}/events", responses=_NOT_FOUND_RESPONSES)
async def get_run_events(
    run_id: str,
    user: CurrentUser,
) -> list[dict]:
    supabase = get_service_client()
    result = await asyncio.to_thread(
        lambda: supabase.table("runs").select("id").eq("id", run_id).eq("user_id", user["sub"]).execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail=_RUN_NOT_FOUND)

    events_result = await asyncio.to_thread(
        lambda: supabase.table("run_events")
        .select("*")
        .eq("run_id", run_id)
        .order("created_at")
        .execute()
    )
    return events_result.data
