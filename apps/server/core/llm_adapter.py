from abc import ABC, abstractmethod

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


class GeminiAdapter(BaseLLMAdapter):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        from langchain_google_genai import ChatGoogleGenerativeAI

        self._llm = ChatGoogleGenerativeAI(model=model, google_api_key=api_key)

    async def generate(
        self,
        prompt: str,
        response_model: type[BaseModel],
        state: AgentState,
    ) -> tuple[BaseModel, int, int]:
        structured_llm = self._llm.with_structured_output(response_model)
        result = await structured_llm.ainvoke(prompt)
        input_tokens = max(len(prompt.split()) * 2, 10)
        output_tokens = 100
        return result, input_tokens, output_tokens
