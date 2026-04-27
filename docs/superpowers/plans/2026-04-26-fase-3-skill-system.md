# Fase 3 — Skill System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Skill Registry com autodiscovery e 4 skills funcionando — WebSearch, CodeInterpreter, TimeManager e FileWriter — com o Worker selecionando skills reais via LLM e cache de resultados no estado do run.

**Architecture:** `Skill` ABC define o contrato; `SkillRegistry` faz autodiscovery de qualquer arquivo em `apps/server/skills/` que contenha uma subclasse de `Skill`. O `worker_node` é refatorado para dois passos de LLM: (1) selecionar skill por nome, (2) gerar parâmetros no schema da skill escolhida. Skills com `requires_approval=True` emitem evento `hitl_required` antes de executar, mas continuam a execução (pause real é Fase 5). Cache de resultados no `AgentState.skill_cache` usa SHA-256 dos parâmetros como chave.

**Tech Stack:** `tavily-python` (WebSearch), `e2b-code-interpreter` (CodeInterpreter), `pendulum` (TimeManager), `supabase-py` já instalado (FileWriter). Todos os clientes externos inicializados dentro de `execute()`, não no import. Testes usam mocks para APIs externas.

---

## File Structure

**Novos:**
- `apps/server/skills/__init__.py` — pacote vazio
- `apps/server/skills/base.py` — `Skill` ABC + `SkillResult` + `SkillMetadata`
- `apps/server/skills/registry.py` — `SkillRegistry`
- `apps/server/skills/time_manager.py` — `TimeManager` (pendulum, sem API externa)
- `apps/server/skills/web_search.py` — `WebSearch` (Tavily)
- `apps/server/skills/code_interpreter.py` — `CodeInterpreter` (E2B, `requires_approval=True`)
- `apps/server/skills/file_writer.py` — `FileWriter` (Supabase Storage, `requires_approval=True`)
- `apps/server/api/deps.py` — singleton `_registry` compartilhado entre rotas
- `apps/server/api/routes/skills.py` — `GET /api/v1/skills`
- `apps/server/tests/unit/test_skill_registry.py` — testes do SkillRegistry
- `apps/server/tests/unit/test_skill_time_manager.py`
- `apps/server/tests/unit/test_skill_web_search.py`
- `apps/server/tests/unit/test_skill_code_interpreter.py`
- `apps/server/tests/unit/test_skill_file_writer.py`
- `apps/server/tests/integration/test_skills_api.py`

**Modificados:**
- `apps/server/requirements.txt` — adicionar tavily-python, e2b-code-interpreter, pendulum
- `apps/server/core/config.py` — adicionar tavily_api_key, e2b_api_key
- `apps/server/core/events.py` — adicionar `hitl_required` e `skill_called` ao `EventType`
- `apps/server/agents/state.py` — adicionar `skill_cache: dict`
- `apps/server/agents/worker.py` — refatorar para SkillRegistry + seleção em dois passos + cache + HITL
- `apps/server/agents/graph.py` — receber `registry: SkillRegistry` em vez de criar `MockSkill`
- `apps/server/api/routes/runs.py` — usar `_registry` e atualizar `initial_state` com `skill_cache`
- `apps/server/api/main.py` — registrar `skills` router
- `apps/server/tests/unit/test_worker.py` — reescrever com registry fixture
- `apps/server/tests/integration/test_graph.py` — reescrever com registry fixture
- `apps/server/tests/unit/test_supervisor.py` — adicionar `skill_cache: {}` ao `_make_state()`
- `apps/server/tests/unit/test_nodes.py` — adicionar `skill_cache: {}` ao `_make_state()`
- `apps/server/tests/unit/test_llm_adapter.py` — adicionar `skill_cache: {}` ao `_make_state()`

---

## Task 1: Worktree, deps e atualizações de state

**Files:**
- Worktree: `.worktrees/fase-3/`
- Modify: `apps/server/requirements.txt`
- Modify: `apps/server/core/config.py`
- Modify: `apps/server/core/events.py`
- Modify: `apps/server/agents/state.py`
- Modify: `apps/server/tests/unit/test_supervisor.py`
- Modify: `apps/server/tests/unit/test_nodes.py`
- Modify: `apps/server/tests/unit/test_llm_adapter.py`

- [ ] **Step 1: Criar branch e worktree**

```bash
git worktree add .worktrees/fase-3 -b feat/fase-3-skill-system
```

Expected output: `Preparing worktree (new branch 'feat/fase-3-skill-system')`

- [ ] **Step 2: Atualizar requirements.txt**

Conteúdo final de `apps/server/requirements.txt`:
```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.9.0
pydantic-settings>=2.5.0
PyJWT>=2.9.0
cryptography>=43.0.0
structlog>=24.4.0
httpx>=0.27.0
supabase>=2.4.0,<2.9.0
langgraph>=0.2.50,<0.3
langchain-google-genai>=1.0.0
google-generativeai>=0.7.0
sse-starlette>=1.8.0
slowapi>=0.1.9
tavily-python>=0.3.0
e2b-code-interpreter>=0.0.10
pendulum>=3.0.0
```

- [ ] **Step 3: Instalar novas dependências**

```bash
cd .worktrees/fase-3/apps/server && pip install -r requirements.txt
```

Expected: sem erros de resolução de versão.

- [ ] **Step 4: Adicionar tavily_api_key e e2b_api_key ao config.py**

Conteúdo final de `apps/server/core/config.py`:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_jwt_secret: str = ""

    gemini_api_key: str = ""
    langsmith_api_key: str = ""
    langsmith_project: str = "aether-os"

    tavily_api_key: str = ""
    e2b_api_key: str = ""

    frontend_url: str = "http://localhost:3000"
    default_budget_limit: int = 10000
    max_requests_per_minute: int = 20
    log_level: str = "INFO"


settings = Settings()
```

- [ ] **Step 5: Adicionar hitl_required e skill_called ao EventType**

Conteúdo final de `apps/server/core/events.py`:
```python
import asyncio
from enum import Enum

from pydantic import BaseModel


class EventType(str, Enum):
    agent_started = "agent_started"
    task_started = "task_started"
    task_completed = "task_completed"
    skill_called = "skill_called"
    hitl_required = "hitl_required"
    run_completed = "run_completed"
    run_failed = "run_failed"
    budget_warning = "budget_warning"


