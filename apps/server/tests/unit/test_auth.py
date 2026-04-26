import time
import jwt
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from api.middleware.auth import get_current_user

test_app = FastAPI()


@test_app.get("/protected")
async def protected_route(user=Depends(get_current_user)):
    return {"user_id": user["sub"]}


@pytest.fixture
def auth_client() -> TestClient:
    return TestClient(test_app)


def make_token(secret: str, sub: str = "user-123", exp_offset: int = 3600) -> str:
    payload = {
        "sub": sub,
        "aud": "authenticated",
        "exp": int(time.time()) + exp_offset,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def test_missing_token_returns_401(auth_client):
    response = auth_client.get("/protected")
    assert response.status_code == 401


def test_invalid_token_returns_401(auth_client):
    response = auth_client.get("/protected", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401


def test_expired_token_returns_401(auth_client):
    token = make_token(secret="test-secret", exp_offset=-10)
    response = auth_client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_valid_token_returns_200(auth_client, monkeypatch):
    secret = "test-secret"
    monkeypatch.setattr("api.middleware.auth.settings.supabase_jwt_secret", secret)
    token = make_token(secret=secret, sub="user-abc")
    response = auth_client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["user_id"] == "user-abc"
