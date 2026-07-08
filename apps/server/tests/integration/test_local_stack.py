"""Testes de integração contra um Supabase LOCAL real (via `supabase start`, ver README).

Diferente dos demais testes de integração (que mockam o cliente Supabase), estes
exercitam profiles/trigger/RLS, promoção a admin e criptografia de settings contra
um Postgres real. São pulados automaticamente se a stack local não estiver no ar.
"""

import uuid

import httpx
import pytest
from fastapi.testclient import TestClient
from supabase import create_client

from api.main import app
from api.middleware.auth import get_current_user
from core.config import settings


def _local_supabase_disponivel() -> bool:
    if not settings.supabase_url or not settings.supabase_service_key:
        return False
    try:
        resp = httpx.get(f"{settings.supabase_url}/auth/v1/health", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _local_supabase_disponivel(),
    reason="Supabase local não está rodando (supabase start)",
)


@pytest.fixture
def real_user():
    admin_client = create_client(settings.supabase_url, settings.supabase_service_key)
    email = f"teste-{uuid.uuid4().hex[:8]}@aether.local"
    created = admin_client.auth.admin.create_user({
        "email": email,
        "password": "senha-super-secreta-123",
        "email_confirm": True,
    })
    user_id = created.user.id
    yield user_id
    try:
        admin_client.auth.admin.delete_user(user_id)
    except Exception:
        pass  # já removido pelo próprio teste (ex: teste de exclusão de conta)


@pytest.fixture
def client():
    yield TestClient(app)
    app.dependency_overrides = {}


def test_trigger_cria_profile_com_role_user(real_user):
    admin_client = create_client(settings.supabase_url, settings.supabase_service_key)
    result = admin_client.table("profiles").select("role").eq("user_id", real_user).execute()
    assert len(result.data) == 1
    assert result.data[0]["role"] == "user"


def test_promover_a_admin_libera_endpoints_de_admin(real_user, client):
    admin_client = create_client(settings.supabase_url, settings.supabase_service_key)

    app.dependency_overrides[get_current_user] = lambda: {"sub": real_user}
    assert client.get("/api/v1/admin/users").status_code == 403

    admin_client.table("profiles").update({"role": "admin"}).eq("user_id", real_user).execute()

    response = client.get("/api/v1/admin/users")
    assert response.status_code == 200
    emails = [u["email"] for u in response.json()]
    assert any(real_user == u["user_id"] for u in response.json())
    assert len(emails) >= 1


def test_settings_round_trip_criptografado_no_postgres_local(real_user, client):
    app.dependency_overrides[get_current_user] = lambda: {"sub": real_user}

    put_response = client.put(
        "/api/v1/settings",
        json={"provider": "gemini", "api_key": "AIzaSyRealChaveDeTeste123"},
    )
    assert put_response.status_code == 200

    admin_client = create_client(settings.supabase_url, settings.supabase_service_key)
    row = (
        admin_client.table("user_settings")
        .select("api_key")
        .eq("user_id", real_user)
        .execute()
        .data[0]
    )
    assert row["api_key"] != "AIzaSyRealChaveDeTeste123"
    assert row["api_key"].startswith("enc:")

    get_response = client.get("/api/v1/settings")
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["api_key_set"] is True
    assert body["api_key_masked"] == "AIzaSyRe...e123"


def test_delete_user_remove_profile_e_settings_em_cascata(real_user, client):
    app.dependency_overrides[get_current_user] = lambda: {"sub": real_user}
    client.put("/api/v1/settings", json={"provider": "gemini", "api_key": "chave-x"})

    admin_client = create_client(settings.supabase_url, settings.supabase_service_key)
    admin_client.auth.admin.delete_user(real_user)

    assert admin_client.table("profiles").select("*").eq("user_id", real_user).execute().data == []
    assert admin_client.table("user_settings").select("*").eq("user_id", real_user).execute().data == []
