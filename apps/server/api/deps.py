from pathlib import Path

from skills.registry import SkillRegistry

_skills_dir = Path(__file__).parent.parent / "skills"
registry = SkillRegistry.autodiscover(_skills_dir)
