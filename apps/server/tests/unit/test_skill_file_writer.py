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
