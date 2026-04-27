import pendulum
from pydantic import BaseModel

from skills.base import Skill, SkillResult


class TimeManagerParams(BaseModel):
    query: str


class TimeManager(Skill):
    name = "time_manager"
    description = (
        "Responde perguntas sobre tempo: data e hora atual, fuso horário, "
        "cálculo de duração entre datas."
    )
    parameters = TimeManagerParams
    requires_approval = False

    async def execute(self, params: BaseModel) -> SkillResult:
        assert isinstance(params, TimeManagerParams)
        now = pendulum.now("UTC")
        return SkillResult(
            success=True,
            output=f"Agora é {now.to_rfc2822_string()} (UTC). Consulta: {params.query}",
            metadata={"timestamp_utc": now.isoformat()},
        )