class RunEvent(BaseModel):
    run_id: str
    type: EventType
    payload: dict = {}


class RunEventEmitter:
    def __init__(self) -> None:
        self._queues: dict[str, asyncio.Queue[RunEvent | None]] = {}

    def create(self, run_id: str) -> None:
        self._queues[run_id] = asyncio.Queue()

    async def emit(self, event: RunEvent) -> None:
        q = self._queues.get(event.run_id)
        if q:
            await q.put(event)

    async def close(self, run_id: str) -> None:
        q = self._queues.get(run_id)
        if q:
            await q.put(None)

    async def listen(self, run_id: str):
        q = self._queues.get(run_id)
        if not q:
            return
        while True:
            event = await q.get()
            if event is None:
                break
            yield event
        del self._queues[run_id]


emitter = RunEventEmitter()
```

- [ ] **Step 6: Adicionar skill_cache ao AgentState**

Conteúdo final de `apps/server/agents/state.py`:
```python
from typing import TypedDict

from pydantic import BaseModel


class Task(BaseModel):
    description: str
    result: str = ""
    status: str = "pending"  # pending | running | done | failed


class AgentState(TypedDict):
    run_id: str
    objective: str
    tasks: list[Task]
    current_task_index: int
    status: str   # running | completed | failed
    error: str
    total_input_tokens: int
    total_output_tokens: int
    skill_cache: dict  # key: "{skill_name}:{sha256_params_hex[:16]}" → output str
```

- [ ] **Step 7: Atualizar _make_state() em test_supervisor.py**

Localizar a função `_make_state` em `apps/server/tests/unit/test_supervisor.py` e adicionar `"skill_cache": {}`:
```python
def _make_state() -> AgentState:
    return {
        "run_id": "run-1",
        "objective": "Construir um blog",
        "tasks": [],
        "current_task_index": 0,
        "status": "running",
        "error": "",
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "skill_cache": {},
    }
```

- [ ] **Step 8: Atualizar _make_state() em test_nodes.py**

Localizar a função `_make_state` em `apps/server/tests/unit/test_nodes.py` e adicionar `"skill_cache": {}`:
```python
def _make_state(**overrides) -> AgentState:
    base: AgentState = {
        "run_id": "run-1",
        "objective": "test",
        "tasks": [Task(description="T1", status="done")],
        "current_task_index": 0,
        "status": "running",
        "error": "",
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "skill_cache": {},
    }
    return {**base, **overrides}
```

- [ ] **Step 9: Atualizar _make_state() em test_llm_adapter.py**

Localizar a função `_make_state` em `apps/server/tests/unit/test_llm_adapter.py` e adicionar `"skill_cache": {}`:
```python
def _make_state() -> AgentState:
    return {
        "run_id": "r1",
        "objective": "test",
        "tasks": [],
        "current_task_index": 0,
        "status": "running",
        "error": "",
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "skill_cache": {},
    }
```

- [ ] **Step 10: Confirmar que testes existentes ainda passam**

```bash
cd .worktrees/fase-3/apps/server && pytest tests/unit/test_supervisor.py tests/unit/test_nodes.py tests/unit/test_llm_adapter.py tests/unit/test_budget.py tests/unit/test_security.py tests/unit/test_events.py -v
```

Expected: todos passam.

- [ ] **Step 11: Commit**

```bash
git add apps/server/requirements.txt apps/server/core/config.py apps/server/core/events.py apps/server/agents/state.py apps/server/tests/unit/test_supervisor.py apps/server/tests/unit/test_nodes.py apps/server/tests/unit/test_llm_adapter.py
git commit -m "chore: adiciona deps, skill_cache no AgentState e hitl_required no EventType"
```

---

## Task 2: skills/base.py — Skill ABC + SkillResult + SkillMetadata

**Files:**
- Create: `apps/server/skills/__init__.py`
- Create: `apps/server/skills/base.py`

Não há testes unitários isolados para a ABC — validada pelos testes de skills concretas.

- [ ] **Step 1: Criar o pacote skills**

`apps/server/skills/__init__.py` — arquivo vazio.

- [ ] **Step 2: Criar skills/base.py**

`apps/server/skills/base.py`:
```python
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
```

- [ ] **Step 3: Confirmar que importação funciona**

```bash
cd .worktrees/fase-3/apps/server && python -c "from skills.base import Skill, SkillResult, SkillMetadata; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add apps/server/skills/__init__.py apps/server/skills/base.py
git commit -m "feat: adiciona Skill ABC, SkillResult e SkillMetadata"
```

---

## Task 3: skills/registry.py — SkillRegistry

**Files:**
- Create: `apps/server/skills/registry.py`
- Create: `apps/server/tests/unit/test_skill_registry.py`

- [ ] **Step 1: Escrever os testes (falha esperada)**

`apps/server/tests/unit/test_skill_registry.py`:
```python
import pytest
from pydantic import BaseModel
from skills.base import Skill, SkillResult
from skills.registry import SkillRegistry


class _DummyParams(BaseModel):
    value: str


class _DummySkill(Skill):
    name = "dummy"
    description = "Skill de teste"
    parameters = _DummyParams
    requires_approval = False

    async def execute(self, params: BaseModel) -> SkillResult:
        return SkillResult(success=True, output=f"dummy:{params.value}")


def test_register_e_get():
    registry = SkillRegistry()
    registry.register(_DummySkill())
    skill = registry.get("dummy")
    assert skill.name == "dummy"


def test_get_skill_desconhecida_levanta_key_error():
    registry = SkillRegistry()
    with pytest.raises(KeyError, match="nao_existe"):
        registry.get("nao_existe")


def test_list_all_retorna_metadados():
    registry = SkillRegistry()
    registry.register(_DummySkill())
    metas = registry.list_all()
    assert len(metas) == 1
    assert metas[0].name == "dummy"
    assert metas[0].requires_approval is False
    assert "value" in metas[0].parameters_schema["properties"]


def test_skill_names():
    registry = SkillRegistry()
    registry.register(_DummySkill())
    assert "dummy" in registry.skill_names()


