import functools

from langgraph.graph import END, START, StateGraph

from agents.nodes import budget_gate_node, evaluate_result_node, finalize_node
from agents.state import AgentState
from agents.supervisor import supervisor_node
from agents.worker import worker_node
from core.budget import BudgetController
from core.events import RunEventEmitter
from core.hitl_store import HitlStore
from core.llm_adapter import BaseLLMAdapter
from skills.registry import SkillRegistry


def build_graph(
    *,
    adapter: BaseLLMAdapter,
    budget: BudgetController,
    emitter: RunEventEmitter,
    registry: SkillRegistry,
    hitl_store: HitlStore,
    langsmith_enabled: bool = False,
):
    supervisor_fn = functools.partial(
        supervisor_node, adapter=adapter, emitter=emitter, langsmith_enabled=langsmith_enabled
    )
    budget_fn = functools.partial(budget_gate_node, budget=budget, emitter=emitter)
    worker_fn = functools.partial(
        worker_node, adapter=adapter, emitter=emitter,
        registry=registry, hitl_store=hitl_store
    )
    evaluate_fn = functools.partial(evaluate_result_node, emitter=emitter, budget=budget)
    finalize_fn = functools.partial(finalize_node, emitter=emitter, budget=budget)

    workflow = StateGraph(AgentState)
    workflow.add_node("supervisor", supervisor_fn)
    workflow.add_node("budget_gate", budget_fn)
    workflow.add_node("worker", worker_fn)
    workflow.add_node("evaluate", evaluate_fn)
    workflow.add_node("finalize", finalize_fn)

    workflow.add_edge(START, "supervisor")

    def _after_supervisor(state: AgentState) -> str:
        return "finalize" if state["status"] == "failed" else "budget_gate"

    def _after_budget_gate(state: AgentState) -> str:
        return "finalize" if state["status"] == "failed" else "worker"

    def _after_evaluate(state: AgentState) -> str:
        if state["status"] == "failed":
            return "finalize"
        if state["current_task_index"] >= len(state["tasks"]):
            return "finalize"
        return "budget_gate"

    workflow.add_conditional_edges(
        "supervisor", _after_supervisor, {"budget_gate": "budget_gate", "finalize": "finalize"}
    )
    workflow.add_conditional_edges(
        "budget_gate", _after_budget_gate, {"worker": "worker", "finalize": "finalize"}
    )
    workflow.add_edge("worker", "evaluate")
    workflow.add_conditional_edges(
        "evaluate", _after_evaluate, {"budget_gate": "budget_gate", "finalize": "finalize"}
    )
    workflow.add_edge("finalize", END)

    return workflow.compile()
