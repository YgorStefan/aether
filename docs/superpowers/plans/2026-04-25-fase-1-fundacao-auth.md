# Fase 1 — Fundação & Auth — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Monorepo com Next.js 15 + FastAPI rodando em paralelo, design system dark premium implementado, auth completa via Supabase (email/password + GitHub OAuth), FastAPI validando JWT em toda rota protegida.

**Architecture:** Monorepo pnpm workspaces com `apps/web` (Next.js 15 App Router) e `apps/server` (FastAPI Python). Supabase gerencia Auth + PostgreSQL. FastAPI valida o JWT emitido pelo Supabase em toda requisição. Frontend usa `@supabase/ssr` para sessão segura em Server Components.

**Tech Stack:** Next.js 15, Tailwind CSS 4, TypeScript, Vitest, FastAPI, PyJWT, pydantic-settings, structlog, pytest, Supabase (`@supabase/ssr` + `supabase-py`), Docker Compose, pnpm

**Success criterion:** Usuário faz login, vê o dashboard vazio com Bento Grid, FastAPI retorna 401 em request sem JWT.

---

## File Map

```
aether/
  pnpm-workspace.yaml
  package.json                            # root — scripts dev/lint/test
  apps/
    web/                                  # Next.js 15 App Router
      app/
        globals.css                       # Tailwind 4 theme + CSS vars
        layout.tsx                        # root layout (Inter/Geist)
        page.tsx                          # landing pública (placeholder)
        (auth)/
          login/page.tsx                  # form login email/pw + GitHub OAuth
          signup/page.tsx                 # form signup email/pw
          callback/route.ts               # OAuth code exchange
        (app)/
          layout.tsx                      # layout autenticado (verifica sessão)
          dashboard/page.tsx              # Bento Grid skeleton
      components/
        ui/
          card.tsx                        # Card glassmorphism base
          spotlight-card.tsx              # Card com spotlight hover
          skeleton.tsx                    # Skeleton loading block
        bento/
          bento-grid.tsx                  # Grid layout responsivo
          bento-grid.test.tsx             # Vitest tests
      lib/
        supabase.ts                       # createBrowserClient
        supabase-server.ts                # createServerClient (Server Components)
      middleware.ts                       # proteção de rotas (app/*) + refresh session
      vitest.config.ts
      vitest.setup.ts
    server/                               # FastAPI Python
      requirements.txt
      requirements-dev.txt
      core/
        config.py                         # Settings via pydantic-settings
        logging.py                        # structlog setup
      api/
        main.py                           # FastAPI app factory
        routes/
          health.py                       # GET /health + /ready
        middleware/
          auth.py                         # JWT Supabase validation dependency
          cors.py                         # CORS config
      tests/
        conftest.py                       # pytest fixtures (TestClient)
        unit/
          test_health.py
          test_auth.py
  supabase/
    migrations/
      20260425000001_initial_schema.sql   # runs + run_events + memories + RLS
  docker-compose.yml
  .env.example
```

---

## Task 1: Monorepo Scaffold

**Files:**
- Create: `pnpm-workspace.yaml`
- Create: `package.json` (root)
- Create: `apps/web/` via `create-next-app`

- [ ] **Step 1: Verify pnpm is installed**

```bash
pnpm --version
```

Expected: `9.x.x` or later. If missing: `npm install -g pnpm`.

- [ ] **Step 2: Create pnpm workspace config**

```yaml
# pnpm-workspace.yaml
packages:
  - 'apps/*'
```

- [ ] **Step 3: Create root package.json**

```json
{
  "name": "aether-os",
  "private": true,
  "scripts": {
    "dev": "concurrently \"pnpm --filter web dev\" \"cd apps/server && uvicorn api.main:app --reload --port 8000\"",
    "build": "pnpm --filter web build",
    "lint": "pnpm --filter web lint",
    "test": "pnpm --filter web test && cd apps/server && pytest"
  },
  "devDependencies": {
    "concurrently": "^9.0.0"
  }
}
```

- [ ] **Step 4: Install root devDependencies**

```bash
pnpm install
```

Expected: `node_modules/.pnpm` created, no errors.

- [ ] **Step 5: Scaffold Next.js 15 app**

```bash
pnpm create next-app@latest apps/web --typescript --tailwind --eslint --app --no-src-dir --import-alias "@/*"
```

