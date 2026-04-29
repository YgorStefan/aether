"""
MCP Server — expõe skills sem estado como ferramentas Model Context Protocol.

Skills expostas: web_search, time_manager, memory_recall

Nota: autenticação não está implementada nesta fase.
Exponha o endpoint apenas em redes internas ou atrás de um reverse-proxy com auth.

Uso com Claude Desktop (exemplo em claude_desktop_config.json):
{
  "mcpServers": {
    "aether-os": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
"""

from fastmcp import FastMCP

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

    memory_repo = MemoryRepository(
        url=settings.supabase_url,
        service_key=settings.supabase_service_key,
        threshold=settings.memory_similarity_threshold,
    )
    adapter = GeminiAdapter(api_key=settings.gemini_api_key) if settings.gemini_api_key else None
    skill = MemoryRecall(memory_repo=memory_repo, user_id=user_id, adapter=adapter)
    result = await skill.execute(MemoryRecallParams(query=query, top_k=top_k))
    return result.output if result.success else f"Erro: {result.error}"


def get_mcp_asgi_app():
    return mcp.http_app()
