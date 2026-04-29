import asyncio
import pytest
from unittest.mock import patch, MagicMock


def _make_app_with_mcp():
    """Creates the FastAPI app with MCP mounted (patches settings.mcp_api_key)."""
    with patch("core.config.settings") as mock_settings:
        mock_settings.mcp_api_key = "test-key"
        mock_settings.supabase_url = "http://test"
        mock_settings.supabase_service_key = "key"
        mock_settings.memory_similarity_threshold = 0.7
        mock_settings.gemini_api_key = ""
        mock_settings.langsmith_api_key = ""
        mock_settings.langsmith_project = "aether-os"
        mock_settings.frontend_url = "http://localhost:3000"
        mock_settings.max_requests_per_minute = 20
        mock_settings.log_level = "INFO"
        mock_settings.default_budget_limit = 10000
        mock_settings.tavily_api_key = ""
        mock_settings.e2b_api_key = ""

        from api.main import create_app
        app = create_app()
    return app


def test_mcp_module_importa_sem_erro():
    """Verifies that api/routes/mcp.py can be imported without errors."""
    import api.routes.mcp  # noqa: F401


def test_mcp_tools_declarados():
    """Verifies that the 3 MCP tools are declared."""
    from api.routes.mcp import mcp
    tools = asyncio.run(mcp.list_tools())
    tool_names = [tool.name for tool in tools]
    assert "web_search" in tool_names
    assert "time_manager" in tool_names
    assert "memory_recall" in tool_names


def test_mcp_get_asgi_app_retorna_app():
    """Verifies that get_mcp_asgi_app() returns a callable ASGI app."""
    from api.routes.mcp import get_mcp_asgi_app
    asgi_app = get_mcp_asgi_app()
    assert asgi_app is not None
    assert callable(asgi_app)
