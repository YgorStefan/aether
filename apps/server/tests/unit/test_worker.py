import pytest
from pydantic import BaseModel
from agents.state import AgentState, Task
from agents.worker import DecisionResult, ObserveResult, SkillSelection, worker_node
from core.events import EventType, RunEventEmitter
from core.llm_adapter import MockLLMAdapter
from skills.base import Skill, SkillResult
from skills.registry import SkillRegistry


class _MockParams(BaseModel):
    value: str


class _MockSkill(Skill):
    name = "mock_skill"
    description = "Skill de teste"
    parameters = _MockParams
    requires_approval = False

    async def execute(self, params: BaseModel) -> SkillResult:
        return SkillResult(success=True, output=f"executado:{params.value}")


class _ApprovalSkill(Skill):
    name = "approval_skill"
    description = "Skill que requer aprovação"
    parameters = _MockParams
    requires_approval = True

    async def execute(self, params: BaseModel) -> SkillResult:
        return SkillResult(success=True, output="aprovado")


class _MockHitlStore:
    def __init__(self, decision: str = "approve") -> None:
        self._decision = decision

    async def wait_for_decision(self, run_id: str) -> str:
        return self._decision

    def cleanup(self, run_id: str) -> None:
        pass


def _make_registry(skill: Skill | None = None) -> SkillRegistry:
    registry = SkillRegistry()
    registry.register(skill or _MockSkill())
    return registry


def _make_state(skill_cache: dict | None = None) -> AgentState:
    return {
        "run_id": "run-1",
        "objective": "...",
        "tasks": [Task(description="Fazer algo")],
        "current_task_index": 0,
        "status": "running",
        "error": "",
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "skill_cache": skill_cache or {},
    }


@pytest.mark.asyncio
async def test_worker_completa_tarefa_com_sucesso():
    mock = MockLLMAdapter()
    mock.enqueue(SkillSelection, SkillSelection(skill_name="mock_skill", rationale="Melhor opção"))
    mock.enqueue(_MockParams, _MockParams(value="teste"))
    mock.enqueue(ObserveResult, ObserveResult(observations="Funcionou bem"))
    mock.enqueue(DecisionResult, DecisionResult(is_complete=True, result="Concluído"))

    e = RunEventEmitter()
    e.create("run-1")
    result = await worker_node(
        _make_state(), adapter=mock, emitter=e,
        registry=_make_registry(), hitl_store=_MockHitlStore()
    )

    assert result["tasks"][0].status == "done"
    assert result["tasks"][0].result == "Concluído"
    assert result["total_input_tokens"] == 400
    assert result["total_output_tokens"] == 200


@pytest.mark.asyncio
async def test_worker_usa_cache_quando_disponivel():
    cache_key = "mock_skill:" + __import__("hashlib").sha256(
        __import__("json").dumps({"value": "cached"}, sort_keys=True).encode()
    ).hexdigest()[:16]
    initial_cache = {cache_key: "resultado do cache"}

    mock = MockLLMAdapter()
    mock.enqueue(SkillSelection, SkillSelection(skill_name="mock_skill", rationale="r"))
    mock.enqueue(_MockParams, _MockParams(value="cached"))
    mock.enqueue(ObserveResult, ObserveResult(observations="Cache funcionou"))
    mock.enqueue(DecisionResult, DecisionResult(is_complete=True, result="Pronto"))

    e = RunEventEmitter()
    e.create("run-1")
    result = await worker_node(
        _make_state(skill_cache=initial_cache), adapter=mock, emitter=e,
        registry=_make_registry(), hitl_store=_MockHitlStore()
    )

    assert result["tasks"][0].status == "done"
    assert result["skill_cache"] == initial_cache


@pytest.mark.asyncio
async def test_worker_emite_hitl_e_executa_quando_aprovado():
    registry = _make_registry(_ApprovalSkill())

    mock = MockLLMAdapter()
    mock.enqueue(SkillSelection, SkillSelection(skill_name="approval_skill", rationale="r"))
    mock.enqueue(_MockParams, _MockParams(value="x"))
    mock.enqueue(ObserveResult, ObserveResult(observations="OK"))
    mock.enqueue(DecisionResult, DecisionResult(is_complete=True, result="Feito"))

    e = RunEventEmitter()
    e.create("run-1")
    result = await worker_node(
        _make_state(), adapter=mock, emitter=e,
        registry=registry, hitl_store=_MockHitlStore(decision="approve")
    )

    # Coletar eventos emitidos
    emitted: list = []
    while not e._queues["run-1"].empty():
        emitted.append(e._queues["run-1"].get_nowait())

    hitl_events = [ev for ev in emitted if ev.type == EventType.hitl_required]
    assert len(hitl_events) == 1
    assert hitl_events[0].payload["skill"] == "approval_skill"
    assert result["tasks"][0].status == "done"


@pytest.mark.asyncio
async def test_worker_falha_quando_rejeitado():
    registry = _make_registry(_ApprovalSkill())

    mock = MockLLMAdapter()
    mock.enqueue(SkillSelection, SkillSelection(skill_name="approval_skill", rationale="r"))
    mock.enqueue(_MockParams, _MockParams(value="x"))

    e = RunEventEmitter()
    e.create("run-1")
    result = await worker_node(
        _make_state(), adapter=mock, emitter=e,
        registry=registry, hitl_store=_MockHitlStore(decision="reject")
    )

    assert result["tasks"][0].status == "failed"
    assert "rejeitou" in result["tasks"][0].result.lower()


@pytest.mark.asyncio
async def test_worker_marca_failed_quando_nao_completo():
    mock = MockLLMAdapter()
    mock.enqueue(SkillSelection, SkillSelection(skill_name="mock_skill", rationale="r"))
    mock.enqueue(_MockParams, _MockParams(value="x"))
    mock.enqueue(ObserveResult, ObserveResult(observations="Falhou"))
    mock.enqueue(DecisionResult, DecisionResult(is_complete=False, result="Incompleto"))

    e = RunEventEmitter()
    e.create("run-1")
    result = await worker_node(
        _make_state(), adapter=mock, emitter=e,
        registry=_make_registry(), hitl_store=_MockHitlStore()
    )

    assert result["tasks"][0].status == "failed"
