# Aether OS — Design Spec
**Data:** 2026-04-25  
**Status:** Aprovado  
**Autor:** Ygor Stefankowski

---

## 1. Visão Geral

Aether OS é um orquestrador de agentes de IA onde o usuário define um objetivo complexo em linguagem natural e o sistema faz o spawn de múltiplos agentes especializados que colaboram para atingir o resultado. É um projeto de portfólio que demonstra domínio sênior em AI engineering, arquitetura de sistemas e UI/UX premium.

**Core value:** O usuário escreve um objetivo, assiste em tempo real os agentes colaborando num grafo visual, e recebe o resultado com total transparência sobre o raciocínio tomado.

**Público-alvo do portfólio:** Tech leads e engenheiros sêniores avaliando capacidades. Devem ver decisões arquiteturais, não só código funcionando.

---

## 2. Stack de Tecnologias

| Camada | Tecnologia | Versão | Motivo da Escolha |
|--------|-----------|--------|-------------------|
| Frontend | Next.js (App Router) | 15 | SSR, streaming nativo, performance |
| Estilo | Tailwind CSS | 4 | Utility-first, design system consistente |
| Animações | Framer Motion + Magic UI | latest | Micro-interações, transições premium |
| Grafo | React Flow | latest | Visualização de DAGs, customizável |
| Agent Engine | LangGraph | latest | Estado rigoroso, ciclos condicionais, checkpointing |
| LLM padrão | Gemini 1.5 Flash | — | Free tier generoso, model-agnostic via adapter |
| Backend/API | FastAPI | latest | Async-native, streaming SSE, Pydantic integrado |
| Auth + Banco | Supabase | — | Auth, PostgreSQL, pgvector e Realtime num único serviço free-tier |
| Code Sandbox | E2B | — | Execução segura e isolada de Python |
| Observabilidade | LangSmith | — | Traces de IA, custo e latência por run |
| Monorepo | — | — | `/apps/web` (Next.js) + `/apps/server` (FastAPI) |

### Decisões Arquiteturais Documentadas

**LangGraph vs CrewAI:**  
LangGraph expõe o estado da máquina de forma explícita e permite controle total sobre ciclos condicionais, checkpointing e fluxo de nós. CrewAI é um wrapper de alto nível que abstrai demais — para um portfólio sênior, controle visível é mais valioso que conveniência.

**Supabase vs Laravel + banco próprio:**  
Laravel adicionaria um terceiro serviço (Python + PHP + Node) sem agregar valor ao que o portfólio precisa comunicar. Supabase entrega auth, PostgreSQL, pgvector, RLS e Realtime num único serviço gerenciado, cabe inteiramente no free-tier e permite focar a complexidade onde ela importa: o engine de agentes.

**FastAPI vs Django/Flask:**  
Async-native, auto-docs via OpenAPI, tipagem forte com Pydantic, e suporte nativo a streaming SSE. Melhor fit para respostas de IA em tempo real.

**SSE vs WebSocket vs Background Jobs:**  
Runs duram até ~2 minutos. SSE direto no FastAPI é suficiente — unidirecional (servidor → cliente), simples de implementar, sem infraestrutura extra (sem Celery, sem Redis). WebSocket seria necessário para comunicação bidirecional em tempo real, mas o HITL é resolvido com um endpoint REST separado (`POST /runs/{id}/approve`).

**Gemini Flash vs GPT-4:**  
Free tier com limites generosos. A arquitetura usa um `BaseLLMAdapter` — trocar para outro modelo é instanciar outro adapter sem tocar no engine.

**E2B vs Docker próprio:**  
E2B entrega isolamento seguro de execução Python com free tier, sem necessidade de gerenciar containers. Docker próprio é v2.

---

## 3. Estrutura do Monorepo

