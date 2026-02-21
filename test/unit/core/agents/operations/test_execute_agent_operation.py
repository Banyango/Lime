import asyncio
from pathlib import Path

import pytest

from core.agents.models import ExecutionModel
from core.agents.operations import execute_agent_operation as operation_module
from core.agents.operations.execute_agent_operation import ExecuteAgentOperation
from core.interfaces.agent_plugin import AgentPlugin
from entities.prompt_integrity import PromptUnverifiedPathError


class MockPlugin(AgentPlugin):
    """Mock plugin for testing."""

    def __init__(self, token: str):
        self.token = token
        self.handle_called = False
        self.handle_params = None

    def is_match(self, token: str) -> bool:
        return token == self.token

    async def handle(self, params: str, execution_model: ExecutionModel):
        self.handle_called = True
        self.handle_params = params


class AlwaysUnverifiedIntegrity:
    def __init__(self):
        self.verify_bytes_calls = 0

    def verify_trusted_path(self, path):
        raise PromptUnverifiedPathError("outside trusted root")

    def verify_bytes(self, path, content_bytes):
        self.verify_bytes_calls += 1


class AlwaysTrustedIntegrity:
    def __init__(self):
        self.verify_trusted_path_calls = 0
        self.verify_bytes_calls = 0
        self.last_verified_path = None
        self.last_verified_bytes = b""

    def verify_trusted_path(self, path):
        self.verify_trusted_path_calls += 1

    def verify_bytes(self, path, content_bytes):
        self.verify_bytes_calls += 1
        self.last_verified_path = path
        self.last_verified_bytes = content_bytes


class FakeIncludeNode:
    def __init__(self, template_name: str):
        self.template_name = template_name


class FakeParser:
    def parse(self, content: str):
        return {}, []


def _create_execution_model():
    return ExecutionModel()


def _create_operation(
    plugins: list[AgentPlugin] | None = None,
    tmp_path: Path | None = None,
    prompt_integrity=None,
    allow_unverified: bool = False,
):
    if plugins is None:
        plugins = []

    execution_model = _create_execution_model()

    operation = ExecuteAgentOperation(
        plugins=plugins,
        execution_model=execution_model,
        prompt_integrity=prompt_integrity,
        allow_unverified=allow_unverified,
    )

    if tmp_path:
        operation.base_path = tmp_path

    return operation


def _patch_include_parser(monkeypatch):
    """Patch parser/include node classes to isolate include execution behavior."""
    monkeypatch.setattr(operation_module, "IncludeNode", FakeIncludeNode)
    monkeypatch.setattr(operation_module, "Parser", FakeParser)


# --- Upstream Tests ---


@pytest.mark.asyncio
async def test_execute_async_should_parse_and_process_text_node_when_given_text():
    # Arrange
    operation = _create_operation()
    mgx_content = """---
description: "Test file"
---

<<
Hello, World!
>>
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert operation.execution_model.context.window == "Hello, World!\n"
    assert operation.execution_model.metadata == {"description": '"Test file"'}


@pytest.mark.asyncio
async def test_execute_async_should_replace_variables_in_text_when_variable_exists():
    # Arrange
    operation = _create_operation()
    operation.execution_model.context.set_variable("name", "Alice")
    mgx_content = """<<
Hello, ${name}!
>>
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert operation.execution_model.context.window == "Hello, Alice!\n"


@pytest.mark.asyncio
async def test_execute_async_should_handle_state_node_when_state_defined():
    # Arrange
    operation = _create_operation()
    mgx_content = """@state my_var = "test_value"
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert operation.execution_model.context.get_variable_value("my_var") == "test_value"


@pytest.mark.asyncio
async def test_execute_async_should_handle_state_with_number_when_state_defined():
    # Arrange
    operation = _create_operation()
    mgx_content = """@state counter = 42
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert operation.execution_model.context.get_variable_value("counter") == 42


@pytest.mark.asyncio
async def test_execute_async_should_handle_state_with_list_when_state_defined():
    # Arrange
    operation = _create_operation()
    mgx_content = """@state items = ["apple", "banana", "cherry"]
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert operation.execution_model.context.get_variable_value("items") == [
        "apple",
        "banana",
        "cherry",
    ]


@pytest.mark.asyncio
async def test_execute_async_should_process_for_loop_when_iterating_over_list():
    # Arrange
    operation = _create_operation()
    operation.execution_model.context.set_variable("items", ["a", "b", "c"])
    mgx_content = """for item in items:
    <<Item: ${item}>>
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert operation.execution_model.context.window == "Item: a\nItem: b\nItem: c\n"