def test_autodiscover_encontra_skills(tmp_path):
    # Escreve um arquivo de skill no diretório temporário
    skill_file = tmp_path / "test_auto.py"
    skill_file.write_text(
        """
from pydantic import BaseModel
from skills.base import Skill, SkillResult

class _AutoParams(BaseModel):
    x: str

class AutoSkill(Skill):
    name = "auto_skill"
    description = "Auto skill"
    parameters = _AutoParams
    async def execute(self, params):
        return SkillResult(success=True, output="auto")
"""
    )
    registry = SkillRegistry.autodiscover(tmp_path)
    assert "auto_skill" in registry.skill_names()
```

- [ ] **Step 2: Executar e confirmar falha**

```bash
cd .worktrees/fase-3/apps/server && pytest tests/unit/test_skill_registry.py -v
```

Expected: `ModuleNotFoundError: No module named 'skills.registry'`

- [ ] **Step 3: Implementar skills/registry.py**

`apps/server/skills/registry.py`:
```python
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
```

- [ ] **Step 4: Executar e confirmar aprovação**

```bash
cd .worktrees/fase-3/apps/server && pytest tests/unit/test_skill_registry.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/server/skills/registry.py apps/server/tests/unit/test_skill_registry.py
git commit -m "feat: adiciona SkillRegistry com register, get, list_all e autodiscover"
```

---

## Task 4: skills/time_manager.py — TimeManager

**Files:**
- Create: `apps/server/skills/time_manager.py`
- Create: `apps/server/tests/unit/test_skill_time_manager.py`

- [ ] **Step 1: Escrever os testes (falha esperada)**

`apps/server/tests/unit/test_skill_time_manager.py`:
```python
import pytest
from pydantic import BaseModel
from skills.time_manager import TimeManager, TimeManagerParams


@pytest.mark.asyncio
async def test_time_manager_retorna_data_atual():
    skill = TimeManager()
    result = await skill.execute(TimeManagerParams(query="Que horas são agora?"))
    assert result.success is True
    assert len(result.output) > 10
    assert "UTC" in result.output


@pytest.mark.asyncio
async def test_time_manager_inclui_query_na_resposta():
    skill = TimeManager()
    result = await skill.execute(TimeManagerParams(query="Quantos dias até sexta?"))
    assert "Quantos dias" in result.output


def test_time_manager_metadados():
    skill = TimeManager()
    meta = skill.metadata()
    assert meta.name == "time_manager"
    assert meta.requires_approval is False
    assert "query" in meta.parameters_schema["properties"]
```

- [ ] **Step 2: Executar e confirmar falha**

```bash
cd .worktrees/fase-3/apps/server && pytest tests/unit/test_skill_time_manager.py -v
```

Expected: `ModuleNotFoundError: No module named 'skills.time_manager'`

- [ ] **Step 3: Implementar skills/time_manager.py**

`apps/server/skills/time_manager.py`:
```python
import pendulum
from pydantic import BaseModel

from skills.base import Skill, SkillResult


class TimeManagerParams(BaseModel):
    query: str


class TimeManager(Skill):
    name = "time_manager"
    description = (
        "Responde perguntas sobre tempo: data e hora atual, fuso horário, "
        "cálculo de duração entre datas."
    )
    parameters = TimeManagerParams
    requires_approval = False

    async def execute(self, params: BaseModel) -> SkillResult:
        assert isinstance(params, TimeManagerParams)
        now = pendulum.now("UTC")
        return SkillResult(
            success=True,
            output=f"Agora é {now.to_rfc2822_string()} (UTC). Consulta: {params.query}",
            metadata={"timestamp_utc": now.isoformat()},
        )
```

- [ ] **Step 4: Executar e confirmar aprovação**

```bash
cd .worktrees/fase-3/apps/server && pytest tests/unit/test_skill_time_manager.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/server/skills/time_manager.py apps/server/tests/unit/test_skill_time_manager.py
git commit -m "feat: adiciona skill TimeManager com pendulum"
```

---

## Task 5: skills/web_search.py — WebSearch

**Files:**
- Create: `apps/server/skills/web_search.py`
- Create: `apps/server/tests/unit/test_skill_web_search.py`

- [ ] **Step 1: Escrever os testes (falha esperada)**

`apps/server/tests/unit/test_skill_web_search.py`:
```python
import pytest
from unittest.mock import MagicMock, patch
from skills.web_search import WebSearch, WebSearchParams


@pytest.mark.asyncio
async def test_web_search_retorna_resultados():
    mock_response = {
        "results": [
            {"title": "Título A", "content": "Conteúdo A"},
            {"title": "Título B", "content": "Conteúdo B"},
        ]
    }
    with patch("skills.web_search.TavilyClient") as MockClient:
        MockClient.return_value.search.return_value = mock_response
        skill = WebSearch()
        result = await skill.execute(WebSearchParams(query="Python LangGraph", max_results=2))

    assert result.success is True
    assert "Título A" in result.output
    assert "Título B" in result.output
    assert result.metadata["results_count"] == 2


@pytest.mark.asyncio
async def test_web_search_sem_resultados():
    with patch("skills.web_search.TavilyClient") as MockClient:
        MockClient.return_value.search.return_value = {"results": []}
        skill = WebSearch()
        result = await skill.execute(WebSearchParams(query="xyz_inexistente_abc"))

    assert result.success is True
    assert "Nenhum resultado" in result.output


@pytest.mark.asyncio
async def test_web_search_falha_de_api():
    with patch("skills.web_search.TavilyClient") as MockClient:
        MockClient.return_value.search.side_effect = Exception("API Error")
        skill = WebSearch()
        result = await skill.execute(WebSearchParams(query="teste"))

    assert result.success is False
    assert result.error is not None


def test_web_search_metadados():
    skill = WebSearch()
    meta = skill.metadata()
    assert meta.name == "web_search"
    assert meta.requires_approval is False
    assert "query" in meta.parameters_schema["properties"]
```

- [ ] **Step 2: Executar e confirmar falha**

```bash
cd .worktrees/fase-3/apps/server && pytest tests/unit/test_skill_web_search.py -v
```

Expected: `ModuleNotFoundError: No module named 'skills.web_search'`

- [ ] **Step 3: Implementar skills/web_search.py**

`apps/server/skills/web_search.py`:
```python
from pydantic import BaseModel