```
/aether-os
  /apps
    /web                        # Next.js 15 App Router
      /app
        /(auth)
          /login
          /signup
        /(app)
          /dashboard             # Bento Grid principal
          /run/[id]              # Run detail com Graph View
          /history               # Lista de runs passados
        /page.tsx                # Landing page pública
      /components
        /ui                      # Shadcn/UI base components
        /bento                   # Bento Grid blocks
        /chat                    # Chat input + message list
        /graph                   # React Flow custom nodes/edges
        /hitl                    # HITL approval dialog
        /run                     # Run card, run detail, token display
        /skills                  # Skills catalog
      /hooks
        /use-run-stream.ts       # SSE consumer hook
        /use-run.ts              # Run data + status
      /lib
        /supabase.ts             # Supabase client (browser)
        /supabase-server.ts      # Supabase client (server components)
        /api.ts                  # FastAPI client helpers
      /public
        /manifest.json           # PWA manifest
    /server                      # FastAPI Python
      /agents
        /state.py                # AgentState Pydantic model
        /supervisor.py           # Supervisor node (LangGraph)
        /worker.py               # Worker node (Think→Act→Observe→Decide)
        /graph.py                # LangGraph graph builder + compilation
        /reflector.py            # Self-correction node
      /skills
        /base.py                 # Skill ABC (base class)
        /registry.py             # SkillRegistry + autodiscovery
        /web_search.py           # WebSearch (Tavily)
        /code_interpreter.py     # CodeInterpreter (E2B)
        /time_manager.py         # TimeManager (local logic)
        /file_writer.py          # FileWriter (Supabase Storage)
      /core
        /llm_adapter.py          # BaseLLMAdapter + GeminiAdapter
        /budget.py               # BudgetController
        /events.py               # RunEvent types + emitter
        /security.py             # Prompt injection guard
        /config.py               # Settings via pydantic-settings
        /logging.py              # structlog configuration
      /api
        /routes
          /runs.py               # CRUD + SSE + approve/cancel
          /skills.py             # GET /skills (autodiscovery)
          /health.py             # GET /health + /ready
        /middleware
          /auth.py               # JWT Supabase validation
          /rate_limit.py         # Rate limiting por usuário
          /cors.py               # CORS configuration
        /main.py                 # FastAPI app factory
      /tests
        /unit/                   # Skill Registry, Skills, Budget, Adapter
        /integration/            # LangGraph com LLM mockado
  /packages
    /config                      # Shared ESLint + TypeScript configs
  docker-compose.yml             # Dev environment local
  .env.example                   # Template de variáveis de ambiente
  README.md                      # README premium (detalhado na Seção 11)
```

---

## 4. Arquitetura do Sistema

### Três Camadas com Fronteiras Bem Definidas

```
[FRONTEND — Next.js]
  ↕ Supabase Auth (JWT)
  ↕ REST + SSE → FastAPI

[BACKEND — FastAPI]
  ↕ Supabase (PostgreSQL via supabase-py)
  ↕ LLM (Gemini via adapter)
  ↕ Skills externas (Tavily, E2B)
  ↕ LangSmith (traces)

[DATA — Supabase]
  PostgreSQL + pgvector + Auth + RLS
```

**Princípio:** A UI não conhece o banco. O FastAPI não usa o Supabase Client de browser. Os agentes não conhecem HTTP. Cada camada é testável e substituível de forma independente.

### Fluxo Completo de um Run

1. Usuário submete objetivo no chat → `POST /api/v1/runs` (com JWT no header)
2. FastAPI valida JWT Supabase → cria registro `runs` no banco → retorna `run_id`
3. Frontend abre conexão SSE em `GET /api/v1/runs/{id}/stream`
4. FastAPI inicia o LangGraph graph em background (async task)
5. A cada evento do grafo, FastAPI escreve na tabela `run_events` e emite via SSE
6. Frontend recebe eventos SSE e atualiza React Flow + logs em tempo real
7. Se `hitl_required`: frontend exibe HITL dialog → usuário aprova/rejeita → `POST /api/v1/runs/{id}/approve`
8. LangGraph resume ou pula a ação
9. Run completa → evento `run_completed` → SSE fecha → UI mostra resultado final

---

## 5. Agent Engine (LangGraph)

### Padrão: Supervisor + Worker Pool

```
Objetivo → [Supervisor] → [Worker A] → [Worker B] → [Worker C] → Resultado
                ↑_____________feedback__________________|
```

### AgentState (estado compartilhado tipado com Pydantic)

```python
class AgentState(TypedDict):
    run_id: str
    objective: str
    tasks: list[Task]           # sub-tasks geradas pelo Supervisor
    current_task_index: int
    observations: list[str]     # resultados acumulados dos Workers
    messages: list[BaseMessage] # histórico de mensagens LLM
    hitl_pending: bool          # True quando aguardando aprovação humana
    hitl_action: str | None     # ação que aguarda aprovação
    budget_used: int            # tokens consumidos até agora
    budget_limit: int           # limite configurado para o run
    skill_cache: dict           # cache de resultados de skills (key: "skill_name:params_hash")
    result: str | None          # resultado final
    error: str | None
```

### Nós do Grafo

**`supervisor_node`**
- Recebe o objetivo
- Chama LLM com prompt estruturado para decompor em lista de `Task` (Pydantic)
- Se o LLM retornar JSON inválido → retry até 3x com prompt corrigido
- Coloca tasks no estado e decide qual Worker usar para cada uma
- Após cada Worker completar → avalia resultado via `evaluate_result_node`

