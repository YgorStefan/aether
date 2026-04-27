from typing import Literal

from pydantic import BaseModel
from e2b_code_interpreter import Sandbox

from core.config import settings
from skills.base import Skill, SkillResult


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

        with Sandbox(api_key=settings.e2b_api_key) as sandbox:
            execution = sandbox.run_code(params.code)
            stdout = "\n".join(execution.logs.stdout)
            stderr = "\n".join(execution.logs.stderr)

        if stderr:
            return SkillResult(success=False, output=stdout, error=stderr)
        return SkillResult(success=True, output=stdout or "(sem output)")