from skills.base import Skill, SkillResult


class WebSearchParams(BaseModel):
    query: str
    max_results: int = 5


class WebSearch(Skill):
    name = "web_search"
    description = (
        "Busca informações atuais na internet. Use para fatos recentes, "
        "notícias, documentação e pesquisa sobre qualquer tema."
    )
    parameters = WebSearchParams
    requires_approval = False

    async def execute(self, params: BaseModel) -> SkillResult:
        assert isinstance(params, WebSearchParams)
        try:
            from tavily import TavilyClient

            from core.config import settings

            client = TavilyClient(api_key=settings.tavily_api_key)
            response = client.search(params.query, max_results=params.max_results)
            results = response.get("results", [])
            output = "\n".join(
                f"- {r['title']}: {r['content']}" for r in results[: params.max_results]
            )
            return SkillResult(
                success=True,
                output=output or "Nenhum resultado encontrado.",
                metadata={"results_count": len(results)},
            )
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))
```

- [ ] **Step 4: Executar e confirmar aprovação**

```bash
cd .worktrees/fase-3/apps/server && pytest tests/unit/test_skill_web_search.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/server/skills/web_search.py apps/server/tests/unit/test_skill_web_search.py
git commit -m "feat: adiciona skill WebSearch com Tavily"
```

---

## Task 6: skills/code_interpreter.py — CodeInterpreter

**Files:**
- Create: `apps/server/skills/code_interpreter.py`
- Create: `apps/server/tests/unit/test_skill_code_interpreter.py`

- [ ] **Step 1: Escrever os testes (falha esperada)**

`apps/server/tests/unit/test_skill_code_interpreter.py`:
```python
import pytest
from typing import Literal
from unittest.mock import MagicMock, patch
from skills.code_interpreter import CodeInterpreter, CodeInterpreterParams


@pytest.mark.asyncio
async def test_code_interpreter_executa_codigo():
    mock_exec = MagicMock()
    mock_exec.logs.stdout = ["Hello World\n"]
    mock_exec.logs.stderr = []

    mock_sandbox = MagicMock()
    mock_sandbox.__enter__ = MagicMock(return_value=mock_sandbox)
    mock_sandbox.__exit__ = MagicMock(return_value=False)
    mock_sandbox.run_code.return_value = mock_exec

    with patch("skills.code_interpreter.Sandbox", return_value=mock_sandbox):
        skill = CodeInterpreter()
        result = await skill.execute(CodeInterpreterParams(code='print("Hello World")'))

    assert result.success is True
    assert "Hello World" in result.output


@pytest.mark.asyncio
async def test_code_interpreter_retorna_stderr_como_error():
    mock_exec = MagicMock()
    mock_exec.logs.stdout = []
    mock_exec.logs.stderr = ["NameError: name 'x' is not defined\n"]

    mock_sandbox = MagicMock()
    mock_sandbox.__enter__ = MagicMock(return_value=mock_sandbox)
    mock_sandbox.__exit__ = MagicMock(return_value=False)
    mock_sandbox.run_code.return_value = mock_exec

    with patch("skills.code_interpreter.Sandbox", return_value=mock_sandbox):
        skill = CodeInterpreter()
        result = await skill.execute(CodeInterpreterParams(code="print(x)"))

    assert result.success is False
    assert "NameError" in result.error


def test_code_interpreter_requires_approval():
    skill = CodeInterpreter()
    assert skill.requires_approval is True


def test_code_interpreter_metadados():
    skill = CodeInterpreter()
    meta = skill.metadata()
    assert meta.name == "code_interpreter"
    assert meta.requires_approval is True
    assert "code" in meta.parameters_schema["properties"]
```

- [ ] **Step 2: Executar e confirmar falha**

```bash
cd .worktrees/fase-3/apps/server && pytest tests/unit/test_skill_code_interpreter.py -v
```

Expected: `ModuleNotFoundError: No module named 'skills.code_interpreter'`

- [ ] **Step 3: Implementar skills/code_interpreter.py**

`apps/server/skills/code_interpreter.py`:
```python
from typing import Literal

from pydantic import BaseModel

from skills.base import Skill, SkillResult


class CodeInterpreterParams(BaseModel):
    code: str
    language: Literal["python"] = "python"


class CodeInterpreter(Skill):
    name = "code_interpreter"
    description = (
        "Executa código Python em sandbox seguro e isolado (E2B). "
        "Ideal para cálculos, análise de dados e automação. Requer aprovação humana."
    )
    parameters = CodeInterpreterParams
    requires_approval = True

    async def execute(self, params: BaseModel) -> SkillResult:
        assert isinstance(params, CodeInterpreterParams)
        from e2b_code_interpreter import Sandbox

        from core.config import settings

        with Sandbox(api_key=settings.e2b_api_key) as sandbox:
            execution = sandbox.run_code(params.code)
            stdout = "\n".join(execution.logs.stdout)
            stderr = "\n".join(execution.logs.stderr)

        if stderr:
            return SkillResult(success=False, output=stdout, error=stderr)
        return SkillResult(success=True, output=stdout or "(sem output)")
```

- [ ] **Step 4: Executar e confirmar aprovação**

```bash
cd .worktrees/fase-3/apps/server && pytest tests/unit/test_skill_code_interpreter.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/server/skills/code_interpreter.py apps/server/tests/unit/test_skill_code_interpreter.py
git commit -m "feat: adiciona skill CodeInterpreter com E2B sandbox"
```

---

## Task 7: skills/file_writer.py — FileWriter

**Files:**
- Create: `apps/server/skills/file_writer.py`
- Create: `apps/server/tests/unit/test_skill_file_writer.py`

- [ ] **Step 1: Escrever os testes (falha esperada)**

`apps/server/tests/unit/test_skill_file_writer.py`:
```python
import pytest
from typing import Literal
from unittest.mock import MagicMock, patch
from skills.file_writer import FileWriter, FileWriterParams


