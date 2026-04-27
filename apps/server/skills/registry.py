import importlib
import importlib.util
import inspect
import sys
from pathlib import Path

from skills.base import Skill, SkillMetadata


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        self._skills[skill.name] = skill

    def get(self, name: str) -> Skill:
        skill = self._skills.get(name)
        if skill is None:
            raise KeyError(f"Skill '{name}' não encontrada")
        return skill

    def list_all(self) -> list[SkillMetadata]:
        return [skill.metadata() for skill in self._skills.values()]

    def skill_names(self) -> list[str]:
        return list(self._skills.keys())

    @classmethod
    def autodiscover(cls, skills_dir: Path) -> "SkillRegistry":
        registry = cls()
        for path in sorted(skills_dir.glob("*.py")):
            if path.name.startswith("_"):
                continue
            module_name = f"_autodiscover_{path.stem}"
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(obj, Skill)
                    and obj is not Skill
                    and hasattr(obj, "name")
                    and isinstance(obj.name, str)
                ):
                    registry.register(obj())
        return registry
