import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from api.main import app
from api.middleware.auth import get_current_user


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = lambda: {"sub": "user-123"}
    yield TestClient(app)
    app.dependency_overrides = {}


def test_get_events_retorna_lista(client):
    mock_run_data = [{"id": "run-abc", "user_id": "user-123"}]
    mock_events_data = [
        {"id": "ev-1", "run_id": "run-abc", "type": "agent_started",
         "agent_name": "supervisor", "payload": {}, "tokens_used": 0}
    ]

    with patch("api.routes.runs.create_client") as mock_supabase:
        mock_table = MagicMock()
        # Primeira chamada: verificar ownership do run
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value \
            = MagicMock(data=mock_run_data)
        # Segunda chamada: buscar eventos
        mock_table.select.return_value.eq.return_value.order.return_value.execute.return_value \
            = MagicMock(data=mock_events_data)
        mock_supabase.return_value.table.return_value = mock_table

        response = client.get("/api/v1/runs/run-abc/events")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_events_retorna_404_se_run_nao_pertence_ao_usuario(client):
    with patch("api.routes.runs.create_client") as mock_supabase:
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value \
            = MagicMock(data=[])
        mock_supabase.return_value.table.return_value = mock_table

        response = client.get("/api/v1/runs/nao-existe/events")

    assert response.status_code == 404