@pytest.mark.asyncio
async def test_file_writer_salva_e_retorna_url():
    mock_storage = MagicMock()
    mock_storage.from_.return_value.upload.return_value = MagicMock()
    mock_storage.from_.return_value.get_public_url.return_value = (
        "https://example.com/artifacts/relatorio.md"
    )

    mock_client = MagicMock()
    mock_client.storage = mock_storage

    with patch("skills.file_writer.create_client", return_value=mock_client):
        skill = FileWriter()
        result = await skill.execute(
            FileWriterParams(filename="relatorio", content="# Relatório\nConteúdo aqui.", format="md")
        )

    assert result.success is True
    assert "https://example.com" in result.output
    assert result.metadata["url"] == "https://example.com/artifacts/relatorio.md"


@pytest.mark.asyncio
async def test_file_writer_falha_de_upload():
    mock_storage = MagicMock()
    mock_storage.from_.return_value.upload.side_effect = Exception("Storage Error")

    mock_client = MagicMock()
    mock_client.storage = mock_storage

    with patch("skills.file_writer.create_client", return_value=mock_client):
        skill = FileWriter()
        result = await skill.execute(
            FileWriterParams(filename="teste", content="conteúdo", format="txt")
        )

    assert result.success is False
    assert result.error is not None


def test_file_writer_requires_approval():
    skill = FileWriter()
    assert skill.requires_approval is True


def test_file_writer_metadados():
    skill = FileWriter()
    meta = skill.metadata()
    assert meta.name == "file_writer"
    assert meta.requires_approval is True
    assert "filename" in meta.parameters_schema["properties"]
    assert "content" in meta.parameters_schema["properties"]
```

- [ ] **Step 2: Executar e confirmar falha**

```bash
cd .worktrees/fase-3/apps/server && pytest tests/unit/test_skill_file_writer.py -v
```

Expected: `ModuleNotFoundError: No module named 'skills.file_writer'`

- [ ] **Step 3: Implementar skills/file_writer.py**

`apps/server/skills/file_writer.py`:
```python
from typing import Literal

from pydantic import BaseModel

from skills.base import Skill, SkillResult


class FileWriterParams(BaseModel):
    filename: str
    content: str
    format: Literal["md", "txt"] = "md"


class FileWriter(Skill):
    name = "file_writer"
    description = (
        "Salva um arquivo de texto no Supabase Storage e retorna a URL pública. "
        "Use para gerar relatórios, documentos e outputs persistentes. Requer aprovação humana."
    )
    parameters = FileWriterParams
    requires_approval = True

    async def execute(self, params: BaseModel) -> SkillResult:
        assert isinstance(params, FileWriterParams)
        try:
            from supabase import create_client

            from core.config import settings

            supabase = create_client(settings.supabase_url, settings.supabase_service_key)
            path = f"{params.filename}.{params.format}"
            data = params.content.encode("utf-8")
            supabase.storage.from_("artifacts").upload(
                path, data, {"content-type": "text/plain; charset=utf-8"}
            )
            url = supabase.storage.from_("artifacts").get_public_url(path)
            return SkillResult(
                success=True,
                output=f"Arquivo salvo em: {url}",
                metadata={"url": url, "path": path},
            )
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))
```

- [ ] **Step 4: Executar e confirmar aprovação**

```bash
cd .worktrees/fase-3/apps/server && pytest tests/unit/test_skill_file_writer.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Executar todas as skills**

```bash
cd .worktrees/fase-3/apps/server && pytest tests/unit/test_skill_registry.py tests/unit/test_skill_time_manager.py tests/unit/test_skill_web_search.py tests/unit/test_skill_code_interpreter.py tests/unit/test_skill_file_writer.py -v
```

Expected: todos passam.

- [ ] **Step 6: Commit**

```bash
git add apps/server/skills/file_writer.py apps/server/tests/unit/test_skill_file_writer.py
git commit -m "feat: adiciona skill FileWriter com Supabase Storage"
```

---

## Task 8: Refatorar agents/worker.py — seleção em dois passos + cache + HITL

**Files:**
- Modify: `apps/server/agents/worker.py`
- Modify: `apps/server/tests/unit/test_worker.py`

O Worker agora usa `SkillRegistry`. O Think é dividido em dois passos de LLM:
1. LLM escolhe a skill pelo nome (`SkillSelection`)
2. LLM gera os parâmetros no schema da skill escolhida

Cache verifica antes de executar. Skills com `requires_approval=True` emitem `hitl_required` mas executam.

- [ ] **Step 1: Escrever os novos testes do worker (falha esperada)**

Conteúdo completo de `apps/server/tests/unit/test_worker.py`:
```python
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
    result = await worker_node(_make_state(), adapter=mock, emitter=e, registry=_make_registry())

    assert result["tasks"][0].status == "done"
    assert result["tasks"][0].result == "Concluído"
    assert result["total_input_tokens"] == 400   # 4 chamadas × 100
    assert result["total_output_tokens"] == 200  # 4 chamadas × 50


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
        _make_state(skill_cache=initial_cache), adapter=mock, emitter=e, registry=_make_registry()
    )

    assert result["tasks"][0].status == "done"
    # Skill não foi chamada diretamente (cache hit), mas o resultado ainda existe
    assert result["skill_cache"] == initial_cache  # cache inalterado pois era hit


@pytest.mark.asyncio
async def test_worker_emite_hitl_para_skill_com_approval():
    registry = _make_registry(_ApprovalSkill())

    mock = MockLLMAdapter()
    mock.enqueue(SkillSelection, SkillSelection(skill_name="approval_skill", rationale="r"))
    mock.enqueue(_MockParams, _MockParams(value="x"))
    mock.enqueue(ObserveResult, ObserveResult(observations="OK"))
    mock.enqueue(DecisionResult, DecisionResult(is_complete=True, result="Feito"))

    e = RunEventEmitter()
    e.create("run-1")

    emitted_events: list = []

    async def _collect():
        async for ev in e.listen("run-1"):
            emitted_events.append(ev)

    import asyncio
    collect_task = asyncio.create_task(_collect())
    await worker_node(_make_state(), adapter=mock, emitter=e, registry=registry)
    await e.close("run-1")
    await collect_task

    hitl_events = [ev for ev in emitted_events if ev.type == EventType.hitl_required]
    assert len(hitl_events) == 1
    assert hitl_events[0].payload["skill"] == "approval_skill"


@pytest.mark.asyncio
async def test_worker_marca_failed_quando_nao_completo():
    mock = MockLLMAdapter()
    mock.enqueue(SkillSelection, SkillSelection(skill_name="mock_skill", rationale="r"))
    mock.enqueue(_MockParams, _MockParams(value="x"))
    mock.enqueue(ObserveResult, ObserveResult(observations="Falhou"))
    mock.enqueue(DecisionResult, DecisionResult(is_complete=False, result="Incompleto"))

    e = RunEventEmitter()
    e.create("run-1")
    result = await worker_node(_make_state(), adapter=mock, emitter=e, registry=_make_registry())

    assert result["tasks"][0].status == "failed"
```

