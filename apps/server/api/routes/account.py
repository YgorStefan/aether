import asyncio

import structlog
from fastapi import APIRouter, Depends, HTTPException

from api.middleware.auth import get_current_user
from core.supabase_client import get_service_client

logger = structlog.get_logger()

router = APIRouter(tags=["account"])


@router.delete("/account", status_code=200)
async def delete_account(user: dict = Depends(get_current_user)) -> dict:
    """Exclui a conta do usuário. Cascata (ON DELETE CASCADE) remove runs, run_events,
    memories, user_settings e profiles automaticamente."""
    supabase = get_service_client()
    try:
        await asyncio.to_thread(supabase.auth.admin.delete_user, user["sub"])
    except Exception as exc:
        logger.exception("account_delete_failed", user_id=user["sub"])
        raise HTTPException(status_code=500, detail="Erro ao excluir conta") from exc

    return {"ok": True}
