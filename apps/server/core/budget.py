_COST_PER_1K_INPUT = 0.00015   # Gemini 1.5 Flash
_COST_PER_1K_OUTPUT = 0.0006


class BudgetExceededException(Exception):
    pass


class BudgetController:
    """Stateless token budget validator. Caller owns cumulative token counts in AgentState."""

    def __init__(self, limit_tokens: int) -> None:
        self.limit_tokens = limit_tokens

    def add_tokens(self, input_tokens: int, output_tokens: int) -> None:
        """Raise BudgetExceededException if caller-provided cumulative totals exceed the limit."""
        if input_tokens + output_tokens > self.limit_tokens:
            raise BudgetExceededException(
                f"Budget excedido: {input_tokens + output_tokens}/{self.limit_tokens} tokens"
            )

    def is_warning(self, input_tokens: int, output_tokens: int) -> bool:
        return (input_tokens + output_tokens) >= self.limit_tokens * 0.8

    def cost_usd(self, input_tokens: int, output_tokens: int) -> float:
        return (
            input_tokens / 1000 * _COST_PER_1K_INPUT
            + output_tokens / 1000 * _COST_PER_1K_OUTPUT
        )
