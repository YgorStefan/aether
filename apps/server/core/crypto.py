"""Criptografia simétrica para segredos armazenados no banco (ex: API keys de usuário).

Usa Fernet (AES-128 + HMAC) com a chave em SETTINGS_ENCRYPTION_KEY. Se a chave não
estiver configurada, os valores são lidos/gravados em texto puro (comportamento
anterior) e um warning é logado — recomendado apenas para desenvolvimento local.

Valores criptografados são prefixados com "enc:" para permanecerem distinguíveis
de valores em texto puro já existentes no banco (compatibilidade retroativa, sem
precisar de migration de dados).
"""

import structlog
from cryptography.fernet import Fernet, InvalidToken

from core.config import settings

logger = structlog.get_logger()

_PREFIX = "enc:"


def _fernet() -> Fernet | None:
    if not settings.settings_encryption_key:
        return None
    return Fernet(settings.settings_encryption_key.encode())


def encrypt(value: str) -> str:
    fernet = _fernet()
    if fernet is None:
        logger.warning("settings_encryption_key_not_set", detail="armazenando valor em texto puro")
        return value
    return _PREFIX + fernet.encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    if not value.startswith(_PREFIX):
        return value  # valor legado em texto puro

    fernet = _fernet()
    if fernet is None:
        raise ValueError(
            "Valor está criptografado, mas SETTINGS_ENCRYPTION_KEY não está configurada"
        )
    try:
        return fernet.decrypt(value[len(_PREFIX):].encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Falha ao decriptografar valor: chave inválida") from exc
