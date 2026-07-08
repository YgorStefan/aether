from functools import lru_cache

from supabase import Client, create_client

from core.config import settings


@lru_cache(maxsize=1)
def get_service_client() -> Client:
    """Cliente Supabase (service role) compartilhado entre requisições.

    Criar um client novo a cada chamada custa ~300-450ms neste ambiente local
    (medido em teste de carga) — reaproveitar uma única instância elimina essa
    tara em toda a API sem nenhuma mudança de comportamento (o client é
    stateless do lado da aplicação, apenas encapsula um `httpx.Client`).
    """
    return create_client(settings.supabase_url, settings.supabase_service_key)
