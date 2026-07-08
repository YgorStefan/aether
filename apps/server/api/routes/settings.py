import asyncio
from typing import Literal

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.middleware.auth import get_current_user
from core.crypto import decrypt, encrypt
from core.supabase_client import get_service_client

logger = structlog.get_logger()

router = APIRouter(tags=["settings"])

SUPPORTED_PROVIDERS = {"gemini"}


class SettingsRequest(BaseModel):
    provider: Literal["gemini"]
    api_key: str


@router.get("/settings")
async def get_settings(user: dict = Depends(get_current_user)) -> dict:
    supabase = get_service_client()
    result = await asyncio.to_thread(
        lambda: supabase.table("user_settings")
        .select("provider, api_key")
        .eq("user_id", user["sub"])
        .execute()
    )
    if not result.data:
        return {"provider": None, "api_key_set": False, "api_key_masked": None}

    row = result.data[0]
    try:
        key = decrypt(row["api_key"])
    except ValueError:
        logger.exception("settings_decrypt_failed", user_id=user["sub"])
        return {"provider": row["provider"], "api_key_set": False, "api_key_masked": None}
    masked = key[:8] + "..." + key[-4:] if len(key) > 12 else "****"
    return {"provider": row["provider"], "api_key_set": True, "api_key_masked": masked}


@router.put("/settings", status_code=200)
async def update_settings(
    body: SettingsRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    if not body.api_key.strip():
        raise HTTPException(status_code=400, detail="API key não pode ser vazia")

    supabase = get_service_client()
    try:
        await asyncio.to_thread(
            lambda: supabase.table("user_settings")
            .upsert(
                {
                    "user_id": user["sub"],
                    "provider": body.provider,
                    "api_key": encrypt(body.api_key.strip()),
                },
                on_conflict="user_id",
            )
            .execute()
        )
    except Exception:
        logger.exception("settings_update_failed", user_id=user["sub"])
        raise HTTPException(status_code=500, detail="Erro ao salvar configurações")

    return {"ok": True}
