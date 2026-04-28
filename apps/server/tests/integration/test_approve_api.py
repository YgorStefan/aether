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


def test_approve_resolve_hitl(client):
    with (
        patch("api.routes.runs.create_client") as mock_supabase,
        patch("api.routes.runs.hitl_store") as mock_hitl,
        patch("api.routes.runs.asyncio") as mock_asyncio,
    ):
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "run-abc"}]
        )
        mock_supabase.return_value.table.return_value = mock_table
        mock_asyncio.create_task = lambda coro: coro.close() or MagicMock()

        response = client.post(
            "/api/v1/runs/run-abc/approve",
            json={"decision": "approve"},
        )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    mock_hitl.resolve.assert_called_once_with("run-abc", "approve")


def test_approve_retorna_404_para_run_nao_pertencente(client):
    with patch("api.routes.runs.create_client") as mock_supabase:
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )
        mock_supabase.return_value.table.return_value = mock_table

        response = client.post(
            "/api/v1/runs/run-inexistente/approve",
            json={"decision": "approve"},
        )

    assert response.status_code == 404


def test_approve_rejeita_decision_invalida(client):
    response = client.post(
        "/api/v1/runs/run-abc/approve",
        json={"decision": "talvez"},
    )
    assert response.status_code == 422


def test_approve_exige_autenticacao():
    app.dependency_overrides = {}
    c = TestClient(app)
    response = c.post("/api/v1/runs/run-abc/approve", json={"decision": "approve"})
    assert response.status_code == 401