**`worker_node` (ciclo Think → Act → Observe → Decide)**
- **Think:** LLM recebe a task + lista de skills disponíveis (nome + descrição) → decide qual skill usar e com quais parâmetros (retorno Pydantic validado)
- **Act:** Se `skill.requires_approval` → emite evento `hitl_required` + pausa o grafo. Senão → executa a skill
- **Observe:** Resultado da skill é adicionado ao `observations` no estado
- **Decide:** LLM avalia se a task está completa ou precisa de mais passos (máximo de iterações configurável)

**`evaluate_result_node`**
- Supervisor avalia o output do Worker
- Se insatisfatório → re-delega com prompt de correção (máximo 2 re-tentativas)
- Se satisfatório → avança para próxima task

**`budget_gate_node`**
- Executado antes de toda chamada ao LLM
- Verifica `budget_used < budget_limit`
- Se excedido → emite evento `budget_exceeded` + encerra grafo com erro descritivo

**`finalize_node`**
- Agrega todos os `observations`
- Chama LLM para síntese final
- Salva embedding do resultado no pgvector (memória de longo prazo)
- Emite evento `run_completed`

### Adições Sênior no Engine

**Structured Output com Pydantic em todo nó:**  
Toda resposta do LLM é parseada para um modelo Pydantic antes de entrar no estado. Se o parsing falhar → retry automático com prompt corrigido (até 3x). Sem falhas silenciosas.

**Run Lifecycle com eventos tipados:**  
Estados: `CREATED → RUNNING → PAUSED → COMPLETED / FAILED / CANCELLED`  
Cada transição persiste no banco (`run_events`) e é emitida via SSE. Se o usuário fechar o browser e voltar, o estado é recuperado do banco.

**Skill Result Cache no estado do run:**  
Se o Supervisor delegar a mesma skill com os mesmos parâmetros duas vezes no mesmo run, o resultado é servido do cache em `AgentState.skill_cache`. Reduz custo e latência.

**Prompt Injection Guard:**  
O objetivo passa por um validador antes de entrar no LangGraph. Detecta padrões conhecidos de prompt injection (regex + classificação rápida com LLM). Rejeita com HTTP 400 antes de spawnar qualquer agente.

### LLM Adapter (model-agnostic)

```python
class BaseLLMAdapter(ABC):
    @abstractmethod
    async def complete(self, messages: list, response_model: type[BaseModel]) -> BaseModel: ...
    
    @abstractmethod
    async def embed(self, text: str) -> list[float]: ...

class GeminiAdapter(BaseLLMAdapter):
    # Implementação com google-generativeai
    # Retorna structured output via Pydantic
    # Registra tokens usados no BudgetController
```

### BudgetController

Wrapper singleton injetado em todos os nós. Conta tokens em cada chamada ao LLM adapter. Se `total_tokens >= limit` → lança `BudgetExceededException` que o grafo captura e converte em evento SSE + status `FAILED`.

Custo estimado em USD calculado com base em preço/token do modelo ativo.

---

## 6. Skill Registry

### Base Class

```python
class Skill(ABC):
    name: str                        # identificador único (snake_case)
    description: str                 # usado pelo LLM para decidir qual skill usar
    parameters: type[BaseModel]      # Pydantic schema dos inputs
    requires_approval: bool = False  # se True, Worker emite HITL antes de executar

    @abstractmethod
    async def execute(self, params: BaseModel) -> SkillResult: ...

class SkillResult(BaseModel):
    success: bool
    output: str          # resultado em texto (vai para observations)
    metadata: dict = {}  # dados extras (ex: URLs encontradas)
    error: str | None = None
```

### SkillRegistry

```python
class SkillRegistry:
    _skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None: ...
    def get(self, name: str) -> Skill: ...
    def list_all(self) -> list[SkillMetadata]: ...  # para o endpoint /skills e para o prompt do Worker
    
    @classmethod
    def autodiscover(cls, skills_dir: Path) -> "SkillRegistry":
        # Escaneia skills_dir, importa qualquer classe que herde de Skill, registra automaticamente
        # Adicionar nova skill = criar o arquivo + reiniciar o servidor
```

### Skills v1

**`WebSearch`**
- API: Tavily Search API (free tier)
- Input: `query: str, max_results: int = 5`
- Output: lista de resultados sumarizados pelo LLM
- `requires_approval: False`

