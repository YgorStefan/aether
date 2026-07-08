import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from api.main import app
from api.middleware.auth import get_current_user


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = lambda: {"sub": "user-123"}
    c = TestClient(app)
    yield c
    app.dependency_overrides = {}


def test_delete_account_chama_admin_delete_user(client):
    with patch("api.routes.account.get_service_client") as mock_supabase:
        mock_admin = MagicMock()
        mock_supabase.return_value.auth.admin = mock_admin

        response = client.delete("/api/v1/account")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    mock_admin.delete_user.assert_called_once_with("user-123")


def test_delete_account_com_falha_retorna_500(client):
    with patch("api.routes.account.get_service_client") as mock_supabase:
        mock_admin = MagicMock()
        mock_admin.delete_user.side_effect = RuntimeError("boom")
        mock_supabase.return_value.auth.admin = mock_admin

        response = client.delete("/api/v1/account")

    assert response.status_code == 500


def test_delete_account_exige_autenticacao():
    app.dependency_overrides = {}
    c = TestClient(app)
    assert c.delete("/api/v1/account").status_code == 401