@pytest.mark.asyncio
async def test_execute_async_should_handle_if_node_when_condition_is_true():
    # Arrange
    operation = _create_operation()
    operation.execution_model.context.set_variable("is_active", True)
    mgx_content = """if is_active:
    <<Active>>
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert operation.execution_model.context.window == "Active\n"


@pytest.mark.asyncio
async def test_execute_async_should_skip_if_block_when_condition_is_false():
    # Arrange
    operation = _create_operation()
    operation.execution_model.context.set_variable("is_active", False)
    mgx_content = """if is_active:
    <<Active>>
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert operation.execution_model.context.window == ""


@pytest.mark.asyncio
async def test_execute_async_should_call_plugin_when_effect_matches():
    # Arrange
    mock_plugin = MockPlugin("test")
    operation = _create_operation(plugins=[mock_plugin])
    mgx_content = """@effect test param1 param2
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert mock_plugin.handle_called is True
    assert mock_plugin.handle_params == "param1 param2"


@pytest.mark.asyncio
async def test_execute_async_should_not_call_plugin_when_effect_does_not_match():
    # Arrange
    mock_plugin = MockPlugin("other")
    operation = _create_operation(plugins=[mock_plugin])
    mgx_content = """@effect test param1
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert mock_plugin.handle_called is False


@pytest.mark.asyncio
async def test_execute_async_should_handle_include_when_file_exists(tmp_path):
    # Arrange
    operation = _create_operation()

    # Create a temporary .mg file
    include_file = tmp_path / "include.mg"
    include_file.write_text("<<Included content>>")

    mgx_content = """[[ include.mg ]]
"""

    # Act
    await operation.execute_async(mgx_content, base_path=tmp_path)

    # Assert
    assert operation.execution_model.context.window == "Included content\n"


@pytest.mark.asyncio
async def test_execute_async_should_skip_include_when_file_does_not_exist(tmp_path):
    # Arrange
    operation = _create_operation()
    mgx_content = """[[ nonexistent.mg ]]
"""

    # Act
    with pytest.raises(FileNotFoundError, match="Included prompt file was not found"):
        await operation.execute_async(mgx_content, base_path=tmp_path)

    # Assert
    # assert operation.execution_model.context.window == ""


@pytest.mark.asyncio
async def test_execute_async_should_start_turn_when_executed():
    # Arrange
    operation = _create_operation()
    mgx_content = """<<Test>>
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert len(operation.execution_model.turns) == 1


@pytest.mark.asyncio
async def test_replace_variables_in_text_node_should_replace_simple_variable():
    # Arrange
    operation = _create_operation()
    operation.execution_model.context.set_variable("name", "Bob")

    # Act
    result = operation.replace_variables_in_text_node("Hello, ${name}!")

    # Assert
    assert result == "Hello, Bob!"


@pytest.mark.asyncio
async def test_replace_variables_in_text_node_should_replace_nested_variable():
    # Arrange
    operation = _create_operation()
    operation.execution_model.context.set_variable("user", {"name": "Charlie"})

    # Act
    result = operation.replace_variables_in_text_node("Hello, ${user.name}!")

    # Assert
    assert result == "Hello, Charlie!"


@pytest.mark.asyncio
async def test_replace_variables_in_text_node_should_replace_with_empty_when_variable_not_found():
    # Arrange
    operation = _create_operation()

    # Act
    result = operation.replace_variables_in_text_node("Hello, ${unknown}!")

    # Assert
    assert result == "Hello, !"


@pytest.mark.asyncio
async def test_replace_variables_in_text_node_should_replace_multiple_variables():
    # Arrange
    operation = _create_operation()
    operation.execution_model.context.set_variable("first", "John")
    operation.execution_model.context.set_variable("last", "Doe")

    # Act
    result = operation.replace_variables_in_text_node("Name: ${first} ${last}")

    # Assert
    assert result == "Name: John Doe"


@pytest.mark.asyncio
async def test_is_truthy_should_return_true_when_value_is_true():
    # Arrange
    operation = _create_operation()

    # Act & Assert
    assert operation._is_truthy(True) is True
    assert operation._is_truthy("text") is True
    assert operation._is_truthy([1, 2, 3]) is True
    assert operation._is_truthy({"key": "value"}) is True
    assert operation._is_truthy(42) is True
    assert operation._is_truthy(1.5) is True


@pytest.mark.asyncio
async def test_is_truthy_should_return_false_when_value_is_falsy():
    # Arrange
    operation = _create_operation()

    # Act & Assert
    assert operation._is_truthy(False) is False
    assert operation._is_truthy(None) is False
    assert operation._is_truthy("") is False
    assert operation._is_truthy([]) is False
    assert operation._is_truthy({}) is False
    assert operation._is_truthy(0) is False
    assert operation._is_truthy(0.0) is False


@pytest.mark.asyncio
async def test_execute_plugin_should_call_matching_plugin_when_plugin_matches():
    # Arrange
    mock_plugin = MockPlugin("run")
    operation = _create_operation(plugins=[mock_plugin])

    # Act
    await operation.execute_plugin(plugin="run", operation="execute")

    # Assert
    assert mock_plugin.handle_called is True
    assert mock_plugin.handle_params == "execute"


@pytest.mark.asyncio
async def test_execute_plugin_should_not_call_plugin_when_no_match():
    # Arrange
    mock_plugin = MockPlugin("run")
    operation = _create_operation(plugins=[mock_plugin])

    # Act
    await operation.execute_plugin(plugin="other", operation="execute")

    # Assert
    assert mock_plugin.handle_called is False


@pytest.mark.asyncio
async def test_execute_async_should_handle_variable_node_when_variable_exists():
    # Arrange
    operation = _create_operation()
    operation.execution_model.context.set_variable("greeting", "Hi there")
    mgx_content = """<<${greeting}>>
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert operation.execution_model.context.window == "Hi there\n"


