<div align="center">
  <h1>🌌 Aether OS</h1>
  <p><strong>Um Sistema Operacional Cognitivo baseado em Agentes Colaborativos</strong></p>
</div>

<br />

<div align="center">
  <!-- Badges placeholders -->
  <img alt="Next.js" src="https://img.shields.io/badge/Next.js-15-black?style=flat-square&logo=next.js" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-Python-009688?style=flat-square&logo=fastapi" />
  <img alt="LangGraph" src="https://img.shields.io/badge/LangGraph-Agents-blue?style=flat-square" />
  <img alt="Supabase" src="https://img.shields.io/badge/Supabase-Auth/DB-3ECF8E?style=flat-square&logo=supabase" />
  <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-Ready-3178C6?style=flat-square&logo=typescript" />
</div>

<br />

## 📖 Sobre o Projeto

**Aether** é um sistema de Inteligência Artificial desenhado para lidar com objetivos complexos através de um orquestrador de múltiplos agentes. Quando o usuário define uma meta de alto nível, o Aether automaticamente instancia (*spawns*) uma rede de agentes especializados que colaboram, planejam, executam e validam tarefas de forma autônoma e orquestrada.

Ao invés de um simples chatbot, o Aether funciona como um verdadeiro "sistema operacional" de IA, com acesso a habilidades (Skills) dinâmicas e capacidade de processamento em background, comunicação via streaming em tempo real e interface otimista (Optimistic UI).

---

## ✨ Recursos Principais

- 🧠 **Orquestração Multi-Agente:** Utiliza **LangGraph** sob o capô para gerenciar o estado da execução e rotear o planejamento e ações entre diferentes sub-agentes (*Supervisor -> Worker -> Evaluate -> Finalize*).
- ⚡ **Streaming em Tempo Real:** Comunicação fluida entre os agentes e a interface utilizando *Server-Sent Events* (SSE). Acompanhe o raciocínio (*Think-Act-Observe-Decide*) de forma transparente e imediata.
- 🛠️ **Skill System Extensível:** Os agentes possuem acesso a um catálogo dinâmico (SkillRegistry) de habilidades reais:
  - 🌐 `WebSearch`: Pesquisas aprofundadas na internet utilizando a API do Tavily.
  - 💻 `CodeInterpreter`: Execução segura de código e scripts via ambientes de sandbox *E2B*.
  - 📁 `FileWriter`: Capacidade de persistir e manipular arquivos com integração ao Supabase Storage.
  - ⏳ `TimeManager`: Agendamento e gerenciamento temporal preciso com a biblioteca *Pendulum*.
- 🛡️ **Segurança e Guardrails:** Defesa contra Prompt Injection, controle de orçamento de tokens (*Budget Controller*), rate limiting rigoroso e controle de concorrência com travas (Locks) de eventos.
- 🎨 **Interface Moderna e Premium:** Construída com **Next.js 15**, **TailwindCSS 4** (Dark Theme por padrão), componentes dinâmicos (*BentoGrid*, *SpotlightCard*, *StatusBadge*) e renderização *Markdown* limpa através do `react-markdown` + `shiki` com segurança estrita.

---

## 🏗️ Arquitetura e Tecnologias

O repositório está estruturado como um monorepo (`pnpm workspace`) contendo o Frontend e o Backend:

### 🖥️ Frontend (`apps/web`)
- **Framework:** Next.js 15 (App Router)
- **Estilização:** Tailwind CSS v4, Componentes Radix UI / Framer Motion
- **Autenticação:** Supabase Auth (SSR Middleware com JWT via ES256 / JWKS)
- **Estado e Integração:** Hooks customizados, `EventSource` e cache inteligente

### ⚙️ Backend (`apps/server`)
- **API Server:** FastAPI (Python) estruturado e tipado
- **Engine Agentica:** LangGraph & LangChain (com adaptadores modulares como `GeminiAdapter`)
- **Persistência:** PostgreSQL (via Supabase REST)
- **Concorrência:** Asyncio (Event Emitters / Queues para streaming robusto)

---

## 🚀 Como Começar

### Pré-requisitos
- [Node.js](https://nodejs.org/en/) >= 20
- [pnpm](https://pnpm.io/) >= 8
- [Python](https://www.python.org/) >= 3.10
- Uma conta no [Supabase](https://supabase.com/) e provedores das APIs de LLM (ex: Google Gemini, Tavily, E2B)

### 1. Clonar o Repositório

```bash
git clone https://github.com/YgorStefan/aether.git
cd aether
```

### 2. Configurar Variáveis de Ambiente

O projeto requer a configuração das variáveis em ambos os ambientes (Backend e Frontend). 
Copie o arquivo de exemplo na raiz ou em cada projeto e adicione suas credenciais:

```bash
cp .env.example .env
```

*Nota: Você precisará gerar chaves para Supabase, Gemini API, E2B API, Tavily API, etc.*

### 3. Instalar Dependências

No diretório raiz (Monorepo), instale as dependências NPM:

```bash
pnpm install
```

Para o backend Python:
```bash
cd apps/server
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows
pip install -r requirements.txt
```

### 4. Executar Localmente

O Aether oferece suporte a `Docker Compose` para levantar rapidamente os serviços anexos. 

Para levantar ambos (Web e Servidor) no ambiente de desenvolvimento com o PNPM e Foreman/Turbo, utilize:

```bash
# Na raiz do projeto:
pnpm run dev
```

- **Frontend:** http://localhost:3000
- **Backend API Docs:** http://localhost:8000/docs
- **Healthcheck:** http://localhost:8000/health

---

## 👨‍💻 Contribuição

Contribuições são sempre bem-vindas! Se você deseja adicionar novas *Skills* ou aprimorar os *Prompts* base dos Agentes, siga o fluxo convencional de *fork* -> *feature branch* -> *Pull Request*.

## 📄 Licença

Este projeto é desenvolvido para uso publico e estudos avançados em Inteligência Artificial Agentica.

---

<div align="center">
  <p>Feito com ❤️ por Ygor Stefankowski da Silva. 🚀</p>
</div>
