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


class GeminiAdapter(BaseLLMAdapter):
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
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
