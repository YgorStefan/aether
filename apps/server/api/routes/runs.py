import asyncio
import uuid
from typing import Literal

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse
from supabase import create_client

from agents.graph import build_graph
from agents.state import AgentState
from api.deps import registry
from api.middleware.auth import get_current_user
from api.middleware.rate_limit import limiter
from core.budget import BudgetController
from core.config import settings
from core.events import EventType, RunEvent, emitter
from core.hitl_store import hitl_store
from core.llm_adapter import GeminiAdapter
from core.security import InjectionDetected, check_prompt

logger = structlog.get_logger()

router = APIRouter(tags=["runs"])

_background_tasks: set[asyncio.Task] = set()


class RunRequest(BaseModel):
    objective: str = Field(..., min_length=10, max_length=500)


class ApproveRequest(BaseModel):
    decision: Literal["approve", "reject"]


@router.post("/runs", status_code=202)
@limiter.limit("5/minute")
async def create_run(
    request: Request,
    body: RunRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    try:
        check_prompt(body.objective)
    except InjectionDetected:
        raise HTTPException(status_code=400, detail="Prompt injection detectado")

    run_id = str(uuid.uuid4())

    try:
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        supabase.table("runs").insert(
            {"id": run_id, "user_id": user["sub"], "objective": body.objective, "status": "RUNNING"}
        ).execute()
    except Exception as exc:
        logger.exception("run_insert_failed", run_id=run_id)
        raise HTTPException(status_code=500, detail="Erro ao criar run") from exc

    emitter.create(run_id)
    hitl_store.create(run_id)

    _persist_sb = create_client(settings.supabase_url, settings.supabase_service_key)

    async def _persist_event(event: RunEvent) -> None:
        try:
            row = {
                "run_id": event.run_id,
                "type": event.type.value,
                "agent_name": event.agent_name,
                "payload": event.payload,
                "tokens_used": event.tokens_used,
            }
            await asyncio.to_thread(
                lambda: _persist_sb.table("run_events").insert(row).execute()
            )
        except Exception:
            logger.exception("event_persist_failed", run_id=event.run_id, type=event.type.value)

    emitter.add_subscriber(run_id, _persist_event)

    initial_state: AgentState = {
        "run_id": run_id,
        "objective": body.objective,
        "tasks": [],
        "current_task_index": 0,
        "status": "running",
        "error": "",
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "skill_cache": {},
        "budget_limit": settings.default_budget_limit,
        "task_start_tokens": 0,
    }

    async def _run() -> None:
        try:
            adapter = GeminiAdapter(api_key=settings.gemini_api_key)
            budget = BudgetController(limit_tokens=settings.default_budget_limit)
            graph = build_graph(
                adapter=adapter, budget=budget, emitter=emitter,
                registry=registry, hitl_store=hitl_store,
                langsmith_enabled=bool(settings.langsmith_api_key),
            )
            final_state = await graph.ainvoke(initial_state)
            db_status = "FAILED" if final_state.get("status") == "failed" else "COMPLETED"
            total_input = final_state.get("total_input_tokens", 0)
            total_output = final_state.get("total_output_tokens", 0)
            cost = budget.cost_usd(total_input, total_output)
            try:
                supabase_inner = create_client(settings.supabase_url, settings.supabase_service_key)
                supabase_inner.table("runs").update({
                    "status": db_status,
                    "total_tokens": total_input + total_output,
                    "cost_usd": float(cost),
                }).eq("id", run_id).execute()
            except Exception:
                logger.exception("run_status_update_failed", run_id=run_id)
        except Exception:
            logger.exception("run_failed", run_id=run_id)
            try:
                supabase_inner = create_client(settings.supabase_url, settings.supabase_service_key)
                supabase_inner.table("runs").update({"status": "FAILED"}).eq("id", run_id).execute()
            except Exception:
                logger.exception("run_status_update_failed", run_id=run_id)
        finally:
            hitl_store.cleanup(run_id)

    task = asyncio.create_task(_run())
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    return {"run_id": run_id}


@router.get("/runs/{run_id}/stream")
async def stream_run(
    run_id: str,
    user: dict = Depends(get_current_user),
) -> EventSourceResponse:
    supabase = create_client(settings.supabase_url, settings.supabase_service_key)
    result = supabase.table("runs").select("id").eq("id", run_id).eq("user_id", user["sub"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Run não encontrada")

    async def event_generator():
        async for event in emitter.listen(run_id):
            yield {"event": event.type.value, "data": event.model_dump_json()}

    return EventSourceResponse(event_generator())


@router.post("/runs/{run_id}/approve", status_code=200)
@limiter.limit("20/minute")
async def approve_run(
    request: Request,
    run_id: str,
    body: ApproveRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    supabase = create_client(settings.supabase_url, settings.supabase_service_key)
    result = supabase.table("runs").select("id").eq("id", run_id).eq("user_id", user["sub"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Run não encontrada")

    await emitter.emit(RunEvent(
        run_id=run_id,
        type=EventType.hitl_resolved,
        payload={"decision": body.decision},
    ))
    hitl_store.resolve(run_id, body.decision)

    return {"ok": True}


@router.get("/runs/{run_id}/events")
async def get_run_events(
    run_id: str,
    user: dict = Depends(get_current_user),
) -> list[dict]:
    supabase = create_client(settings.supabase_url, settings.supabase_service_key)
    result = supabase.table("runs").select("id").eq("id", run_id).eq("user_id", user["sub"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Run não encontrada")

    events_result = (
        supabase.table("run_events")
        .select("*")
        .eq("run_id", run_id)
        .order("created_at")
        .execute()
    )
    return events_result.data