When prompted: accept all defaults (no turbopack prompt in 15, it's the default).

- [ ] **Step 6: Verify Next.js app runs**

```bash
pnpm --filter web dev
```

Expected: server starts on `http://localhost:3000`. Ctrl+C to stop.

- [ ] **Step 7: Add Vitest + Testing Library to web**

```bash
pnpm --filter web add -D vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

- [ ] **Step 8: Create `apps/web/vitest.config.ts`**

```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
    globals: true,
  },
  resolve: {
    alias: { '@': path.resolve(__dirname, '.') },
  },
})
```

- [ ] **Step 9: Create `apps/web/vitest.setup.ts`**

```typescript
import '@testing-library/jest-dom'
```

- [ ] **Step 10: Add test script to `apps/web/package.json`**

Open `apps/web/package.json` and add inside `"scripts"`:
```json
"test": "vitest run",
"test:watch": "vitest"
```

- [ ] **Step 11: Commit**

```bash
git add pnpm-workspace.yaml package.json pnpm-lock.yaml apps/web
git commit -m "feat: scaffold monorepo e Next.js 15 com Vitest"
```

---

## Task 2: FastAPI Project Structure

**Files:**
- Create: `apps/server/requirements.txt`
- Create: `apps/server/requirements-dev.txt`
- Create: `apps/server/core/config.py`
- Create: `apps/server/core/logging.py`
- Create: `apps/server/api/middleware/cors.py`
- Create: `apps/server/api/main.py`

- [ ] **Step 1: Create Python directory structure**

```bash
mkdir -p apps/server/core apps/server/api/routes apps/server/api/middleware apps/server/tests/unit
touch apps/server/__init__.py apps/server/core/__init__.py apps/server/api/__init__.py
touch apps/server/api/routes/__init__.py apps/server/api/middleware/__init__.py
touch apps/server/tests/__init__.py apps/server/tests/unit/__init__.py
```

- [ ] **Step 2: Create `apps/server/requirements.txt`**

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
pydantic==2.9.0
pydantic-settings==2.5.0
PyJWT==2.9.0
cryptography==43.0.0
structlog==24.4.0
httpx==0.27.0
supabase==2.9.0
```

- [ ] **Step 3: Create `apps/server/requirements-dev.txt`**

```
-r requirements.txt
pytest==8.3.0
pytest-asyncio==0.24.0
anyio==4.6.0
```

- [ ] **Step 4: Install Python dependencies**

```bash
cd apps/server && pip install -r requirements-dev.txt
```

Expected: all packages installed, no version conflicts.

- [ ] **Step 5: Create `apps/server/core/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_jwt_secret: str = ""

    frontend_url: str = "http://localhost:3000"
    default_budget_limit: int = 10000
    max_requests_per_minute: int = 20
    log_level: str = "INFO"


settings = Settings()
```

- [ ] **Step 6: Create `apps/server/core/logging.py`**

```python
import logging
import structlog


def configure_logging(log_level: str = "INFO") -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if log_level == "DEBUG" else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )
```

- [ ] **Step 7: Create `apps/server/api/middleware/cors.py`**

```python
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings


def add_cors_middleware(app) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

- [ ] **Step 8: Create `apps/server/api/main.py`**

```python
from fastapi import FastAPI
from core.config import settings
from core.logging import configure_logging
from api.middleware.cors import add_cors_middleware
from api.routes import health


def create_app() -> FastAPI:
    configure_logging(settings.log_level)

    app = FastAPI(title="Aether OS API", version="1.0.0")
    add_cors_middleware(app)
    app.include_router(health.router, prefix="/api/v1")

    return app


app = create_app()
```

- [ ] **Step 9: Verify FastAPI starts**

```bash
cd apps/server && uvicorn api.main:app --reload --port 8000
```

Expected: `Application startup complete.` on `http://localhost:8000`. Ctrl+C.

Note: health routes don't exist yet — that's Task 3.

- [ ] **Step 10: Commit**

```bash
git add apps/server
git commit -m "feat: scaffold FastAPI com config, logging e CORS"
```

---

## Task 3: FastAPI Health Endpoints (TDD)

**Files:**
- Create: `apps/server/tests/conftest.py`
- Create: `apps/server/tests/unit/test_health.py`
- Create: `apps/server/api/routes/health.py`

- [ ] **Step 1: Create `apps/server/tests/conftest.py`**

```python
import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
```

- [ ] **Step 2: Write failing tests for health endpoints**

```python
# apps/server/tests/unit/test_health.py


def test_health_returns_ok(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_ok(client):
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")
    assert "supabase" in data
```

- [ ] **Step 3: Run tests — verify they fail**

```bash
cd apps/server && python -m pytest tests/unit/test_health.py -v
```

Expected: `FAILED` — `404 Not Found` for `/api/v1/health`.

- [ ] **Step 4: Create `apps/server/api/routes/health.py`**

```python
import httpx
from fastapi import APIRouter
from core.config import settings

router = APIRouter(tags=["system"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/ready")
async def ready():
    supabase_ok = False
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get(f"{settings.supabase_url}/rest/v1/")
            supabase_ok = resp.status_code in (200, 404)
    except Exception:
        pass

    status = "ok" if supabase_ok else "degraded"
    return {"status": status, "supabase": supabase_ok}
```

