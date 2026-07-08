import asyncio

import structlog
from fastapi import APIRouter, Depends, Query

from api.middleware.auth import get_current_user, require_admin
from core.supabase_client import get_service_client

logger = structlog.get_logger()

router = APIRouter(tags=["admin"])


def _sb():
    return get_service_client()


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)) -> dict:
    """Retorna email e role do usuário autenticado (usado pelo frontend p/ exibir o nav de admin)."""
    supabase = _sb()
    result = await asyncio.to_thread(
        lambda: supabase.table("profiles").select("email, role").eq("user_id", user["sub"]).execute()
    )
    if not result.data:
        return {"email": user.get("email", ""), "role": "user"}
    row = result.data[0]
    return {"email": row["email"], "role": row["role"]}


@router.get("/admin/users")
async def list_users(_: dict = Depends(require_admin)) -> list[dict]:
    """Visão geral somente leitura de todos os usuários e a contagem de runs de cada um."""
    supabase = _sb()
    profiles = (
        await asyncio.to_thread(
            lambda: supabase.table("profiles")
            .select("user_id, email, role, created_at")
            .order("created_at", desc=True)
            .execute()
        )
    ).data or []
    runs = (await asyncio.to_thread(lambda: supabase.table("runs").select("user_id").execute())).data or []
    counts: dict[str, int] = {}
    for r in runs:
        counts[r["user_id"]] = counts.get(r["user_id"], 0) + 1

    return [
        {
            "user_id": p["user_id"],
            "email": p["email"],
            "role": p["role"],
            "created_at": p["created_at"],
            "run_count": counts.get(p["user_id"], 0),
        }
        for p in profiles
    ]


@router.get("/admin/runs")
async def list_all_runs(
    _: dict = Depends(require_admin),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[dict]:
    """Visão geral somente leitura de todas as runs do sistema, paginada."""
    supabase = _sb()
    runs = (
        await asyncio.to_thread(
            lambda: supabase.table("runs")
            .select("id, user_id, objective, status, total_tokens, cost_usd, created_at")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
    ).data or []

    user_ids = list({r["user_id"] for r in runs if r.get("user_id")})
    emails: dict[str, str] = {}
    if user_ids:
        profiles = (
            await asyncio.to_thread(
                lambda: supabase.table("profiles")
                .select("user_id, email")
                .in_("user_id", user_ids)
                .execute()
            )
        ).data or []
        emails = {p["user_id"]: p["email"] for p in profiles}

    return [{**r, "user_email": emails.get(r["user_id"], "")} for r in runs]