- [ ] **Step 2: Executar e confirmar falha**

```bash
cd .worktrees/fase-3/apps/server && pytest tests/unit/test_worker.py -v
```

Expected: erros de importação — `SkillSelection` e `SkillRegistry` não existem no worker ainda.

- [ ] **Step 3: Implementar o novo agents/worker.py**

Conteúdo completo de `apps/server/agents/worker.py`:
```python
import hashlib
import json

from pydantic import BaseModel

from agents.state import AgentState, Task
from core.events import EventType, RunEvent, RunEventEmitter
from core.llm_adapter import BaseLLMAdapter
from skills.registry import SkillRegistry


class SkillSelection(BaseModel):
    skill_name: str
    rationale: str


class ObserveResult(BaseModel):
    observations: str


class DecisionResult(BaseModel):
    is_complete: bool
    result: str


def _cache_key(skill_name: str, params: BaseModel) -> str:
    params_json = json.dumps(params.model_dump(), sort_keys=True)
    digest = hashlib.sha256(params_json.encode()).hexdigest()[:16]
    return f"{skill_name}:{digest}"


async def worker_node(
    state: AgentState,
    *,
    adapter: BaseLLMAdapter,
    emitter: RunEventEmitter,
    registry: SkillRegistry,
) -> dict:
    idx = state["current_task_index"]
    task = state["tasks"][idx]

    await emitter.emit(RunEvent(
        run_id=state["run_id"],
        type=EventType.task_started,
        payload={"task": task.description, "index": idx},
    ))

    total_input = state["total_input_tokens"]
    total_output = state["total_output_tokens"]

    # Think step 1: selecionar skill
    skill_list = "\n".join(
        f"- {m.name}: {m.description}" for m in registry.list_all()
    )
    selection_prompt = (
        f"Skills disponíveis:\n{skill_list}\n\n"
        f"Objetivo: {state['objective']}\n"
        f"Tarefa atual: {task.description}\n\n"
        f"Escolha a skill mais adequada para executar esta tarefa."
    )
    selection, i1, o1 = await adapter.generate(selection_prompt, SkillSelection, state)
    total_input += i1
    total_output += o1

    skill = registry.get(selection.skill_name)

    # Think step 2: gerar parâmetros no schema da skill
    params_prompt = (
        f"Tarefa: {task.description}\n"
        f"Skill escolhida: {skill.name}\n"
        f"Gere os parâmetros necessários para executar esta skill."
    )
    params, i2, o2 = await adapter.generate(params_prompt, skill.parameters, state)
    total_input += i2
    total_output += o2

    # Cache check
    key = _cache_key(skill.name, params)
    updated_cache = dict(state["skill_cache"])

    if key in updated_cache:
        skill_output = updated_cache[key]
    else:
        # HITL: emite evento se skill requer aprovação (pause real é Fase 5)
        if skill.requires_approval:
            await emitter.emit(RunEvent(
                run_id=state["run_id"],
                type=EventType.hitl_required,
                payload={"skill": skill.name, "params": params.model_dump()},
            ))

        await emitter.emit(RunEvent(
            run_id=state["run_id"],
            type=EventType.skill_called,
            payload={"skill": skill.name},
        ))

        skill_result = await skill.execute(params)
        skill_output = skill_result.output
        updated_cache[key] = skill_output

    # Observe
    observe_prompt = (
        f"Tarefa: {task.description}\n"
        f"Resultado da skill '{skill.name}': {skill_output}\n"
        f"Quais são suas observações sobre o resultado?"
    )
    observe_result, i3, o3 = await adapter.generate(observe_prompt, ObserveResult, state)
    total_input += i3
    total_output += o3

    # Decide
    decide_prompt = (
        f"Tarefa: {task.description}\n"
        f"Observações: {observe_result.observations}\n"
        f"A tarefa está completa com base nessas observações?"
    )
    decision, i4, o4 = await adapter.generate(decide_prompt, DecisionResult, state)
    total_input += i4
    total_output += o4

    updated_status = "done" if decision.is_complete else "failed"
    updated_tasks = list(state["tasks"])
    updated_tasks[idx] = task.model_copy(
        update={"result": decision.result, "status": updated_status}
    )

    return {
        "tasks": updated_tasks,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "skill_cache": updated_cache,
    }
```

- [ ] **Step 4: Executar e confirmar aprovação**

```bash
cd .worktrees/fase-3/apps/server && pytest tests/unit/test_worker.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/server/agents/worker.py apps/server/tests/unit/test_worker.py
git commit -m "feat: refatora worker_node para SkillRegistry com seleção em dois passos e cache"
```

---

## Task 9: Refatorar agents/graph.py + api/routes/runs.py + testes de integração

**Files:**
- Modify: `apps/server/agents/graph.py`
- Modify: `apps/server/api/routes/runs.py`
- Create: `apps/server/api/deps.py`
- Modify: `apps/server/tests/integration/test_graph.py`

- [ ] **Step 1: Reescrever os testes de integração do graph (falha esperada)**