- [ ] **Step 5: Run tests — verify they pass**

```bash
cd apps/server && python -m pytest tests/unit/test_health.py -v
```

Expected: `PASSED` for both tests (supabase will be False/degraded since no real URL in test env — that's fine, the test only checks `status in ("ok", "degraded")`).

- [ ] **Step 6: Commit**

```bash
git add apps/server/tests/conftest.py apps/server/tests/unit/test_health.py apps/server/api/routes/health.py
git commit -m "feat: endpoints /health e /ready com testes"
```

---

## Task 4: FastAPI JWT Auth Middleware (TDD)

**Files:**
- Create: `apps/server/tests/unit/test_auth.py`
- Create: `apps/server/api/middleware/auth.py`

- [ ] **Step 1: Write failing tests for JWT middleware**

```python
# apps/server/tests/unit/test_auth.py
import time
import jwt
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from api.middleware.auth import get_current_user

# A test app that uses the auth dependency
test_app = FastAPI()

@test_app.get("/protected")
async def protected_route(user=Depends(get_current_user)):
    return {"user_id": user["sub"]}


@pytest.fixture
def auth_client() -> TestClient:
    return TestClient(test_app)


def make_token(secret: str, sub: str = "user-123", exp_offset: int = 3600) -> str:
    payload = {
        "sub": sub,
        "aud": "authenticated",
        "exp": int(time.time()) + exp_offset,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def test_missing_token_returns_401(auth_client):
    response = auth_client.get("/protected")
    assert response.status_code == 401


def test_invalid_token_returns_401(auth_client):
    response = auth_client.get("/protected", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401


def test_expired_token_returns_401(auth_client):
    token = make_token(secret="test-secret", exp_offset=-10)
    response = auth_client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_valid_token_returns_200(auth_client, monkeypatch):
    secret = "test-secret"
    monkeypatch.setattr("api.middleware.auth.settings.supabase_jwt_secret", secret)
    token = make_token(secret=secret, sub="user-abc")
    response = auth_client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["user_id"] == "user-abc"
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd apps/server && python -m pytest tests/unit/test_auth.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — `auth.py` doesn't exist yet.

- [ ] **Step 3: Create `apps/server/api/middleware/auth.py`**

```python
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd apps/server && python -m pytest tests/unit/test_auth.py -v
```

Expected: all 4 tests `PASSED`.

- [ ] **Step 5: Run full test suite**

```bash
cd apps/server && python -m pytest tests/ -v
```

Expected: all 6 tests pass (2 health + 4 auth).

- [ ] **Step 6: Commit**

```bash
git add apps/server/api/middleware/auth.py apps/server/tests/unit/test_auth.py
git commit -m "feat: middleware JWT Supabase com testes"
```

---

## Task 5: Design System — Tailwind 4 Theme

**Files:**
- Modify: `apps/web/app/globals.css`
- Modify: `apps/web/app/layout.tsx`
- Modify: `apps/web/next.config.ts`

- [ ] **Step 1: Verify Tailwind 4 is installed**

```bash
cd apps/web && pnpm list tailwindcss
```

Expected: `tailwindcss 4.x.x`. If it shows `3.x.x`, upgrade:
```bash
pnpm add tailwindcss@^4 @tailwindcss/postcss@^4
```

- [ ] **Step 2: Install Inter + Geist via next/font**

```bash
cd apps/web && pnpm add geist
```

- [ ] **Step 3: Replace `apps/web/app/globals.css` with Tailwind 4 theme**

```css
@import "tailwindcss";

@theme {
  --color-background: #000000;
  --color-card: #0a0a0a;
  --color-card-border: #1f1f1f;
  --color-primary: #a855f7;
  --color-primary-blue: #3b82f6;
  --color-success: #22c55e;
  --color-warning: #fbbf24;
  --color-error: #ef4444;
  --color-text-primary: #e2e8f0;
  --color-text-secondary: #94a3b8;
  --color-text-muted: #64748b;

  --font-sans: var(--font-geist-sans), ui-sans-serif, system-ui, sans-serif;
  --font-mono: var(--font-geist-mono), ui-monospace, monospace;

  --radius-card: 0.75rem;
}

body {
  background-color: var(--color-background);
  color: var(--color-text-primary);
  font-family: var(--font-sans);
  -webkit-font-smoothing: antialiased;
}

* {
  border-color: var(--color-card-border);
}

::selection {
  background-color: color-mix(in srgb, var(--color-primary) 30%, transparent);
}
```

- [ ] **Step 4: Update `apps/web/app/layout.tsx` to apply Geist fonts**

```typescript
import type { Metadata } from 'next'
import { GeistSans } from 'geist/font/sans'
import { GeistMono } from 'geist/font/mono'
import './globals.css'

export const metadata: Metadata = {
  title: 'Aether OS',
  description: 'AI agent orchestrator',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body>{children}</body>
    </html>
  )
}
```

- [ ] **Step 5: Verify dev server renders dark background**

```bash
cd apps/web && pnpm dev
```

Open `http://localhost:3000`. Background should be `#000000`. Ctrl+C.

