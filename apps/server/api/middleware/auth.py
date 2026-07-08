import asyncio
import json
import urllib.request

import jwt
import structlog
from jwt.algorithms import ECAlgorithm
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config import settings
from core.supabase_client import get_service_client

logger = structlog.get_logger()

bearer_scheme = HTTPBearer(auto_error=False)

_public_key = None


def _load_public_key():
    global _public_key
    if _public_key is not None:
        return _public_key

    jwks_url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
    with urllib.request.urlopen(jwks_url) as resp:
        jwks = json.load(resp)

    key_data = jwks["keys"][0]
    _public_key = ECAlgorithm.from_jwk(json.dumps(key_data))
    return _public_key


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        public_key = await asyncio.to_thread(_load_public_key)
        payload = jwt.decode(
            credentials.credentials,
            public_key,
            algorithms=["ES256"],
            audience="authenticated",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Garante que o usuário autenticado tem role='admin' em profiles."""
    try:
        supabase = get_service_client()
        result = await asyncio.to_thread(
            lambda: supabase.table("profiles").select("role").eq("user_id", user["sub"]).execute()
        )
    except Exception:
        logger.exception("require_admin_lookup_failed", user_id=user["sub"])
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")

    if not result.data or result.data[0]["role"] != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return user