@pytest.mark.asyncio
async def test_execute_async_should_handle_nested_for_loops():
    # Arrange
    operation = _create_operation()
    operation.execution_model.context.set_variable("outer", [1, 2])
    operation.execution_model.context.set_variable("inner", ["a", "b"])
    mgx_content = """for x in outer:
    for y in inner:
        <<${x}${y} >>
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert operation.execution_model.context.window == "1a\n1b\n2a\n2b\n"


@pytest.mark.asyncio
async def test_execute_async_should_process_import_node_when_import_present():
    # Arrange
    operation = _create_operation()
    mgx_content = """from math import sqrt
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert len(operation.execution_model.turns) == 1


@pytest.mark.asyncio
async def test_execute_async_should_handle_complex_mgx_file():
    # Arrange
    mock_plugin = MockPlugin("run")
    operation = _create_operation(plugins=[mock_plugin])
    operation.execution_model.context.set_variable("items", ["apple", "banana"])

    mgx_content = """---
description: "Complex test"
author: "Test"
---

@state count = 0

<<Processing items:>>

for item in items:
    <<
    - ${item}
    >>

@effect run
"""

    # Act
    await operation.execute_async(mgx_content)

    # Assert
    assert operation.execution_model.metadata == {
        "description": '"Complex test"',
        "author": '"Test"',
    }
    assert operation.execution_model.context.get_variable_value("count") == 0
    assert "Processing items:" in operation.execution_model.context.window
    assert "- apple" in operation.execution_model.context.window
    assert "- banana" in operation.execution_model.context.window
    assert mock_plugin.handle_called is True


# --- Prompt Integrity Tests (Feature Branch) ---


def test_normalize_include_path_should_append_mg_extension_when_extension_is_missing():
    # Arrange
    sut = _create_operation()

    # Act
    result = sut._normalize_include_path("salt/use-uv/use-uv")

    # Assert
    assert result == "salt/use-uv/use-uv.mg"


def test_normalize_include_path_should_keep_md_extension_when_extension_is_allowed():
    # Arrange
    sut = _create_operation()

    # Act
    result = sut._normalize_include_path("salt/setup.md")

    # Assert
    assert result == "salt/setup.md"


def test_normalize_include_path_should_raise_value_error_when_extension_is_not_supported():
    # Arrange
    sut = _create_operation()

    # Act
    # Assert
    with pytest.raises(ValueError, match="Unsupported include extension"):
        sut._normalize_include_path("salt/setup.txt")


def test_process_nodes_async_should_execute_false_block_when_if_condition_is_false(monkeypatch):
    # Arrange
    class FakeTextNode:
        def __init__(self, content: str):
            self.content = content

    class FakeIfNode:
        def __init__(self, condition: str, true_block: list, false_block: list):
            self.condition = condition
            self.true_block = true_block
            self.false_block = false_block

    monkeypatch.setattr(operation_module, "TextNode", FakeTextNode)
    monkeypatch.setattr(operation_module, "IfNode", FakeIfNode)

    execution_model = _create_execution_model()
    execution_model.context.set_variable("feature_enabled", False)

    sut = ExecuteAgentOperation(
        plugins=[],
        execution_model=execution_model,
    )

    if_node = FakeIfNode(
        condition="feature_enabled",
        true_block=[FakeTextNode("TRUE")],
        false_block=[FakeTextNode("FALSE")],
    )

    # Act
    asyncio.run(sut._process_nodes_async([if_node]))

    # Assert
    assert execution_model.context.window == "FALSE"


