import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from api.routes.mcp import _McpAuthMiddleware


async def _ok(request):
    return PlainTextResponse("ok")


def _make_client(api_key: str) -> TestClient:
    inner = Starlette(routes=[Route("/", _ok)])
    app = _McpAuthMiddleware(inner, api_key=api_key)
    return TestClient(app)


def test_sem_header_retorna_401():
    client = _make_client("segredo")
    response = client.get("/")
    assert response.status_code == 401


def test_header_incorreto_retorna_401():
    client = _make_client("segredo")
    response = client.get("/", headers={"X-MCP-Api-Key": "errado"})
    assert response.status_code == 401


def test_header_correto_permite_acesso():
    client = _make_client("segredo")
    response = client.get("/", headers={"X-MCP-Api-Key": "segredo"})
    assert response.status_code == 200
    assert response.text == "ok"
