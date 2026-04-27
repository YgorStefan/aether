from fastapi import APIRouter, Depends

from api.deps import registry
from api.middleware.auth import get_current_user

router = APIRouter(tags=["skills"])


@router.get("/skills")
async def list_skills(
    user: dict = Depends(get_current_user),
) -> list[dict]:
    return [m.model_dump() for m in registry.list_all()]
