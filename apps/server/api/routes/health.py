import httpx
from fastapi import APIRouter
from core.config import settings

router = APIRouter(tags=["system"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/ready")
async def ready():
    supabase_ok = False
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get(f"{settings.supabase_url}/rest/v1/")
            supabase_ok = resp.status_code in (200, 404)
    except Exception:
        pass

    langsmith_ok = bool(settings.langsmith_api_key)

    status = "ok" if supabase_ok else "degraded"
    return {"status": status, "supabase": supabase_ok, "langsmith": langsmith_ok}