Conteúdo completo de `apps/server/tests/integration/test_graph.py`:
```python
import pytest
from agents.graph import build_graph
from agents.state import AgentState
from agents.supervisor import TaskPlan
from agents.worker import DecisionResult, ObserveResult, SkillSelection
from core.budget import BudgetController
from core.events import RunEventEmitter
from core.llm_adapter import MockLLMAdapter
from pydantic import BaseModel
from skills.base import Skill, SkillResult
from skills.registry import SkillRegistry


class _MockParams(BaseModel):
    value: str


class _MockSkill(Skill):
    name = "mock_skill"
    description = "Skill para testes de integração"
    parameters = _MockParams
    requires_approval = False

    async def execute(self, params: BaseModel) -> SkillResult:
        return SkillResult(success=True, output="resultado_mock")


def _make_registry() -> SkillRegistry:
    r = SkillRegistry()
    r.register(_MockSkill())
    return r


def _initial_state(run_id: str = "run-1") -> AgentState:
    return {
        "run_id": run_id,
        "objective": "Objetivo simples",
        "tasks": [],
        "current_task_index": 0,
        "status": "running",
        "error": "",
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "skill_cache": {},
    }


@pytest.mark.asyncio
async def test_graph_completa_run_com_uma_tarefa():
    mock = MockLLMAdapter()
    mock.enqueue(TaskPlan, TaskPlan(tasks=["Tarefa única"]))
    mock.enqueue(SkillSelection, SkillSelection(skill_name="mock_skill", rationale="OK"))
    mock.enqueue(_MockParams, _MockParams(value="x"))
    mock.enqueue(ObserveResult, ObserveResult(observations="Funcionou"))
    mock.enqueue(DecisionResult, DecisionResult(is_complete=True, result="Pronto"))

    e = RunEventEmitter()
    e.create("run-1")
    budget = BudgetController(limit_tokens=10000)
    registry = _make_registry()
    graph = build_graph(adapter=mock, budget=budget, emitter=e, registry=registry)

    result = await graph.ainvoke(_initial_state())

    assert result["status"] == "completed"
    assert len(result["tasks"]) == 1
    assert result["tasks"][0].status == "done"
    assert result["tasks"][0].result == "Pronto"


@pytest.mark.asyncio
async def test_graph_falha_se_budget_excedido():
    mock = MockLLMAdapter()
    mock.enqueue(TaskPlan, TaskPlan(tasks=["T1"]))

    e = RunEventEmitter()
    e.create("run-1")
    budget = BudgetController(limit_tokens=1)

    state = _initial_state()
    state["total_input_tokens"] = 100  # já começa acima do limite

    registry = _make_registry()
    graph = build_graph(adapter=mock, budget=budget, emitter=e, registry=registry)

    result = await graph.ainvoke(state)
    assert result["status"] == "failed"
    assert "excedido" in result["error"].lower()
```

- [ ] **Step 2: Executar e confirmar falha**

```bash
cd .worktrees/fase-3/apps/server && pytest tests/integration/test_graph.py -v
```

Expected: erro porque `build_graph` não aceita `registry` ainda.

- [ ] **Step 3: Atualizar agents/graph.py**

Conteúdo completo de `apps/server/agents/graph.py`:
```python
import functools

from langgraph.graph import END, START, StateGraph

from agents.nodes import budget_gate_node, evaluate_result_node, finalize_node
from agents.state import AgentState
from agents.supervisor import supervisor_node
from agents.worker import worker_node
from core.budget import BudgetController
from core.events import RunEventEmitter
from core.llm_adapter import BaseLLMAdapter
from skills.registry import SkillRegistry


def build_graph(
    *,
    adapter: BaseLLMAdapter,
    budget: BudgetController,
    emitter: RunEventEmitter,
    registry: SkillRegistry,
):
    supervisor_fn = functools.partial(supervisor_node, adapter=adapter, emitter=emitter)
    budget_fn = functools.partial(budget_gate_node, budget=budget, emitter=emitter)
    worker_fn = functools.partial(worker_node, adapter=adapter, emitter=emitter, registry=registry)
    evaluate_fn = functools.partial(evaluate_result_node, emitter=emitter)
    finalize_fn = functools.partial(finalize_node, emitter=emitter)

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
```

- [ ] **Step 4: Criar api/deps.py com singleton do registry**

`apps/server/api/deps.py`:
```python
from pathlib import Path

from skills.registry import SkillRegistry

_skills_dir = Path(__file__).parent.parent / "skills"
registry = SkillRegistry.autodiscover(_skills_dir)
```

- [ ] **Step 5: Atualizar api/routes/runs.py para usar registry e skill_cache no initial_state**

Conteúdo completo de `apps/server/api/routes/runs.py`:
```python
import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse
from supabase import create_client

from agents.graph import build_graph
from agents.state import AgentState
from api.deps import registry
from api.middleware.auth import get_current_user
from api.middleware.rate_limit import limiter
from core.budget import BudgetController
from core.config import settings
from core.events import emitter
from core.llm_adapter import GeminiAdapter
from core.security import InjectionDetected, check_prompt

router = APIRouter(tags=["runs"])


class RunRequest(BaseModel):
    objective: str = Field(..., min_length=10, max_length=500)


@router.post("/runs", status_code=202)
@limiter.limit("5/minute")
async def create_run(
    request: Request,
    body: RunRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    try:
        check_prompt(body.objective)
    except InjectionDetected:
        raise HTTPException(status_code=400, detail="Prompt injection detectado")

    run_id = str(uuid.uuid4())

    supabase = create_client(settings.supabase_url, settings.supabase_service_key)
    supabase.table("runs").insert(
        {"id": run_id, "user_id": user["sub"], "objective": body.objective, "status": "running"}
    ).execute()

    emitter.create(run_id)

    initial_state: AgentState = {
        "run_id": run_id,
        "objective": body.objective,
        "tasks": [],
        "current_task_index": 0,
        "status": "running",
        "error": "",
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "skill_cache": {},
    }

    adapter = GeminiAdapter(api_key=settings.gemini_api_key)
    budget = BudgetController(limit_tokens=settings.default_budget_limit)
    graph = build_graph(adapter=adapter, budget=budget, emitter=emitter, registry=registry)

    asyncio.create_task(graph.ainvoke(initial_state))

    return {"run_id": run_id}


@router.get("/runs/{run_id}/stream")
async def stream_run(
    run_id: str,
    user: dict = Depends(get_current_user),
) -> EventSourceResponse:
    async def event_generator():
        async for event in emitter.listen(run_id):
            yield {"event": event.type.value, "data": event.model_dump_json()}

    return EventSourceResponse(event_generator())
```

- [ ] **Step 6: Executar testes de integração**

