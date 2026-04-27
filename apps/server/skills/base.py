from abc import ABC, abstractmethod

from pydantic import BaseModel


class SkillResult(BaseModel):
    success: bool
    output: str
    metadata: dict = {}
    error: str | None = None


class SkillMetadata(BaseModel):
    name: str
    description: str
    parameters_schema: dict
    requires_approval: bool


class Skill(ABC):
    name: str
    description: str
    parameters: type[BaseModel]
    requires_approval: bool = False

    @abstractmethod
    async def execute(self, params: BaseModel) -> SkillResult: ...

    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name=self.name,
            description=self.description,
            parameters_schema=self.parameters.model_json_schema(),
            requires_approval=self.requires_approval,
        )