- [ ] **Step 6: Commit**

```bash
git add apps/web/app/globals.css apps/web/app/layout.tsx
git commit -m "feat: design system Tailwind 4 dark theme"
```

---

## Task 6: Base UI Components

**Files:**
- Create: `apps/web/components/ui/card.tsx`
- Create: `apps/web/components/ui/spotlight-card.tsx`
- Create: `apps/web/components/ui/skeleton.tsx`
- Create: `apps/web/components/bento/bento-grid.tsx`
- Create: `apps/web/components/bento/bento-grid.test.tsx`

- [ ] **Step 1: Write failing tests for BentoGrid**

```typescript
// apps/web/components/bento/bento-grid.test.tsx
import { render, screen } from '@testing-library/react'
import { BentoGrid, BentoItem } from './bento-grid'

test('renders children inside grid', () => {
  render(
    <BentoGrid>
      <BentoItem>
        <span>Test content</span>
      </BentoItem>
    </BentoGrid>
  )
  expect(screen.getByText('Test content')).toBeInTheDocument()
})

test('BentoItem default has no col-span modifier', () => {
  const { container } = render(<BentoItem>content</BentoItem>)
  expect(container.firstChild).not.toHaveClass('md:col-span-2')
  expect(container.firstChild).not.toHaveClass('md:col-span-3')
})

test('BentoItem colSpan=2 applies md:col-span-2', () => {
  const { container } = render(<BentoItem colSpan={2}>content</BentoItem>)
  expect(container.firstChild).toHaveClass('md:col-span-2')
})

test('BentoItem colSpan=3 applies md:col-span-3', () => {
  const { container } = render(<BentoItem colSpan={3}>content</BentoItem>)
  expect(container.firstChild).toHaveClass('md:col-span-3')
})
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd apps/web && pnpm test
```

Expected: `Cannot find module './bento-grid'` — component doesn't exist yet.

- [ ] **Step 3: Create `apps/web/components/bento/bento-grid.tsx`**

```typescript
interface BentoGridProps {
  children: React.ReactNode
  className?: string
}

interface BentoItemProps {
  children: React.ReactNode
  className?: string
  colSpan?: 1 | 2 | 3
}

export function BentoGrid({ children, className }: BentoGridProps) {
  return (
    <div className={`grid grid-cols-1 md:grid-cols-3 gap-4 ${className ?? ''}`}>
      {children}
    </div>
  )
}

export function BentoItem({ children, className, colSpan = 1 }: BentoItemProps) {
  const spanClass =
    colSpan === 3 ? 'md:col-span-3' : colSpan === 2 ? 'md:col-span-2' : ''
  return (
    <div className={`${spanClass} ${className ?? ''}`}>
      {children}
    </div>
  )
}
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd apps/web && pnpm test
```

Expected: 4 tests `PASSED`.

- [ ] **Step 5: Create `apps/web/components/ui/card.tsx`**

```typescript
interface CardProps {
  children: React.ReactNode
  className?: string
}

export function Card({ children, className }: CardProps) {
  return (
    <div
      className={`rounded-[var(--radius-card)] border border-[var(--color-card-border)] bg-[var(--color-card)] backdrop-blur-sm ${className ?? ''}`}
    >
      {children}
    </div>
  )
}
```

- [ ] **Step 6: Create `apps/web/components/ui/spotlight-card.tsx`**

```typescript
'use client'

import { useRef, useState } from 'react'

interface SpotlightCardProps {
  children: React.ReactNode
  className?: string
}

export function SpotlightCard({ children, className }: SpotlightCardProps) {
  const ref = useRef<HTMLDivElement>(null)
  const [pos, setPos] = useState({ x: 0, y: 0 })
  const [hovered, setHovered] = useState(false)

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!ref.current) return
    const rect = ref.current.getBoundingClientRect()
    setPos({ x: e.clientX - rect.left, y: e.clientY - rect.top })
  }

  return (
    <div
      ref={ref}
      className={`relative overflow-hidden rounded-[var(--radius-card)] border border-[var(--color-card-border)] bg-[var(--color-card)] backdrop-blur-sm ${className ?? ''}`}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {hovered && (
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0"
          style={{
            background: `radial-gradient(300px circle at ${pos.x}px ${pos.y}px, rgba(168,85,247,0.08), transparent 70%)`,
          }}
        />
      )}
      {children}
    </div>
  )
}
```

