"""Teste de carga do Aether OS (Locust).

Simula usuários concorrentes cobrindo os fluxos principais: health check,
criação de runs (modo mock, sem custo de LLM real), streaming SSE do
progresso e listagem do painel admin.

Uso (com a stack local rodando — backend em :8000, Supabase local em :54321,
USE_MOCK_LLM=true no apps/server/.env):

    cd apps/server
    venv\\Scripts\\python.exe -m locust -f tests/load/locustfile.py \\
        --host=http://127.0.0.1:8000 --headless -u 20 -r 5 -t 2m --csv=tests/load/results

Cada usuário virtual cria sua própria conta no Supabase local (signup) no
`on_start`, evitando qualquer estado compartilhado ou dependência de dados
pré-existentes.
"""
import time
import uuid

from locust import HttpUser, between, task

SUPABASE_URL = "http://127.0.0.1:54321"
SUPABASE_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9."
    "CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"
)


class AetherUser(HttpUser):
    """Usuário autenticado que cria runs e acompanha o progresso via SSE."""

    wait_time = between(1, 3)

    def on_start(self) -> None:
        email = f"load-{uuid.uuid4().hex[:12]}@e2e.local"
        password = "senha-teste-123"
        resp = self.client.post(
            f"{SUPABASE_URL}/auth/v1/signup",
            json={"email": email, "password": password},
            headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
            name="/auth/v1/signup",
        )
        token = resp.json().get("access_token") if resp.status_code < 400 else None
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}

    @task(5)
    def health_check(self) -> None:
        self.client.get("/api/v1/health", name="/health")

    @task(3)
    def list_skills(self) -> None:
        self.client.get("/api/v1/skills", headers=self.headers, name="/skills")

    @task(1)
    def create_and_watch_run(self) -> None:
        if not self.headers:
            return
        resp = self.client.post(
            "/api/v1/runs",
            json={"objective": "Verificar o horário atual do sistema (teste de carga)"},
            headers=self.headers,
            name="/runs [POST]",
        )
        if resp.status_code != 202:
            return
        run_id = resp.json()["run_id"]

        # Streaming SSE via requests puro: o cliente do Locust não entende
        # `text/event-stream` nativamente, então medimos manualmente o tempo
        # até o primeiro byte de resposta (proxy de latência de conexão).
        start = time.perf_counter()
        try:
            with self.client.get(
                f"/api/v1/runs/{run_id}/stream",
                headers=self.headers,
                name="/runs/[id]/stream",
                stream=True,
                timeout=10,
            ) as stream_resp:
                for _ in stream_resp.iter_lines():
                    break
        except Exception:
            pass
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self.environment.events.request.fire(
                request_type="SSE",
                name="/runs/[id]/stream first-byte",
                response_time=elapsed_ms,
                response_length=0,
            )
