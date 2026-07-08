import types
from abc import ABC, abstractmethod
from enum import Enum
from typing import Literal, Union, get_args, get_origin

from pydantic import BaseModel

from agents.state import AgentState


class BaseLLMAdapter(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        response_model: type[BaseModel],
        state: AgentState,
    ) -> tuple[BaseModel, int, int]:
        """Retorna (resposta, input_tokens, output_tokens)."""
        ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Retorna embedding de 768 dimensões."""
        ...


class MockLLMAdapter(BaseLLMAdapter):
    def __init__(self) -> None:
        self._responses: dict[type, list[BaseModel]] = {}

    def enqueue(self, response_type: type, response: BaseModel) -> None:
        if response_type not in self._responses:
            self._responses[response_type] = []
        self._responses[response_type].append(response)

    async def generate(
        self,
        prompt: str,
        response_model: type[BaseModel],
        state: AgentState,
    ) -> tuple[BaseModel, int, int]:
        responses = self._responses.get(response_model, [])
        if not responses:
            raise ValueError(f"Nenhuma resposta mock enfileirada para {response_model.__name__}")
        return responses.pop(0), 100, 50

    async def embed(self, text: str) -> list[float]:
        return [0.1] * 768


class AutoMockLLMAdapter(BaseLLMAdapter):
    """Adapter determinístico para rodar o grafo de agentes completo (Supervisor→Worker→
    Evaluate→Finalize) sem uma chave Gemini real — usado em testes locais (E2E, carga,
    UAT) quando USE_MOCK_LLM=true. NUNCA deve ser habilitado em produção.

    Responde a qualquer `response_model` pedido pelos nós do grafo: reconhece os modelos
    conhecidos (TaskPlan, SkillSelection, ObserveResult, DecisionResult, FinalSynthesis)
    com respostas coerentes, e para os demais (ex: parâmetros de skills) preenche os
    campos obrigatórios genericamente. Por padrão seleciona a skill `default_skill_name`
    (`time_manager`: sem custo, sem aprovação, sempre bem-sucedida), exceto quando o
    objetivo contém a palavra "arquivo" — nesse caso seleciona `file_writer`, que exige
    aprovação humana (HITL), permitindo exercitar esse fluxo em testes E2E/manuais.
    """

    def __init__(self, default_skill_name: str = "time_manager") -> None:
        self._default_skill_name = default_skill_name

    async def generate(
        self,
        prompt: str,
        response_model: type[BaseModel],
        state: AgentState,
    ) -> tuple[BaseModel, int, int]:
        return self._build(response_model, state), 10, 5

    async def embed(self, text: str) -> list[float]:
        return [0.1] * 768

    def _build(self, model: type[BaseModel], state: AgentState) -> BaseModel:
        skill_name = self._default_skill_name
        if "arquivo" in state.get("objective", "").lower():
            skill_name = "file_writer"
        known: dict[str, dict] = {
            "TaskPlan": {"tasks": ["Tarefa de teste automática (modo mock)"]},
            "SkillSelection": {
                "skill_name": skill_name,
                "rationale": "Selecionado automaticamente (modo mock)",
            },
            "ObserveResult": {"observations": "Resultado observado com sucesso (modo mock)"},
            "DecisionResult": {"is_complete": True, "result": "Tarefa concluída com sucesso (modo mock)"},
            "FinalSynthesis": {"summary": "Objetivo concluído com sucesso (modo mock)"},
        }
        if model.__name__ in known:
            return model(**known[model.__name__])
        return self._generic_fill(model)

    def _generic_fill(self, model: type[BaseModel]) -> BaseModel:
        values = {
            name: self._dummy_value(field.annotation)
            for name, field in model.model_fields.items()
            if field.is_required()
        }
        return model(**values)

    def _dummy_value(self, annotation):
        origin = get_origin(annotation)
        if origin is Literal:
            return get_args(annotation)[0]
        if origin in (Union, types.UnionType):
            args = [a for a in get_args(annotation) if a is not type(None)]
            return self._dummy_value(args[0]) if args else None
        if origin in (list, tuple, set):
            return []
        if origin is dict:
            return {}
        if isinstance(annotation, type) and issubclass(annotation, Enum):
            return next(iter(annotation))
        if annotation is int:
            return 1
        if annotation is float:
            return 1.0
        if annotation is bool:
            return True
        return "mock"


class GeminiAdapter(BaseLLMAdapter):
    def __init__(self, api_key: str, model: str = "gemini-flash-lite-latest") -> None:
        from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

        self._api_key = api_key
        self._llm = ChatGoogleGenerativeAI(model=model, google_api_key=api_key)
        self._embedder = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=api_key,
        )

    async def generate(
        self,
        prompt: str,
        response_model: type[BaseModel],
        state: AgentState,
    ) -> tuple[BaseModel, int, int]:
        structured_llm = self._llm.with_structured_output(response_model, include_raw=True)
        raw_result = await structured_llm.ainvoke(prompt)
        parsed = raw_result["parsed"]
        raw_msg = raw_result["raw"]
        usage = getattr(raw_msg, "usage_metadata", None) or raw_msg.response_metadata.get("usage_metadata", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        return parsed, input_tokens, output_tokens

    async def embed(self, text: str) -> list[float]:
        return await self._embedder.aembed_query(text)