**`CodeInterpreter`**
- API: E2B Sandbox
- Input: `code: str, language: str = "python"`
- Output: stdout + stderr da execução
- `requires_approval: True` — toda execução de código pede aprovação humana
- Timeout: 30s por execução

**`TimeManager`**
- API: Nenhuma (lógica local com `pendulum`)
- Input: `query: str` (ex: "quantos dias até sexta?", "que horas são em Tokyo?")
- Output: resposta calculada
- `requires_approval: False`

**`FileWriter`**
- API: Supabase Storage
- Input: `filename: str, content: str, format: Literal["md", "pdf", "txt"]`
- Output: URL pública do arquivo salvo
- `requires_approval: True`

**`MemoryRecall`** *(adicionada na Fase 7)*
- API: Supabase pgvector
- Input: `query: str, top_k: int = 5`
- Output: trechos de memória relevantes de runs anteriores
- `requires_approval: False`
- Usada pelo Supervisor no início de cada run para contextualizar com conhecimento prévio

### Skills v2 (roadmap)

**`GitHubPR`**
- API: GitHub REST API
- Acessa repositório → lê código → identifica bug via análise estática + LLM → abre Pull Request
- `requires_approval: True`

---

## 7. Frontend — Páginas e Componentes

### Páginas

**`/` — Landing Page (pública)**
- Demonstra o que o sistema faz sem precisar de login
- Hero section com animação do React Flow mostrando agentes colaborando
- Seção de skills disponíveis
- CTA para login/signup
- Importante: é o primeiro impacto para avaliadores do portfólio

**`/login` e `/signup` — Auth**
- Supabase Auth UI ou formulário customizado com estilo dark
- GitHub OAuth + email/password
- Redirect para `/dashboard` após auth

**`/dashboard` — Bento Grid Principal**
- Layout A: Chat/input ocupa espaço principal (60%), sidebar com status + skills + runs recentes
- Bento Grid colapsa em coluna única no mobile (≤768px)
- Blocos:
  - Input de objetivo (grande, destaque)
  - Status dos agentes ativos
  - Catálogo de skills (gerado dinamicamente via `GET /api/v1/skills`)
  - Runs recentes (últimos 5)

**`/run/[id]` — Run Detail (hero visual do portfólio)**
- Top bar: objetivo truncado, status badge (animado), agente count, tokens usados, custo estimado
- Painel esquerdo (60%): React Flow com grafo de agentes
  - Custom nodes por tipo (Supervisor roxo, Workers azul/verde/etc., nó inativo cinza)
  - Nó ativo tem glow animado + pulso
  - Arestas animadas mostrando direção do fluxo de dados
- Painel direito (40%): trace em tempo real (logs tipados por agente) + HITL dialog inline quando agente pausa
- Bottom bar: budget progress bar, link LangSmith, skills ativas no run
- Mobile: Graph View colapsável (toggle), logs em fullscreen

**`/history` — Histórico de Runs**
- Lista de todos os runs do usuário com status, objetivo truncado, custo, data
- Clica no run → vai para `/run/[id]`

### Componentes Importantes

**`RunStream` hook (`use-run-stream.ts`)**  
Consome SSE de `/api/v1/runs/{id}/stream`. Mantém reconexão automática com backoff exponencial. Emite eventos tipados que atualizam o React Flow e os logs simultaneamente.

**React Flow custom nodes**  
Cada tipo de agente tem seu próprio node component com cor e animação distintas. O estado do nó (idle, thinking, done, failed) controla o estilo via CSS variables.

**HITL Dialog**  
Aparece inline no painel de logs, não como modal — o agente está pausado, o grafo fica estático, o usuário vê exatamente qual ação está pendente de aprovação. Botões Aprovar / Rejeitar fazem `POST /api/v1/runs/{id}/approve`.

**Toast Notifications**  
Eventos de HITL, run completo e erros chegam como toasts (Sonner). No mobile é especialmente importante — o usuário pode ter saído do painel de logs.

### Adições Sênior no Frontend

**Skeleton Loading States:**  
Cada bloco do Bento Grid tem skeleton screens enquanto carrega. Sem spinners. Detalhe de polish que separa portfólios amadores de sêniores.

**Optimistic UI:**  
Run aparece como `PENDING` imediatamente ao submeter, antes do servidor confirmar. A UI não trava.

**Error Boundaries:**  
React error boundaries em torno do Graph View e do Chat. Se o React Flow travar, o resto da página continua funcionando.

**Keyboard Shortcuts:**  
`Cmd/Ctrl + Enter` para submeter objetivo, `Esc` para cancelar run.