- [ ] **Step 7: Create `apps/web/components/ui/skeleton.tsx`**

```typescript
interface SkeletonProps {
  className?: string
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse rounded-md bg-[var(--color-card-border)] ${className ?? ''}`}
    />
  )
}
```

- [ ] **Step 8: Commit**

```bash
git add apps/web/components
git commit -m "feat: componentes base Card, SpotlightCard, Skeleton, BentoGrid"
```

---

## Task 7: Supabase Schema

**Files:**
- Create: `supabase/migrations/20260425000001_initial_schema.sql`

- [ ] **Step 1: Create migrations directory**

```bash
mkdir -p supabase/migrations
```

- [ ] **Step 2: Create `supabase/migrations/20260425000001_initial_schema.sql`**

```sql
-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Runs table
CREATE TABLE runs (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  objective   TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'CREATED'
    CHECK (status IN ('CREATED','RUNNING','PAUSED','COMPLETED','FAILED','CANCELLED')),
  total_tokens INT DEFAULT 0,
  cost_usd    DECIMAL(10,6) DEFAULT 0,
  result      TEXT,
  error       TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Run events table
CREATE TABLE run_events (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id      UUID REFERENCES runs(id) ON DELETE CASCADE,
  type        TEXT NOT NULL
    CHECK (type IN (
      'agent_started','skill_called','skill_result',
      'hitl_required','hitl_resolved',
      'budget_warning','run_completed','run_failed','run_cancelled'
    )),
  agent_name  TEXT,
  payload     JSONB,
  tokens_used INT DEFAULT 0,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Memories table (pgvector RAG)
CREATE TABLE memories (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  run_id      UUID REFERENCES runs(id) ON DELETE SET NULL,
  content     TEXT NOT NULL,
  embedding   vector(768),
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Vector similarity index
CREATE INDEX memories_embedding_idx ON memories
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- updated_at trigger for runs
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER runs_updated_at
  BEFORE UPDATE ON runs
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- RLS
ALTER TABLE runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE run_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE memories ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users own runs" ON runs
  FOR ALL USING (user_id = auth.uid());

CREATE POLICY "users own run_events via runs" ON run_events
  FOR ALL USING (
    run_id IN (SELECT id FROM runs WHERE user_id = auth.uid())
  );

CREATE POLICY "users own memories" ON memories
  FOR ALL USING (user_id = auth.uid());
```

- [ ] **Step 3: Apply migration in Supabase Dashboard**

1. Go to `https://supabase.com/dashboard` → seu projeto → SQL Editor
2. Paste the entire SQL content above
3. Click "Run"
4. Expected: all statements execute without errors

- [ ] **Step 4: Verify tables in Table Editor**

In the Supabase Dashboard → Table Editor, confirm:
- `runs` table with all columns visible
- `run_events` table with all columns visible
- `memories` table with `embedding` column of type `vector(768)`

- [ ] **Step 5: Commit migration file**

```bash
git add supabase/migrations/20260425000001_initial_schema.sql
git commit -m "feat: schema Supabase com runs, run_events, memories e RLS"
```

---

## Task 8: Auth — Supabase Clients + Next.js Middleware

**Files:**
- Install: `@supabase/ssr @supabase/supabase-js`
- Create: `apps/web/lib/supabase.ts`
- Create: `apps/web/lib/supabase-server.ts`
- Create: `apps/web/middleware.ts`

- [ ] **Step 1: Install Supabase SSR packages**

```bash
cd apps/web && pnpm add @supabase/ssr @supabase/supabase-js
```

- [ ] **Step 2: Add env vars to `apps/web/.env.local`**

Create `apps/web/.env.local` (not committed):
```
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

Fill in real values from Supabase Dashboard → Settings → API.

- [ ] **Step 3: Create `apps/web/lib/supabase.ts`** (browser client)

```typescript
import { createBrowserClient } from '@supabase/ssr'

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}
```

- [ ] **Step 4: Create `apps/web/lib/supabase-server.ts`** (Server Components client)

```typescript
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

export async function createClient() {
  const cookieStore = await cookies()
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) =>
            cookieStore.set(name, value, options)
          )
        },
      },
    }
  )
}
```

- [ ] **Step 5: Create `apps/web/middleware.ts`** (route protection + session refresh)

```typescript
import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

const APP_ROUTES = ['/dashboard', '/run', '/history']

