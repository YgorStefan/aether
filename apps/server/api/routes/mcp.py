"""
MCP Server — expõe skills sem estado como ferramentas Model Context Protocol.

Skills expostas: web_search, time_manager, memory_recall

Autenticação: toda requisição a /mcp deve incluir o header X-MCP-Api-Key com o
valor configurado em MCP_API_KEY. Ver get_mcp_asgi_app() para o wrapper que valida.

Uso com Claude Desktop (exemplo em claude_desktop_config.json):
{
  "mcpServers": {
    "aether-os": {
      "url": "http://localhost:8000/mcp",
      "headers": { "X-MCP-Api-Key": "sua-chave" }
    }
  }
}
"""

from fastmcp import FastMCP
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from core.config import settings

mcp = FastMCP("aether-os")


@mcp.tool()
async def web_search(query: str, max_results: int = 5) -> str:
    """Busca informações atuais na internet via Tavily."""
    from api.deps import registry
    from skills.web_search import WebSearchParams

    skill = registry.get("web_search")
    result = await skill.execute(WebSearchParams(query=query, max_results=max_results))
    return result.output if result.success else f"Erro: {result.error}"


@mcp.tool()
async def time_manager(query: str) -> str:
    """Responde perguntas sobre data, hora e fusos horários."""
    from api.deps import registry
    from skills.time_manager import TimeManagerParams

    skill = registry.get("time_manager")
    result = await skill.execute(TimeManagerParams(query=query))
    return result.output if result.success else f"Erro: {result.error}"


@mcp.tool()
async def memory_recall(query: str, top_k: int = 5, user_id: str = "") -> str:
    """Busca memórias de runs anteriores relevantes ao tema informado.

    Requer user_id (UUID do usuário Supabase) para filtrar por usuário.
    """
    if not user_id:
        return "Erro: user_id é obrigatório para buscar memórias."

    from core.llm_adapter import GeminiAdapter
    from core.memory import MemoryRepository
    from skills.memory_recall import MemoryRecall, MemoryRecallParams

    memory_repo = MemoryRepository(threshold=settings.memory_similarity_threshold)
    adapter = GeminiAdapter(api_key=settings.gemini_api_key) if settings.gemini_api_key else None
    skill = MemoryRecall(memory_repo=memory_repo, user_id=user_id, adapter=adapter)
    result = await skill.execute(MemoryRecallParams(query=query, top_k=top_k))
    return result.output if result.success else f"Erro: {result.error}"


class _McpAuthMiddleware:
    """Valida o header X-MCP-Api-Key antes de encaminhar para o app MCP."""

    def __init__(self, app: ASGIApp, api_key: str) -> None:
        self.app = app
        self.api_key = api_key

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        provided = headers.get(b"x-mcp-api-key", b"").decode()
        if provided != self.api_key:
            response = JSONResponse({"detail": "Não autorizado"}, status_code=401)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


def get_mcp_asgi_app():
    return _McpAuthMiddleware(mcp.http_app(), api_key=settings.mcp_api_key)
