import io

from rich.console import Console, Group

from lime_ai.app.config import AppConfig
from lime_ai.app.writers.writer import CliWriter
from lime_ai.core.agents.models import ExecutionModel
from lime_ai.entities.function import FunctionCall
from lime_ai.entities.run import ContentBlock, ContentBlockType, Run, RunStatus, TokenUsage


def _create_writer() -> CliWriter:
    return CliWriter(app_config=AppConfig(show_context=False))


def _create_run(status: RunStatus = RunStatus.COMPLETED) -> Run:
    return Run(
        status=status,
        model="gpt-4o",
        duration_ms=1200.0,
        tokens=TokenUsage(input_tokens=100, output_tokens=50),
        tool_calls=[],
    )


def _create_execution_model_with_turns(count: int, status: RunStatus = RunStatus.COMPLETED) -> ExecutionModel:
    model = ExecutionModel()
    model.start()
    for _ in range(count):
        model.start_turn()
        run = _create_run(status=status)
        model.turns[-1].run = run
    return model


def _render_parts_to_str(parts: list) -> str:
    """Helper to render a list of Rich renderables to string."""
    console = Console(file=io.StringIO(), highlight=False)
    console.print(Group(*parts))
    return console.file.getvalue()


# --- _build_header ---


def test_build_header_should_include_logo():
    # Arrange
    writer = _create_writer()
    model = ExecutionModel()
    model.start()

    # Act
    parts = writer.build_header(model)

    # Assert — first element is the LOGO
    from lime_ai.app import LOGO

    assert parts[0] is LOGO


def test_build_header_should_include_warnings():
    # Arrange
    writer = _create_writer()
    model = ExecutionModel()
    model.start()
    model.add_warning("something deprecated")

    # Act
    parts = writer.build_header(model)

    # Assert
    console = Console(file=io.StringIO(), highlight=False)
    from rich.console import Group

    console.print(Group(*parts))
    output = console.file.getvalue()
    assert "something deprecated" in output


def test_build_header_should_include_metadata():
    # Arrange
    writer = _create_writer()
    model = ExecutionModel()
    model.start()
    model.metadata["version"] = "1.2.3"

    # Act
    parts = writer.build_header(model)

    # Assert
    console = Console(file=io.StringIO(), highlight=False)
    from rich.console import Group

    console.print(Group(*parts))
    output = console.file.getvalue()
    assert "version" in output
    assert "1.2.3" in output


# --- _build_status ---


def test_build_status_should_return_none_when_no_runs():
    # Arrange
    writer = _create_writer()
    model = ExecutionModel()
    model.start()
    model.start_turn()
    # Turn has no run

    # Act
    result = writer._build_status(model)

    # Assert
    assert result is None


def test_build_status_should_return_executing_when_running():
    # Arrange
    writer = _create_writer()
    model = _create_execution_model_with_turns(1, status=RunStatus.RUNNING)

    # Act
    result = writer._build_status(model)

    # Assert
    assert result is not None
    assert "Executing" in result.plain


def test_build_status_should_return_completed_when_all_turns_done():
    # Arrange
    writer = _create_writer()
    model = _create_execution_model_with_turns(2, status=RunStatus.COMPLETED)

    # Act
    result = writer._build_status(model)

    # Assert
    assert result is not None
    assert "All turns completed" in result.plain


def test_build_status_should_return_completed_when_turns_have_error_status():
    # Arrange
    writer = _create_writer()
    model = _create_execution_model_with_turns(1, status=RunStatus.ERROR)

    # Act
    result = writer._build_status(model)

    # Assert
    assert result is not None
    assert "All turns completed" in result.plain


# --- render_run ---


def test_render_run_should_include_response_content():
    # Arrange
    writer = _create_writer()
    run = Run(
        status=RunStatus.COMPLETED,
        tool_calls=[],
        content_blocks=[ContentBlock(type=ContentBlockType.RESPONSE, text="Hello from the model")],
    )

    # Act
    parts = writer.render_run(run, index=1)

    # Assert
    output = _render_parts_to_str(parts)
    assert "Hello from the model" in output