export async function middleware(request: NextRequest) {
  let response = NextResponse.next({ request })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
          response = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) =>
            response.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  const { data: { user } } = await supabase.auth.getUser()

  const path = request.nextUrl.pathname
  const isAppRoute = APP_ROUTES.some((r) => path.startsWith(r))
  const isAuthRoute = path === '/login' || path === '/signup'

  if (!user && isAppRoute) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  if (user && isAuthRoute) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  return response
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon\\.ico|.*\\.(?:svg|png|jpg|gif|webp)$).*)'],
}
```

- [ ] **Step 6: Commit**

```bash
git add apps/web/lib/supabase.ts apps/web/lib/supabase-server.ts apps/web/middleware.ts
git commit -m "feat: Supabase SSR client e middleware de proteção de rotas"
```

---

## Task 9: Auth — Login, Signup e OAuth Callback Pages

**Files:**
- Create: `apps/web/app/(auth)/layout.tsx`
- Create: `apps/web/app/(auth)/login/page.tsx`
- Create: `apps/web/app/(auth)/signup/page.tsx`
- Create: `apps/web/app/(auth)/callback/route.ts`

- [ ] **Step 1: Create `apps/web/app/(auth)/layout.tsx`**

```typescript
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--color-background)] px-4">
      {children}
    </main>
  )
}
```

- [ ] **Step 2: Create `apps/web/app/(auth)/login/page.tsx`**

```typescript
'use client'

import { createClient } from '@/lib/supabase'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

export default function LoginPage() {
  const router = useRouter()
  const supabase = createClient()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) {
      setError(error.message)
      setLoading(false)
    } else {
      router.push('/dashboard')
      router.refresh()
    }
  }

  async function handleGitHub() {
    await supabase.auth.signInWithOAuth({
      provider: 'github',
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    })
  }

  return (
    <div className="w-full max-w-sm space-y-6">
      <div className="space-y-1 text-center">
        <h1 className="text-2xl font-semibold text-[var(--color-text-primary)]">Entrar</h1>
        <p className="text-sm text-[var(--color-text-muted)]">Acesse o Aether OS</p>
      </div>

      <form onSubmit={handleLogin} className="space-y-4">
        <div className="space-y-2">
          <label className="block text-sm text-[var(--color-text-secondary)]">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg border border-[var(--color-card-border)] bg-[var(--color-card)] px-3 py-2 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
            placeholder="seu@email.com"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-sm text-[var(--color-text-secondary)]">Senha</label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border border-[var(--color-card-border)] bg-[var(--color-card)] px-3 py-2 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
            placeholder="••••••••"
          />
        </div>

        {error && <p className="text-xs text-[var(--color-error)]">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {loading ? 'Entrando...' : 'Entrar'}
        </button>
      </form>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-[var(--color-card-border)]" />
        </div>
        <div className="relative flex justify-center text-xs text-[var(--color-text-muted)]">
          <span className="bg-[var(--color-background)] px-2">ou</span>
        </div>
      </div>

      <button
        onClick={handleGitHub}
        className="flex w-full items-center justify-center gap-2 rounded-lg border border-[var(--color-card-border)] bg-[var(--color-card)] px-4 py-2 text-sm text-[var(--color-text-primary)] transition-colors hover:border-[var(--color-primary)]"
      >
        <svg viewBox="0 0 24 24" className="h-4 w-4 fill-current" aria-hidden>
          <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
        </svg>
        Continuar com GitHub
      </button>

      <p className="text-center text-xs text-[var(--color-text-muted)]">
        Não tem conta?{' '}
        <Link href="/signup" className="text-[var(--color-primary)] hover:underline">
          Criar conta
        </Link>
      </p>
    </div>
  )
}
```

- [ ] **Step 3: Create `apps/web/app/(auth)/signup/page.tsx`**

```typescript
'use client'

import { createClient } from '@/lib/supabase'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

