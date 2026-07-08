import asyncio
from typing import Literal

from pydantic import BaseModel
from e2b_code_interpreter import Sandbox

from core.config import settings
from skills.base import Skill, SkillResult


def _run_in_sandbox(code: str) -> tuple[str, str]:
    with Sandbox(api_key=settings.e2b_api_key) as sandbox:
        execution = sandbox.run_code(code)
        stdout = "\n".join(execution.logs.stdout)
        stderr = "\n".join(execution.logs.stderr)
    return stdout, stderr


class CodeInterpreterParams(BaseModel):
    code: str
    language: Literal["python"] = "python"


class CodeInterpreter(Skill):
    name = "code_interpreter"
    description = (
        "Executa código Python em sandbox seguro e isolado (E2B). "
        "Ideal para cálculos, análise de dados e automação. Requer aprovação humana."
    )
    parameters = CodeInterpreterParams
    requires_approval = True

    async def execute(self, params: BaseModel) -> SkillResult:
        assert isinstance(params, CodeInterpreterParams)

        stdout, stderr = await asyncio.to_thread(_run_in_sandbox, params.code)

        if stderr:
            return SkillResult(success=False, output=stdout, error=stderr)
        return SkillResult(success=True, output=stdout or "(sem output)")
