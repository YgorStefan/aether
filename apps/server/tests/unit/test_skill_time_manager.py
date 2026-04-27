import pytest
from pydantic import BaseModel
from skills.time_manager import TimeManager, TimeManagerParams


@pytest.mark.asyncio
async def test_time_manager_retorna_data_atual():
    skill = TimeManager()
    result = await skill.execute(TimeManagerParams(query="Que horas são agora?"))
    assert result.success is True
    assert len(result.output) > 10
    assert "UTC" in result.output


@pytest.mark.asyncio
async def test_time_manager_inclui_query_na_resposta():
    skill = TimeManager()
    result = await skill.execute(TimeManagerParams(query="Quantos dias até sexta?"))
    assert "Quantos dias" in result.output


def test_time_manager_metadados():
    skill = TimeManager()
    meta = skill.metadata()
    assert meta.name == "time_manager"
    assert meta.requires_approval is False
    assert "query" in meta.parameters_schema["properties"]
