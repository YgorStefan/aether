import time
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from api.middleware.auth import get_current_user
import api.middleware.auth as auth_module

test_app = FastAPI()


@test_app.get("/protected")
async def protected_route(user=Depends(get_current_user)):
    return {"user_id": user["sub"]}


_test_private_key = ec.generate_private_key(ec.SECP256R1())
_test_public_key = _test_private_key.public_key()


@pytest.fixture(autouse=True)
def mock_jwks(monkeypatch):
    monkeypatch.setattr(auth_module, "_load_public_key", lambda: _test_public_key)
    monkeypatch.setattr(auth_module, "_public_key", None)


@pytest.fixture
def auth_client() -> TestClient:
    return TestClient(test_app)


def make_token(sub: str = "user-123", exp_offset: int = 3600) -> str:
    payload = {
        "sub": sub,
        "aud": "authenticated",
        "exp": int(time.time()) + exp_offset,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, _test_private_key, algorithm="ES256")


def test_missing_token_returns_401(auth_client):
    response = auth_client.get("/protected")
    assert response.status_code == 401


def test_invalid_token_returns_401(auth_client):
    response = auth_client.get("/protected", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401


def test_expired_token_returns_401(auth_client):
    token = make_token(exp_offset=-10)
    response = auth_client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_valid_token_returns_200(auth_client):
    token = make_token(sub="user-abc")
    response = auth_client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["user_id"] == "user-abc"
