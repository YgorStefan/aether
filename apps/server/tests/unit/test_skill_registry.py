import pytest
from pydantic import BaseModel
from skills.base import Skill, SkillResult
from skills.registry import SkillRegistry


class _DummyParams(BaseModel):
    value: str


class _DummySkill(Skill):
    name = "dummy"
    description = "Skill de teste"
    parameters = _DummyParams
    requires_approval = False

    async def execute(self, params: BaseModel) -> SkillResult:
        return SkillResult(success=True, output=f"dummy:{params.value}")


def test_register_e_get():
    registry = SkillRegistry()
    registry.register(_DummySkill())
    skill = registry.get("dummy")
    assert skill.name == "dummy"


def test_get_skill_desconhecida_levanta_key_error():
    registry = SkillRegistry()
    with pytest.raises(KeyError, match="nao_existe"):
        registry.get("nao_existe")


def test_list_all_retorna_metadados():
    registry = SkillRegistry()
    registry.register(_DummySkill())
    metas = registry.list_all()
    assert len(metas) == 1
    assert metas[0].name == "dummy"
    assert metas[0].requires_approval is False
    assert "value" in metas[0].parameters_schema["properties"]


def test_skill_names():
    registry = SkillRegistry()
    registry.register(_DummySkill())
    assert "dummy" in registry.skill_names()


def test_autodiscover_encontra_skills(tmp_path):
    # Escreve um arquivo de skill no diretório temporário
    skill_file = tmp_path / "test_auto.py"
    skill_file.write_text(
        """
from pydantic import BaseModel
from skills.base import Skill, SkillResult

class _AutoParams(BaseModel):
    x: str

class AutoSkill(Skill):
    name = "auto_skill"
    description = "Auto skill"
    parameters = _AutoParams
    async def execute(self, params):
        return SkillResult(success=True, output="auto")
"""
    )
    registry = SkillRegistry.autodiscover(tmp_path)
    assert "auto_skill" in registry.skill_names()
