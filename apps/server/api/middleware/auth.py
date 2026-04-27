import json
import urllib.request

import jwt
from jwt.algorithms import ECAlgorithm
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config import settings

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
        public_key = _load_public_key()
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
