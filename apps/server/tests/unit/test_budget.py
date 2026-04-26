import pytest
from core.budget import BudgetController, BudgetExceededException

COST_PER_1K_INPUT = 0.00015
COST_PER_1K_OUTPUT = 0.0006


def test_budget_excedido_levanta_excecao():
    budget = BudgetController(limit_tokens=100)
    with pytest.raises(BudgetExceededException):
        budget.add_tokens(60, 50)  # 110 > 100


def test_budget_dentro_do_limite_nao_levanta():
    budget = BudgetController(limit_tokens=100)
    budget.add_tokens(40, 30)  # 70 <= 100 — não deve levantar


def test_budget_warning_acima_de_80_porcento():
    budget = BudgetController(limit_tokens=100)
    assert budget.is_warning(40, 45) is True   # 85 >= 80
    assert budget.is_warning(40, 40) is True   # 80 == 80% boundary
    assert budget.is_warning(40, 30) is False  # 70 < 80


def test_cost_usd_calculado_corretamente():
    budget = BudgetController(limit_tokens=10000)
    cost = budget.cost_usd(1000, 500)
    expected = (1000 / 1000 * COST_PER_1K_INPUT) + (500 / 1000 * COST_PER_1K_OUTPUT)
    assert abs(cost - expected) < 1e-9
