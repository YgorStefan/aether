import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.middleware.auth import get_current_user


@pytest.fixture
def client_autenticado():
    app.dependency_overrides[get_current_user] = lambda: {"sub": "user-123"}
    client = TestClient(app)
    yield client
    app.dependency_overrides = {}


def test_get_skills_retorna_lista(client_autenticado):
    response = client_autenticado.get("/api/v1/skills")
    assert response.status_code == 200
    skills = response.json()
    assert isinstance(skills, list)
    assert len(skills) >= 4  # time_manager, web_search, code_interpreter, file_writer

    names = [s["name"] for s in skills]
    assert "time_manager" in names
    assert "web_search" in names
    assert "code_interpreter" in names
    assert "file_writer" in names


def test_get_skills_estrutura_correta(client_autenticado):
    response = client_autenticado.get("/api/v1/skills")
    skills = response.json()
    for skill in skills:
        assert "name" in skill
        assert "description" in skill
        assert "parameters_schema" in skill
        assert "requires_approval" in skill


def test_get_skills_exige_autenticacao():
    client = TestClient(app)
    response = client.get("/api/v1/skills")
    assert response.status_code == 401


def test_skills_requires_approval_correto(client_autenticado):
    response = client_autenticado.get("/api/v1/skills")
    skills = {s["name"]: s for s in response.json()}
    assert skills["time_manager"]["requires_approval"] is False
    assert skills["web_search"]["requires_approval"] is False
    assert skills["code_interpreter"]["requires_approval"] is True
    assert skills["file_writer"]["requires_approval"] is True