export default function SignupPage() {
  const router = useRouter()
  const supabase = createClient()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleSignup(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: { emailRedirectTo: `${window.location.origin}/auth/callback` },
    })
    if (error) {
      setError(error.message)
      setLoading(false)
    } else {
      setSuccess(true)
    }
  }

  if (success) {
    return (
      <div className="w-full max-w-sm space-y-4 text-center">
        <p className="text-[var(--color-success)] text-sm">
          Verifique seu email para confirmar a conta.
        </p>
        <Link href="/login" className="text-xs text-[var(--color-primary)] hover:underline">
          Ir para login
        </Link>
      </div>
    )
  }

  return (
    <div className="w-full max-w-sm space-y-6">
      <div className="space-y-1 text-center">
        <h1 className="text-2xl font-semibold text-[var(--color-text-primary)]">Criar conta</h1>
        <p className="text-sm text-[var(--color-text-muted)]">Junte-se ao Aether OS</p>
      </div>

      <form onSubmit={handleSignup} className="space-y-4">
        <div className="space-y-2">
          <label className="block text-sm text-[var(--color-text-secondary)]">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg border border-[var(--color-card-border)] bg-[var(--color-card)] px-3 py-2 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
            placeholder="seu@email.com"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-sm text-[var(--color-text-secondary)]">Senha</label>
          <input
            type="password"
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border border-[var(--color-card-border)] bg-[var(--color-card)] px-3 py-2 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
            placeholder="mínimo 6 caracteres"
          />
        </div>

        {error && <p className="text-xs text-[var(--color-error)]">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {loading ? 'Criando conta...' : 'Criar conta'}
        </button>
      </form>

      <p className="text-center text-xs text-[var(--color-text-muted)]">
        Já tem conta?{' '}
        <Link href="/login" className="text-[var(--color-primary)] hover:underline">
          Entrar
        </Link>
      </p>
    </div>
  )
}
```

- [ ] **Step 4: Create `apps/web/app/(auth)/callback/route.ts`**

```typescript
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const code = searchParams.get('code')
  const next = searchParams.get('next') ?? '/dashboard'

  if (!code) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  const cookieStore = await cookies()
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) =>
            cookieStore.set(name, value, options)
          )
        },
      },
    }
  )

  const { error } = await supabase.auth.exchangeCodeForSession(code)
  if (error) {
    return NextResponse.redirect(new URL('/login?error=auth', request.url))
  }

  return NextResponse.redirect(new URL(next, request.url))
}
```

- [ ] **Step 5: Verify login page renders**

```bash
cd apps/web && pnpm dev
```

Open `http://localhost:3000/login`. Expected: dark form with email/password fields + GitHub button. Ctrl+C.

- [ ] **Step 6: Commit**

```bash
git add apps/web/app/\(auth\)
git commit -m "feat: páginas de login, signup e callback OAuth"
```

---

## Task 10: Dashboard Layout + Docker Compose + .env.example

**Files:**
- Create: `apps/web/app/(app)/layout.tsx`
- Create: `apps/web/app/(app)/dashboard/page.tsx`
- Create: `apps/web/app/page.tsx`
- Create: `docker-compose.yml`
- Create: `.env.example`

- [ ] **Step 1: Create `apps/web/app/(app)/layout.tsx`** (verifica sessão server-side)

```typescript
import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase-server'

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    redirect('/login')
  }

  return (
    <div className="min-h-screen bg-[var(--color-background)]">
      <nav className="border-b border-[var(--color-card-border)] px-6 py-4 flex items-center justify-between">
        <span className="text-sm font-semibold text-[var(--color-text-primary)]">Aether OS</span>
        <span className="text-xs text-[var(--color-text-muted)]">{user.email}</span>
      </nav>
      <main className="p-6">{children}</main>
    </div>
  )
}
```

- [ ] **Step 2: Create `apps/web/app/(app)/dashboard/page.tsx`**

```typescript
import { BentoGrid, BentoItem } from '@/components/bento/bento-grid'
import { SpotlightCard } from '@/components/ui/spotlight-card'
import { Skeleton } from '@/components/ui/skeleton'

export default function DashboardPage() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <h1 className="text-xl font-semibold text-[var(--color-text-primary)]">Dashboard</h1>

      <BentoGrid>
        <BentoItem colSpan={2}>
          <SpotlightCard className="p-6 h-48">
            <p className="text-sm text-[var(--color-text-muted)] mb-3">Objetivo</p>
            <Skeleton className="h-10 w-full" />
            <Skeleton className="mt-2 h-4 w-3/4" />
          </SpotlightCard>
        </BentoItem>

        <BentoItem>
          <SpotlightCard className="p-6 h-48">
            <p className="text-sm text-[var(--color-text-muted)] mb-3">Agentes ativos</p>
            <Skeleton className="h-8 w-16" />
          </SpotlightCard>
        </BentoItem>

        <BentoItem>
          <SpotlightCard className="p-6 h-40">
            <p className="text-sm text-[var(--color-text-muted)] mb-3">Skills</p>
            <div className="space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
              <Skeleton className="h-4 w-4/6" />
            </div>
          </SpotlightCard>
        </BentoItem>

        <BentoItem colSpan={2}>
          <SpotlightCard className="p-6 h-40">
            <p className="text-sm text-[var(--color-text-muted)] mb-3">Runs recentes</p>
            <div className="space-y-2">
              <Skeleton className="h-8 w-full rounded-lg" />
              <Skeleton className="h-8 w-full rounded-lg" />
            </div>
          </SpotlightCard>
        </BentoItem>
      </BentoGrid>
    </div>
  )
}
```

- [ ] **Step 3: Update `apps/web/app/page.tsx`** (landing page placeholder)

