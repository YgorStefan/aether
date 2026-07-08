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


def test_get_settings_sem_chave_configurada(client):
    with patch("api.routes.settings.get_service_client") as mock_supabase:
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_supabase.return_value.table.return_value = mock_table

        response = client.get("/api/v1/settings")

    assert response.status_code == 200
    assert response.json() == {"provider": None, "api_key_set": False, "api_key_masked": None}


def test_put_settings_criptografa_antes_de_salvar(client):
    with patch("api.routes.settings.get_service_client") as mock_supabase, \
         patch("api.routes.settings.encrypt", return_value="enc:xxxx") as mock_encrypt:
        mock_table = MagicMock()
        mock_table.upsert.return_value.execute.return_value = MagicMock()
        mock_supabase.return_value.table.return_value = mock_table

        response = client.put(
            "/api/v1/settings",
            json={"provider": "gemini", "api_key": "minha-chave-real"},
        )

    assert response.status_code == 200
    mock_encrypt.assert_called_once_with("minha-chave-real")
    saved_payload = mock_table.upsert.call_args[0][0]
    assert saved_payload["api_key"] == "enc:xxxx"


def test_get_settings_decripta_e_mascara_chave(client):
    with patch("api.routes.settings.get_service_client") as mock_supabase, \
         patch("api.routes.settings.decrypt", return_value="AIzaSy1234567890abcdef") as mock_decrypt:
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"provider": "gemini", "api_key": "enc:blob"}]
        )
        mock_supabase.return_value.table.return_value = mock_table

        response = client.get("/api/v1/settings")

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "gemini"
    assert body["api_key_set"] is True
    assert body["api_key_masked"] == "AIzaSy12...cdef"
    mock_decrypt.assert_called_once_with("enc:blob")


def test_get_settings_com_falha_de_decriptacao_retorna_nao_configurado(client):
    with patch("api.routes.settings.get_service_client") as mock_supabase, \
         patch("api.routes.settings.decrypt", side_effect=ValueError("chave inválida")):
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"provider": "gemini", "api_key": "enc:blob"}]
        )
        mock_supabase.return_value.table.return_value = mock_table

        response = client.get("/api/v1/settings")

    assert response.status_code == 200
    assert response.json()["api_key_set"] is False


def test_put_settings_rejeita_api_key_vazia(client):
    response = client.put("/api/v1/settings", json={"provider": "gemini", "api_key": "   "})
    assert response.status_code == 400


def test_put_settings_rejeita_provider_nao_suportado(client):
    response = client.put("/api/v1/settings", json={"provider": "openai", "api_key": "x"})
    assert response.status_code == 422


def test_settings_exige_autenticacao():
    app.dependency_overrides = {}
    c = TestClient(app)
    assert c.get("/api/v1/settings").status_code == 401
    assert c.put("/api/v1/settings", json={"provider": "gemini", "api_key": "x"}).status_code == 401