def test_render_run_should_skip_empty_response_blocks():
    # Arrange
    writer = _create_writer()
    run = Run(
        status=RunStatus.COMPLETED,
        tool_calls=[],
        content_blocks=[
            ContentBlock(type=ContentBlockType.RESPONSE, text=""),
            ContentBlock(type=ContentBlockType.RESPONSE, text="Actual content"),
        ],
    )

    # Act
    parts = writer.render_run(run, index=1)

    # Assert
    output = _render_parts_to_str(parts)
    assert "Actual content" in output


def test_render_run_should_include_token_usage_when_completed():
    # Arrange
    writer = _create_writer()
    run = Run(
        status=RunStatus.COMPLETED,
        tool_calls=[],
        tokens=TokenUsage(input_tokens=100, output_tokens=50),
    )

    # Act
    parts = writer.render_run(run, index=1)

    # Assert
    output = _render_parts_to_str(parts)
    assert "100" in output
    assert "50" in output


def test_render_run_should_skip_reasoning_blocks():
    # Arrange
    writer = _create_writer()
    run = Run(
        status=RunStatus.COMPLETED,
        tool_calls=[],
        content_blocks=[
            ContentBlock(type=ContentBlockType.REASONING, text="Internal reasoning"),
            ContentBlock(type=ContentBlockType.RESPONSE, text="Public response"),
        ],
    )

    # Act
    parts = writer.render_run(run, index=1)

    # Assert
    output = _render_parts_to_str(parts)
    assert "Internal reasoning" not in output
    assert "Public response" in output


def test_render_run_should_include_logging_blocks():
    # Arrange
    writer = _create_writer()
    run = Run(
        status=RunStatus.COMPLETED,
        tool_calls=[],
        content_blocks=[ContentBlock(type=ContentBlockType.LOGGING, text="Log message")],
    )

    # Act
    parts = writer.render_run(run, index=1)

    # Assert
    output = _render_parts_to_str(parts)
    assert "Log message" in output


# --- render_function_calls ---


def test_render_function_calls_should_include_method_name():
    # Arrange
    writer = _create_writer()
    function_calls = [FunctionCall(method="my_func", params='{"x": 1}', result="42")]

    # Act
    parts = writer.render_function_calls(function_calls)

    # Assert
    output = _render_parts_to_str(parts)
    assert "my_func" in output


def test_render_function_calls_should_include_params():
    # Arrange
    writer = _create_writer()
    function_calls = [FunctionCall(method="my_func", params='{"x": 1}', result="42")]

    # Act
    parts = writer.render_function_calls(function_calls)

    # Assert
    output = _render_parts_to_str(parts)
    assert '"x": 1' in output


def test_render_function_calls_should_include_result():
    # Arrange
    writer = _create_writer()
    function_calls = [FunctionCall(method="my_func", params='{"x": 1}', result="Result value")]

    # Act
    parts = writer.render_function_calls(function_calls)

    # Assert
    output = _render_parts_to_str(parts)
    assert "Result value" in output


def test_render_function_calls_should_handle_empty_list():
    # Arrange
    writer = _create_writer()
    function_calls = []

    # Act
    parts = writer.render_function_calls(function_calls)

    # Assert
    assert parts == []


def test_render_function_calls_should_handle_multiple_calls():
    # Arrange
    writer = _create_writer()
    function_calls = [
        FunctionCall(method="func1", params='{"a": 1}', result="result1"),
        FunctionCall(method="func2", params='{"b": 2}', result="result2"),
    ]

    # Act
    parts = writer.render_function_calls(function_calls)

    # Assert
    output = _render_parts_to_str(parts)
    assert "func1" in output
    assert "func2" in output
    assert "result1" in output
    assert "result2" in output
