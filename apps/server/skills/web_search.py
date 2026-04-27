from pydantic import BaseModel
from tavily import TavilyClient

from skills.base import Skill, SkillResult


class WebSearchParams(BaseModel):
    query: str
    max_results: int = 5


class WebSearch(Skill):
    name = "web_search"
    description = (
        "Busca informações atuais na internet. Use para fatos recentes, "
        "notícias, documentação e pesquisa sobre qualquer tema."
    )
    parameters = WebSearchParams
    requires_approval = False

    async def execute(self, params: BaseModel) -> SkillResult:
        assert isinstance(params, WebSearchParams)
        try:
            from core.config import settings

            client = TavilyClient(api_key=settings.tavily_api_key)
            response = client.search(params.query, max_results=params.max_results)
            results = response.get("results", [])
            output = "\n".join(
                f"- {r['title']}: {r['content']}" for r in results[: params.max_results]
            )
            return SkillResult(
                success=True,
                output=output or "Nenhum resultado encontrado.",
                metadata={"results_count": len(results)},
            )
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))
