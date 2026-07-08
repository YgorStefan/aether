import pytest
from cryptography.fernet import Fernet

from core import crypto


@pytest.fixture(autouse=True)
def _with_key(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setattr(crypto.settings, "settings_encryption_key", key)
    return key


def test_encrypt_decrypt_round_trip():
    encrypted = crypto.encrypt("minha-chave-secreta")
    assert encrypted != "minha-chave-secreta"
    assert encrypted.startswith("enc:")
    assert crypto.decrypt(encrypted) == "minha-chave-secreta"


def test_decrypt_valor_legado_em_texto_puro():
    # Valores gravados antes da criptografia existir não têm o prefixo "enc:"
    assert crypto.decrypt("chave-antiga-em-texto-puro") == "chave-antiga-em-texto-puro"


def test_encrypt_sem_chave_configurada_retorna_texto_puro(monkeypatch):
    monkeypatch.setattr(crypto.settings, "settings_encryption_key", "")
    assert crypto.encrypt("valor") == "valor"


def test_decrypt_com_valor_criptografado_mas_sem_chave_levanta_erro(monkeypatch):
    encrypted = crypto.encrypt("valor")
    monkeypatch.setattr(crypto.settings, "settings_encryption_key", "")
    with pytest.raises(ValueError):
        crypto.decrypt(encrypted)


def test_decrypt_com_chave_errada_levanta_erro(monkeypatch):
    encrypted = crypto.encrypt("valor")
    monkeypatch.setattr(crypto.settings, "settings_encryption_key", Fernet.generate_key().decode())
    with pytest.raises(ValueError):
        crypto.decrypt(encrypted)
