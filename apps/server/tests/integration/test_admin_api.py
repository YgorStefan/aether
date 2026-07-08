import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from api.main import app
from api.middleware.auth import get_current_user


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = lambda: {"sub": "user-123", "email": "user@test.com"}
    c = TestClient(app)
    yield c
    app.dependency_overrides = {}


def test_get_me_retorna_role_do_profile(client):
    with patch("api.routes.admin.get_service_client") as mock_supabase:
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"email": "user@test.com", "role": "user"}]
        )
        mock_supabase.return_value.table.return_value = mock_table

        response = client.get("/api/v1/me")

    assert response.status_code == 200
    assert response.json() == {"email": "user@test.com", "role": "user"}


def test_get_me_sem_profile_usa_fallback(client):
    with patch("api.routes.admin.get_service_client") as mock_supabase:
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_supabase.return_value.table.return_value = mock_table

        response = client.get("/api/v1/me")

    assert response.status_code == 200
    assert response.json()["role"] == "user"


def test_admin_users_retorna_403_sem_role_admin(client):
    with patch("api.middleware.auth.get_service_client") as mock_supabase:
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"role": "user"}]
        )
        mock_supabase.return_value.table.return_value = mock_table

        response = client.get("/api/v1/admin/users")

    assert response.status_code == 403


def test_admin_users_retorna_200_com_role_admin(client):
    with patch("api.middleware.auth.get_service_client") as mock_auth_supabase, \
         patch("api.routes.admin.get_service_client") as mock_admin_supabase:
        mock_auth_table = MagicMock()
        mock_auth_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"role": "admin"}]
        )
        mock_auth_supabase.return_value.table.return_value = mock_auth_table

        mock_profiles_table = MagicMock()
        mock_profiles_table.select.return_value.order.return_value.execute.return_value = MagicMock(
            data=[{"user_id": "u1", "email": "a@test.com", "role": "admin", "created_at": "2026-01-01"}]
        )
        mock_runs_table = MagicMock()
        mock_runs_table.select.return_value.execute.return_value = MagicMock(
            data=[{"user_id": "u1"}, {"user_id": "u1"}]
        )

        def _table(name):
            return {"profiles": mock_profiles_table, "runs": mock_runs_table}[name]

        mock_admin_supabase.return_value.table.side_effect = _table

        response = client.get("/api/v1/admin/users")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["run_count"] == 2


def test_admin_users_exige_autenticacao():
    app.dependency_overrides = {}
    c = TestClient(app)
    assert c.get("/api/v1/admin/users").status_code == 401


def test_require_admin_com_falha_no_lookup_retorna_403():
    async def _user():
        return {"sub": "user-123"}

    app.dependency_overrides[get_current_user] = _user
    c = TestClient(app)
    with patch("api.middleware.auth.get_service_client", side_effect=RuntimeError("db offline")):
        response = c.get("/api/v1/admin/users")
    app.dependency_overrides = {}
    assert response.status_code == 403