**PWA:**  
`manifest.json` + ícones para "adicionar à tela inicial" no mobile. Sem service worker complexo.

### Design System

```
Background:        #000000
Cards:             #0a0a0a
Card borders:      1px solid #1f1f1f
Primary purple:    #a855f7 (Supervisor nodes, accents)
Primary blue:      #3b82f6 (Worker nodes, links)
Success green:     #22c55e (completed states)
Warning yellow:    #fbbf24 (HITL, budget warnings)
Error red:         #ef4444
Text primary:      #e2e8f0
Text secondary:    #94a3b8
Text muted:        #64748b
Typography:        Inter ou Geist Sans
```

**Efeitos:**
- Glassmorphism sutil em cards com `backdrop-blur`
- Gradiente radial em glow atrás de componentes ativos
- Spotlight effect no hover de cards (brilho segue o mouse)
- Framer Motion para transições de página e animações de estado

**Responsividade:**
- Desktop (≥1280px): layout completo com sidebar
- Tablet (768–1279px): sidebar colapsa em drawer
- Mobile (<768px): coluna única, Graph View colapsável, touch-friendly tap targets (≥44px)

---

## 8. Data Model (Supabase)

### Tabelas

```sql
-- Gerenciada pelo Supabase Auth
-- auth.users: id, email, created_at

-- Runs de agente
CREATE TABLE runs (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  objective   TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'CREATED',
    -- CREATED | RUNNING | PAUSED | COMPLETED | FAILED | CANCELLED
  total_tokens INT DEFAULT 0,
  cost_usd    DECIMAL(10,6) DEFAULT 0,
  result      TEXT,
  error       TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Eventos de cada run (fonte do SSE + trace viewer)
CREATE TABLE run_events (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id      UUID REFERENCES runs(id) ON DELETE CASCADE,
  type        TEXT NOT NULL,
    -- agent_started | skill_called | skill_result | hitl_required |
    -- hitl_resolved | budget_warning | run_completed | run_failed | run_cancelled
  agent_name  TEXT,            -- qual agente emitiu o evento
  payload     JSONB,           -- dados do evento (parâmetros, resultados, etc.)
  tokens_used INT DEFAULT 0,   -- tokens neste evento
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Memória de longo prazo (RAG)
CREATE TABLE memories (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  run_id      UUID REFERENCES runs(id) ON DELETE SET NULL,
  content     TEXT NOT NULL,      -- texto do insight/resultado
  embedding   vector(768),        -- embedding Gemini (768 dimensões)
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Índice para busca por similaridade
CREATE INDEX memories_embedding_idx ON memories
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
```

### Row Level Security (RLS)

```sql
-- Todas as tabelas têm RLS habilitado
ALTER TABLE runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE run_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE memories ENABLE ROW LEVEL SECURITY;

-- Policies: usuário só acessa seus próprios dados
CREATE POLICY "users own runs" ON runs
  FOR ALL USING (user_id = auth.uid());

CREATE POLICY "users own run_events via runs" ON run_events
  FOR ALL USING (
    run_id IN (SELECT id FROM runs WHERE user_id = auth.uid())
  );

CREATE POLICY "users own memories" ON memories
  FOR ALL USING (user_id = auth.uid());
```

---

## 9. API (FastAPI)

### Endpoints

```
# Autenticação
Todos os endpoints exceto /health e /ready requerem:
  Authorization: Bearer <supabase_jwt>

# Runs
POST   /api/v1/runs                → Inicia run. Body: {objective: str, budget_limit: int}
                                     Response: {run_id: uuid, status: "CREATED"}

GET    /api/v1/runs                → Lista runs do usuário autenticado (paginado)
                                     Query: ?page=1&limit=20&status=COMPLETED

GET    /api/v1/runs/{id}           → Detalhes do run + todos os eventos
                                     Response: Run + list[RunEvent]

GET    /api/v1/runs/{id}/stream    → SSE endpoint
                                     Emite: RunEvent objects como JSON lines
                                     Heartbeat: event: ping a cada 15s para manter conexão

POST   /api/v1/runs/{id}/approve   → Resolve HITL
                                     Body: {decision: "approve" | "reject"}

POST   /api/v1/runs/{id}/cancel    → Cancela run em andamento

# Skills
GET    /api/v1/skills              → Lista todas as skills registradas (autodiscovery)
                                     Response: [{name, description, parameters_schema, requires_approval}]

# Sistema
GET    /api/v1/health              → Liveness check. Response: {status: "ok"}
GET    /api/v1/ready               → Readiness check (verifica conexão Supabase + LLM). Response: {status: "ok"}
```