```typescript
import Link from 'next/link'

export default function LandingPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-[var(--color-background)] px-4 text-center">
      <h1 className="text-4xl font-bold text-[var(--color-text-primary)] mb-4">
        Aether OS
      </h1>
      <p className="text-lg text-[var(--color-text-secondary)] mb-8 max-w-md">
        Orquestrador de agentes de IA. Defina um objetivo, assista os agentes colaborando em tempo real.
      </p>
      <Link
        href="/login"
        className="rounded-lg bg-[var(--color-primary)] px-6 py-3 text-sm font-medium text-white transition-opacity hover:opacity-90"
      >
        Começar
      </Link>
    </main>
  )
}
```

- [ ] **Step 4: Create `docker-compose.yml`**

```yaml
version: '3.9'

services:
  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    volumes:
      - ./apps/web:/app
      - /app/node_modules
      - /app/.next
    environment:
      - NEXT_PUBLIC_SUPABASE_URL=${NEXT_PUBLIC_SUPABASE_URL}
      - NEXT_PUBLIC_SUPABASE_ANON_KEY=${NEXT_PUBLIC_SUPABASE_ANON_KEY}
    depends_on:
      - server

  server:
    build:
      context: ./apps/server
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - ./apps/server:/app
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}
      - SUPABASE_JWT_SECRET=${SUPABASE_JWT_SECRET}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - TAVILY_API_KEY=${TAVILY_API_KEY}
      - E2B_API_KEY=${E2B_API_KEY}
      - LANGSMITH_API_KEY=${LANGSMITH_API_KEY}
      - LANGSMITH_PROJECT=${LANGSMITH_PROJECT:-aether-os}
      - FRONTEND_URL=${FRONTEND_URL:-http://localhost:3000}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
```

- [ ] **Step 5: Create `.env.example`**

```env
# ======================
# SUPABASE
# ======================
# Frontend (public — pode ser exposto)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Backend (privado — nunca commitado, nunca no frontend)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret

# ======================
# LLM
# ======================
GEMINI_API_KEY=your-gemini-key

# ======================
# SKILLS
# ======================
TAVILY_API_KEY=your-tavily-key
E2B_API_KEY=your-e2b-key

# ======================
# OBSERVABILIDADE
# ======================
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_PROJECT=aether-os

# ======================
# CONFIGURAÇÕES
# ======================
FRONTEND_URL=http://localhost:3000
DEFAULT_BUDGET_LIMIT=10000
MAX_REQUESTS_PER_MINUTE=20
LOG_LEVEL=INFO
```

- [ ] **Step 6: Add `.env.local` and `.env` to `.gitignore`**

Open `.gitignore` and ensure it contains:
```
.env
.env.local
.env*.local
apps/web/.env.local
apps/server/.env
```

- [ ] **Step 7: Run full frontend test suite**

```bash
cd apps/web && pnpm test
```

Expected: 4 BentoGrid tests pass.

- [ ] **Step 8: Run full Python test suite**

```bash
cd apps/server && python -m pytest tests/ -v
```

Expected: 6 tests pass (health + auth).

- [ ] **Step 9: Manual smoke test — full auth flow**

1. `pnpm --filter web dev` + `cd apps/server && uvicorn api.main:app --reload --port 8000`
2. Open `http://localhost:3000` — landing page visible
3. Click "Começar" → redirects to `/login`
4. Create account at `/signup` with real email
5. Confirm email → return to `/login`
6. Login → redirected to `/dashboard`
7. Dashboard shows Bento Grid with skeletons
8. Test FastAPI rejection: `curl -X GET http://localhost:8000/api/v1/runs` (returns 404 — route doesn't exist yet, but `/health` works: `curl http://localhost:8000/api/v1/health` returns `{"status":"ok"}`)
9. Test JWT rejection with a mock route: the unit tests already cover this

- [ ] **Step 10: Final commit**

```bash
git add apps/web/app docker-compose.yml .env.example .gitignore
git commit -m "feat: dashboard skeleton, landing page, Docker Compose e .env.example"
```

---

## Checklist de Entrega (Fase 1)

- [ ] `pnpm dev` inicia Next.js na :3000 e FastAPI na :8000
- [ ] `GET /api/v1/health` retorna `{"status":"ok"}`
- [ ] Request sem JWT para rota protegida retorna 401
- [ ] Signup de usuário novo funciona (email de confirmação enviado)
- [ ] Login com email/password redireciona para `/dashboard`
- [ ] Dashboard exibe Bento Grid com cards e skeletons
- [ ] Acesso a `/dashboard` sem sessão redireciona para `/login`
- [ ] Tabelas `runs`, `run_events`, `memories` existem no Supabase com RLS
- [ ] 10 testes passando (6 Python + 4 TypeScript)
- [ ] `.env.example` documenta todas as variáveis necessárias
