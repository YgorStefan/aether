from typing import Literal

from pydantic import BaseModel
from supabase import create_client

from skills.base import Skill, SkillResult


class FileWriterParams(BaseModel):
    filename: str
    content: str
    format: Literal["md", "txt"] = "md"


class FileWriter(Skill):
    name = "file_writer"
    description = (
        "Salva um arquivo de texto no Supabase Storage e retorna a URL pública. "
        "Use para gerar relatórios, documentos e outputs persistentes. Requer aprovação humana."
    )
    parameters = FileWriterParams
    requires_approval = True

    async def execute(self, params: BaseModel) -> SkillResult:
        assert isinstance(params, FileWriterParams)
        try:
            from core.config import settings

            supabase = create_client(settings.supabase_url, settings.supabase_service_key)
            path = f"{params.filename}.{params.format}"
            data = params.content.encode("utf-8")
            supabase.storage.from_("artifacts").upload(
                path, data, {"content-type": "text/plain; charset=utf-8"}
            )
            url = supabase.storage.from_("artifacts").get_public_url(path)
            return SkillResult(
                success=True,
                output=f"Arquivo salvo em: {url}",
                metadata={"url": url, "path": path},
            )
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))