### Middleware Stack (ordem de execução)

1. **CORS** — permite apenas origem do frontend (configurável via env)
2. **Rate Limiting** — máximo de requests por usuário por minuto (configurável)
3. **JWT Auth** — valida token Supabase em todo request (exceto /health e /ready)
4. **Structured Logging** — toda request logada com structlog (método, path, user_id, duração, status)

### Variáveis de Ambiente (.env.example)

```env
# Supabase
SUPABASE_URL=
SUPABASE_SERVICE_KEY=        # chave de serviço (nunca exposta no frontend)
SUPABASE_JWT_SECRET=

# LLM
GEMINI_API_KEY=

# Skills
TAVILY_API_KEY=              # WebSearch
E2B_API_KEY=                 # CodeInterpreter sandbox

# Observabilidade
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=aether-os

# Configurações
FRONTEND_URL=http://localhost:3000
DEFAULT_BUDGET_LIMIT=10000   # tokens por run
MAX_REQUESTS_PER_MINUTE=20
LOG_LEVEL=INFO
```

---

## 10. Segurança

| Vetor | Mitigação |
|-------|-----------|
| Acesso não autorizado | JWT Supabase validado em todo request FastAPI |
| Dados entre usuários | RLS no Supabase: `user_id = auth.uid()` em todas as tabelas |
| Prompt injection | Guard antes de entrar no LangGraph (regex + classificação LLM) |
| Execução de código malicioso | CodeInterpreter usa E2B sandbox isolado, `requires_approval: True` |
| XSS | CSP headers no Next.js, sanitização de Markdown com DOMPurify |
| CSRF | Supabase Auth usa JWT stateless, sem cookies de sessão tradicionais |
| Secrets expostos | `.env` nunca commitado, `.env.example` documentado sem valores |
| Rate abuse | Rate limiting por usuário no middleware FastAPI |
| CORS abuse | CORS configurado para aceitar apenas a origem do frontend |
| DoS via runs infinitos | Budget Controller + timeout máximo por run |

---

## 11. Testes

### Estratégia por Camada

**Unit Tests (pytest)**
- `SkillRegistry`: registro, autodiscovery, listagem
- Cada Skill: inputs válidos, inputs inválidos, erro de API externa (mock)
- `BudgetController`: contagem de tokens, exceção ao exceder limite
- `GeminiAdapter`: com mock do cliente Gemini, verifica structured output e retry
- `PromptInjectionGuard`: casos conhecidos de injection

**Integration Tests (pytest + LangGraph)**
- Grafo completo com LLM mockado (retorna respostas Pydantic fixas)
- Verifica: decomposição de objetivo → tasks → execução de skills → resultado final
- Verifica: evento `hitl_required` emitido quando `requires_approval: True`
- Verifica: `BudgetExceededException` encerra o grafo corretamente
- Verifica: checkpointing — salva estado, restaura, continua execução

**E2E Tests (Playwright)**
- Login com email/password → redirect para dashboard
- Submete objetivo simples → aguarda run completar → verifica resultado
- HITL flow: submete objetivo com skill protegida → aprova → run completa
- Mobile viewport: layout responsivo no dashboard e run detail

**Regra:** Nunca testar o LangGraph contra o Gemini real em CI. O adapter mockado garante o contrato sem custo ou instabilidade de API externa.

---

## 12. README (Estrutura Premium)

O README é o documento mais importante do portfólio — é o primeiro (e às vezes único) documento que um avaliador lê.

```markdown
# Aether OS
[Badge de status do CI/CD]
[Badge de versão do Next.js]
[Badge de versão do Python]

> [hero GIF ou screenshot animado do Graph View com agentes em execução]

Aether OS é um orquestrador de agentes de IA onde você define um objetivo 
em linguagem natural e assiste em tempo real os agentes colaborando para entregá-lo.

## Demo
[Link para o deploy na Vercel]
[Screenshot do dashboard]
[Screenshot do run detail com Graph View]

## Por que essas tecnologias
A seção mais importante — explica decisões arquiteturais com raciocínio:

### LangGraph vs CrewAI
[Explica o tradeoff: controle vs conveniência]

### Supabase vs banco próprio
[Explica o tradeoff: foco no engine de IA vs infraestrutura]

### SSE vs WebSocket vs Background Jobs
[Explica por que SSE é suficiente para runs de até 2 minutos]

### E2B vs Docker próprio
[Explica o tradeoff: velocidade de ship vs controle]

## Arquitetura
[Diagrama ASCII ou imagem da arquitetura de 3 camadas]

## Stack Completo
[Tabela com tecnologia, versão, motivo — igual à Seção 2 deste spec]

## Funcionalidades
- Agentic Workflows com DAGs (LangGraph)
- Skill Registry com injeção de dependência (SOLID)
- Real-time Graph View (React Flow)
- Human-in-the-loop com approval dialog
- Budget Controller com token tracking
- Memória de longo prazo via RAG (pgvector)
- MCP Server (Model Context Protocol)

## Como Rodar Localmente
[Passo a passo detalhado com cada variável de ambiente]

## Roadmap
- v1: [link para as 7 fases]
- v2: GitHub PR Skill (agente que lê repo, identifica bug, abre PR)

## Aprendizados
[O que foi não-óbvio: gerenciar estado no LangGraph, HITL com SSE, 
React Flow com dados dinâmicos, etc.]
```