def test_process_nodes_async_should_raise_unverified_path_error_when_unverified_include_is_disallowed(
    monkeypatch, tmp_path
):
    # Arrange
    _patch_include_parser(monkeypatch)

    include_file = tmp_path / "external.mg"
    include_file.write_text("<<external>>")

    sut = _create_operation(
        tmp_path=tmp_path,
        prompt_integrity=AlwaysUnverifiedIntegrity(),
        allow_unverified=False,
    )

    # Act
    # Assert
    with pytest.raises(PromptUnverifiedPathError):
        asyncio.run(sut._process_nodes_async([FakeIncludeNode("external")]))


def test_process_nodes_async_should_raise_file_not_found_error_when_include_file_is_missing(monkeypatch, tmp_path):
    # Arrange
    _patch_include_parser(monkeypatch)
    sut = _create_operation(tmp_path=tmp_path)

    # Act
    # Assert
    with pytest.raises(FileNotFoundError, match="Included prompt file was not found"):
        asyncio.run(sut._process_nodes_async([FakeIncludeNode("does-not-exist")]))


def test_process_nodes_async_should_skip_hash_verification_when_unverified_include_is_allowed(monkeypatch, tmp_path):
    # Arrange
    _patch_include_parser(monkeypatch)

    include_file = tmp_path / "external.mg"
    include_file.write_text("<<external>>")
    warning_messages = []

    def _fake_warning(message: str, *args, **kwargs):
        warning_messages.append(message.format(*args))

    monkeypatch.setattr(operation_module.logger, "warning", _fake_warning)

    integrity = AlwaysUnverifiedIntegrity()
    sut = _create_operation(
        tmp_path=tmp_path,
        prompt_integrity=integrity,
        allow_unverified=True,
    )

    # Act
    asyncio.run(sut._process_nodes_async([FakeIncludeNode("external")]))

    # Assert
    assert integrity.verify_bytes_calls == 0
    assert len(warning_messages) == 1
    assert "Allowing unverified include outside trusted prompt root" in warning_messages[0]
    assert str(include_file.resolve(strict=False)) in warning_messages[0]
    assert "outside trusted root" in warning_messages[0]


def test_process_nodes_async_should_verify_trusted_include_when_include_is_in_trusted_root(monkeypatch, tmp_path):
    # Arrange
    _patch_include_parser(monkeypatch)

    include_file = tmp_path / "trusted.mg"
    include_file.write_text("<<trusted>>")

    integrity = AlwaysTrustedIntegrity()
    sut = _create_operation(
        tmp_path=tmp_path,
        prompt_integrity=integrity,
        allow_unverified=False,
    )

    # Act
    asyncio.run(sut._process_nodes_async([FakeIncludeNode("trusted")]))

    # Assert
    assert integrity.verify_trusted_path_calls == 1
    assert integrity.verify_bytes_calls == 1
    assert str(integrity.last_verified_path) == str(include_file.resolve(strict=False))
    assert integrity.last_verified_bytes == b"<<trusted>>"


def test_process_nodes_async_should_raise_error_when_included_prompt_content_is_malformed(monkeypatch, tmp_path):
    # Arrange
    class RaisingParser:
        def parse(self, content: str):
            raise ValueError("Malformed include prompt content")

    monkeypatch.setattr(operation_module, "IncludeNode", FakeIncludeNode)
    monkeypatch.setattr(operation_module, "Parser", RaisingParser)

    include_file = tmp_path / "trusted.mg"
    include_file.write_text("<<broken>>")
    sut = _create_operation(tmp_path=tmp_path)

    # Act
    # Assert
    with pytest.raises(ValueError, match="Malformed include prompt content"):
        asyncio.run(sut._process_nodes_async([FakeIncludeNode("trusted")]))


def test_process_nodes_async_should_raise_unicode_decode_error_when_include_file_is_not_utf8(monkeypatch, tmp_path):
    # Arrange
    _patch_include_parser(monkeypatch)
    binary_include_file = tmp_path / "binary.mg"
    binary_include_file.write_bytes(b"\xff")
    sut = _create_operation(tmp_path=tmp_path)

    # Act
    # Assert
    with pytest.raises(UnicodeDecodeError):
        asyncio.run(sut._process_nodes_async([FakeIncludeNode("binary")]))