```bash
cd .worktrees/fase-3/apps/server && pytest tests/integration/test_graph.py -v
```

Expected: `2 passed`

- [ ] **Step 7: Executar toda a suíte**

```bash
cd .worktrees/fase-3/apps/server && pytest -v
```

Expected: todos os testes passam, sem regressões.

- [ ] **Step 8: Commit**

```bash
git add apps/server/agents/graph.py apps/server/api/deps.py apps/server/api/routes/runs.py apps/server/tests/integration/test_graph.py
git commit -m "feat: integra SkillRegistry ao build_graph e ao endpoint POST /runs"
```

---

## Task 10: GET /api/v1/skills — endpoint de listagem de skills

**Files:**
- Create: `apps/server/api/routes/skills.py`
- Modify: `apps/server/api/main.py`
- Create: `apps/server/tests/integration/test_skills_api.py`

- [ ] **Step 1: Escrever o teste de integração (falha esperada)**

`apps/server/tests/integration/test_skills_api.py`:
```python
import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.middleware.auth import get_current_user


@pytest.fixture
def client_autenticado():
    app.dependency_overrides[get_current_user] = lambda: {"sub": "user-123"}
    client = TestClient(app)
    yield client
    app.dependency_overrides = {}


def test_get_skills_retorna_lista(client_autenticado):
    response = client_autenticado.get("/api/v1/skills")
    assert response.status_code == 200
    skills = response.json()
    assert isinstance(skills, list)
    assert len(skills) >= 4  # time_manager, web_search, code_interpreter, file_writer

    names = [s["name"] for s in skills]
    assert "time_manager" in names
    assert "web_search" in names
    assert "code_interpreter" in names
    assert "file_writer" in names


def test_get_skills_estrutura_correta(client_autenticado):
    response = client_autenticado.get("/api/v1/skills")
    skills = response.json()
    for skill in skills:
        assert "name" in skill
        assert "description" in skill
        assert "parameters_schema" in skill
        assert "requires_approval" in skill


def test_get_skills_exige_autenticacao():
    client = TestClient(app)
    response = client.get("/api/v1/skills")
    assert response.status_code == 401


def test_skills_requires_approval_correto(client_autenticado):
    response = client_autenticado.get("/api/v1/skills")
    skills = {s["name"]: s for s in response.json()}
    assert skills["time_manager"]["requires_approval"] is False
    assert skills["web_search"]["requires_approval"] is False
    assert skills["code_interpreter"]["requires_approval"] is True
    assert skills["file_writer"]["requires_approval"] is True
```

- [ ] **Step 2: Executar e confirmar falha**

```bash
cd .worktrees/fase-3/apps/server && pytest tests/integration/test_skills_api.py -v
```

Expected: `404 Not Found` — endpoint não existe.

- [ ] **Step 3: Criar api/routes/skills.py**

`apps/server/api/routes/skills.py`:
```python
from fastapi import APIRouter, Depends

from api.deps import registry
from api.middleware.auth import get_current_user

router = APIRouter(tags=["skills"])


@router.get("/skills")
async def list_skills(
    user: dict = Depends(get_current_user),
) -> list[dict]:
    return [m.model_dump() for m in registry.list_all()]
```

- [ ] **Step 4: Registrar o skills router em api/main.py**

Conteúdo final de `apps/server/api/main.py`:
```python
from fastapi import FastAPI

from api.middleware.cors import add_cors_middleware
from api.middleware.rate_limit import add_rate_limit_middleware
from api.routes import health, runs, skills
from core.config import settings
from core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging(settings.log_level)

    app = FastAPI(title="Aether OS API", version="1.0.0")
    add_cors_middleware(app)
    add_rate_limit_middleware(app)
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(runs.router, prefix="/api/v1")
    app.include_router(skills.router, prefix="/api/v1")

    return app


app = create_app()
```

- [ ] **Step 5: Executar testes do skills endpoint**

```bash
cd .worktrees/fase-3/apps/server && pytest tests/integration/test_skills_api.py -v
```

Expected: `4 passed`

- [ ] **Step 6: Executar toda a suíte final**

```bash
cd .worktrees/fase-3/apps/server && pytest -v --tb=short
```

Expected: todos os testes passam.

- [ ] **Step 7: Commit**

```bash
git add apps/server/api/routes/skills.py apps/server/api/main.py apps/server/tests/integration/test_skills_api.py
git commit -m "feat: adiciona GET /api/v1/skills com autodiscovery"
```

---

## Task 11: Smoke test final e merge

**Files:**
- Merge `feat/fase-3-skill-system` → `master`

- [ ] **Step 1: Executar toda a suíte de testes**

```bash
cd .worktrees/fase-3/apps/server && pytest -v --tb=short
```

Expected: todos os testes passam, sem warnings relevantes.

- [ ] **Step 2: Iniciar servidor em modo dev**

```bash
cd .worktrees/fase-3/apps/server && uvicorn api.main:app --reload --port 8000
```

Expected: `Application startup complete.`

- [ ] **Step 3: Smoke test — listar skills sem auth (deve rejeitar)**

```bash
curl -s http://localhost:8000/api/v1/skills | python -m json.tool
```

Expected: `{"detail": "Authorization header missing"}` com status 401.

- [ ] **Step 4: Smoke test — health check**

```bash
curl -s http://localhost:8000/api/v1/health | python -m json.tool
```

Expected: `{"status": "ok"}`

- [ ] **Step 5: Confirmar working tree limpa**

```bash
git status
```

Expected: `nothing to commit, working tree clean`

- [ ] **Step 6: Merge para master**

```bash
git checkout master
git merge --no-ff feat/fase-3-skill-system -m "feat: Fase 3 — Skill System (Registry + 4 skills + worker refatorado)"
```

- [ ] **Step 7: Remover worktree**

```bash
git worktree remove .worktrees/fase-3
```

---

## Critério de sucesso

Endpoint `GET /api/v1/skills` lista as 4 skills com metadados corretos (`requires_approval` correto por skill). Worker escolhe a skill via LLM em dois passos (seleção + parâmetros), verifica cache antes de executar, emite `hitl_required` para CodeInterpreter e FileWriter. Toda a suíte de testes passa sem regressões da Fase 2.