---

## 13. Fases de Desenvolvimento

### Fase 1 — Fundação & Auth
**Goal:** Monorepo rodando, design system implementado, auth funcionando

Entregáveis:
- [ ] Monorepo com Next.js 15 + FastAPI rodando em paralelo (`pnpm dev` + `uvicorn`)
- [ ] `docker-compose.yml` para desenvolvimento local
- [ ] Design system: dark theme (#000/#0a0a0a), Tailwind config, tipografia Inter/Geist
- [ ] Componentes base: Card com glassmorphism, Bento Grid responsivo, spotlight hover effect
- [ ] Supabase: projeto criado, tabelas `runs` + `run_events` + `memories` com RLS
- [ ] Auth completa: signup, login, logout, GitHub OAuth
- [ ] FastAPI: middleware JWT Supabase funcionando, endpoint `/health` e `/ready`
- [ ] `.env.example` documentado

Critério de sucesso: Usuário faz login, vê o dashboard vazio com Bento Grid, FastAPI rejeita request sem JWT.

### Fase 2 — Core Agent Engine
**Goal:** LangGraph executando o ciclo completo de agentes

Entregáveis:
- [ ] `AgentState` Pydantic model com todos os campos
- [ ] `supervisor_node`: decomposição de objetivo em tasks com structured output + retry
- [ ] `worker_node`: ciclo Think→Act→Observe→Decide com mock de skills
- [ ] `evaluate_result_node`: self-correction do Supervisor
- [ ] `budget_gate_node`: BudgetController integrado
- [ ] `finalize_node`: síntese final
- [ ] `GeminiAdapter`: structured output via Pydantic, contagem de tokens
- [ ] Eventos SSE tipados emitidos a cada transição de nó
- [ ] Endpoint `POST /api/v1/runs` inicia o grafo
- [ ] Endpoint `GET /api/v1/runs/{id}/stream` transmite eventos SSE com heartbeat
- [ ] Prompt injection guard operacional

Critério de sucesso: Submit de objetivo simples → Supervisor decompõe → Workers executam com skills mockadas → resultado retornado via SSE.

### Fase 3 — Skill System
**Goal:** Skill Registry com autodiscovery e 4 skills funcionando

Entregáveis:
- [ ] `Skill` ABC com `name`, `description`, `parameters`, `requires_approval`, `execute`
- [ ] `SkillRegistry` com `register`, `get`, `list_all`, `autodiscover`
- [ ] `WebSearch` skill (Tavily API)
- [ ] `CodeInterpreter` skill (E2B sandbox, `requires_approval: True`)
- [ ] `TimeManager` skill (lógica local com pendulum)
- [ ] `FileWriter` skill (Supabase Storage, `requires_approval: True`)
- [ ] Endpoint `GET /api/v1/skills` retornando skills descobertas automaticamente
- [ ] Skill result cache no `AgentState`
- [ ] Workers usam skills reais (não mock)

Critério de sucesso: Endpoint `/skills` lista as 4 skills. Worker escolhe e executa a skill correta para uma task real.

### Fase 4 — Frontend Integration
**Goal:** UI conectada ao engine — sistema utilizável de ponta a ponta

Entregáveis:
- [ ] `use-run-stream.ts` hook: SSE consumer com reconexão automática e backoff exponencial
- [ ] Dashboard (`/dashboard`): Bento Grid com input, skills catalog (dinâmico), runs recentes
- [ ] Chat input: submete objetivo → cria run → abre SSE stream
- [ ] Mensagens do agente renderizadas com Markdown + syntax highlighting (react-markdown + shiki)
- [ ] Run card component com status badge animado
- [ ] Página `/history` com lista de runs
- [ ] Skeleton loading em todos os blocos do Bento Grid
- [ ] Optimistic UI: run aparece como PENDING imediatamente
- [ ] Error boundaries em torno de Graph View e Chat
- [ ] Toast notifications para eventos importantes
- [ ] Keyboard shortcuts: Cmd+Enter para submeter, Esc para cancelar
- [ ] PWA: manifest.json + ícones
- [ ] Responsividade mobile testada (≤768px)

Critério de sucesso: Usuário autenticado submete objetivo no dashboard → vê resposta do agente em streaming → run aparece no histórico.

### Fase 5 — Graph View & HITL
**Goal:** Visualização do grafo de agentes em tempo real + aprovação humana

Entregáveis:
- [ ] React Flow instalado e configurado
- [ ] Custom nodes: `SupervisorNode`, `WorkerNode`, `SkillNode` com cores e estilos distintos
- [ ] Estado do nó (idle, thinking, done, failed) controla animação via CSS
- [ ] Nó ativo tem glow animado + pulso (Framer Motion)
- [ ] Arestas animadas mostrando direção do fluxo
- [ ] Página `/run/[id]` com layout: Graph View (60%) + logs + HITL panel (40%)
- [ ] SSE events mapeados para atualizações no React Flow graph
- [ ] HITL dialog inline no painel de logs (não modal)
- [ ] Endpoint `POST /api/v1/runs/{id}/approve` funcionando
- [ ] LangGraph pausa o grafo em `hitl_required` e aguarda resolução
- [ ] Mobile: Graph View colapsável com toggle

Critério de sucesso: Run com CodeInterpreter → grafo anima → agente pausa → dialog de aprovação → usuário aprova → grafo continua e finaliza.

### Fase 6 — Observabilidade & Budget
**Goal:** Token tracking, custo visível e Budget Controller

Entregáveis:
- [ ] Token count e custo estimado em USD atualizados em tempo real na top bar do `/run/[id]`
- [ ] Breakdown de tokens por agente visível nos detalhes do run
- [ ] Budget progress bar na bottom bar do run detail
- [ ] `BudgetController` interrompe execução quando limite é atingido (evento `budget_exceeded`)
- [ ] Toast de aviso quando 80% do budget é consumido
- [ ] Trace completo armazenado na tabela `run_events` e visualizável após conclusão
- [ ] Link para LangSmith trace na UI (quando `LANGSMITH_API_KEY` configurado)
- [ ] Health + readiness endpoints retornando status do LangSmith

Critério de sucesso: Run com budget baixo → aviso visual → execução interrompida ao atingir limite → UI mostra custo final.

### Fase 7 — Memória & MCP
**Goal:** Memória de longo prazo via RAG e MCP Server

Entregáveis:
- [ ] `finalize_node` salva embedding do resultado no pgvector após cada run
- [ ] Skill `MemoryRecall`: o Supervisor consulta memória relevante no início de cada run
- [ ] Query por similaridade cosine com threshold configurável
- [ ] MCP Server com FastMCP: skills expostas como ferramentas MCP-compatíveis
- [ ] Endpoint MCP seguindo a especificação do Model Context Protocol
- [ ] Documentação do MCP Server no README

Critério de sucesso: Segundo run sobre o mesmo tópico usa informações do run anterior. MCP Server responde corretamente a uma chamada de ferramenta MCP.

---

## 14. v2 — GitHub PR Skill (Roadmap)

Skill que demonstra autonomia real do agente:

1. Recebe URL de repositório GitHub + descrição do problema
2. Clona o repositório (ou usa GitHub Contents API)
3. Analisa o código via LLM para identificar o bug
4. Gera o patch de correção
5. Cria uma branch + commit + abre Pull Request via GitHub API
6. `requires_approval: True` — usuário revisa antes da PR ser aberta

Essa skill é o maior diferencial individual do portfólio — demonstra integração com API real, raciocínio sobre código e autonomia do agente end-to-end.

---

## 15. Deploy (Free Tier)

| Serviço | Plataforma | Plano |
|---------|-----------|-------|
| Frontend (Next.js) | Vercel | Hobby (grátis) |
| Backend (FastAPI) | Render ou Railway | Free / Trial |
| Banco + Auth | Supabase | Free (500MB) |
| LLM | Gemini API | Free tier |
| WebSearch | Tavily | Free tier |
| Code Sandbox | E2B | Free tier |
| Traces | LangSmith | Free tier |

**CI/CD:** GitHub Actions para lint + testes em cada PR. Deploy automático no merge para `main` (Vercel auto-detecta Next.js; Render/Railway pode ser configurado com webhook).
