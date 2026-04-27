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
