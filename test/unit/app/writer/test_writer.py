import io

from rich.console import Console
from rich.text import Text

from app.config import AppConfig
from app.writers.writer import CliWriter
from core.agents.models import ExecutionModel
from entities.function import FunctionCall
from entities.run import ContentBlock, ContentBlockType, Run, RunStatus, TokenUsage


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


def _render_group_to_str(writer: CliWriter, model: ExecutionModel) -> str:
    group = writer._build_display(model)
    console = Console(file=io.StringIO(), highlight=False)
    console.print(group)
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
    from app.writers.writer import LOGO

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


# --- _render_run_summary ---


def test_render_run_summary_should_include_run_index_and_status():
    # Arrange
    writer = _create_writer()
    run = _create_run(status=RunStatus.COMPLETED)

    # Act
    parts = writer._render_run_summary(run, index=3)

    # Assert
    assert len(parts) == 2
    header = parts[0]
    assert isinstance(header, Text)
    rendered = header.plain
    assert "Run 3" in rendered
    assert "completed" in rendered


def test_render_run_summary_should_include_model_and_duration_when_present():
    # Arrange
    writer = _create_writer()
    run = _create_run()

    # Act
    parts = writer._render_run_summary(run, index=1)

    # Assert
    header = parts[0]
    assert isinstance(header, Text)
    rendered = header.plain
    assert "gpt-4o" in rendered
    assert "1.2s" in rendered


def test_render_run_summary_should_include_token_count_when_nonzero():
    # Arrange
    writer = _create_writer()
    run = _create_run()

    # Act
    parts = writer._render_run_summary(run, index=1)

    # Assert
    header = parts[0]
    assert "150" in header.plain


def test_render_run_summary_should_include_click_hint():
    # Arrange
    writer = _create_writer()
    run = _create_run(status=RunStatus.COMPLETED)

    # Act
    parts = writer._render_run_summary(run, index=1)

    # Assert
    header = parts[0]
    assert "click to expand" in header.plain


def test_render_run_summary_should_omit_tokens_when_zero():
    # Arrange
    writer = _create_writer()
    run = Run(status=RunStatus.COMPLETED, tool_calls=[], tokens=TokenUsage())

    # Act
    parts = writer._render_run_summary(run, index=1)

    # Assert
    header = parts[0]
    assert "tokens" not in header.plain


# --- _build_display turn rendering ---


def test_build_display_should_render_full_run_when_it_is_the_last_turn():
    # Arrange
    writer = _create_writer()
    model = ExecutionModel()
    model.start()
    model.start_turn()
    run = Run(
        status=RunStatus.RUNNING,
        tool_calls=[],
        content_blocks=[ContentBlock(type=ContentBlockType.RESPONSE, text="Hello from the model")],
    )
    model.turns[-1].run = run

    # Act
    output = _render_group_to_str(writer, model)

    # Assert
    assert "Hello from the model" in output


def test_build_display_should_render_summary_only_when_turn_is_not_the_last():
    # Arrange
    writer = _create_writer()
    model = ExecutionModel()
    model.start()
    # First turn (completed, not last)
    model.start_turn()
    completed_run = Run(
        status=RunStatus.COMPLETED,
        model="gpt-4o",
        tool_calls=[],
        content_blocks=[ContentBlock(type=ContentBlockType.RESPONSE, text="Old response content")],
    )
    model.turns[-1].run = completed_run
    # Second turn (active, last)
    model.start_turn()
    active_run = Run(
        status=RunStatus.RUNNING,
        tool_calls=[],
        content_blocks=[ContentBlock(type=ContentBlockType.RESPONSE, text="Current response")],
    )
    model.turns[-1].run = active_run

    # Act
    output = _render_group_to_str(writer, model)

    # Assert — completed turn content is hidden, active turn content is shown
    assert "Old response content" not in output
    assert "Current response" in output
    assert "completed" in output  # summary line still present


def test_build_display_should_hide_function_calls_for_completed_turns():
    # Arrange
    writer = _create_writer()
    model = ExecutionModel()
    model.start()
    # First turn with a function call (not last)
    model.start_turn()
    model.turns[-1].function_calls = [FunctionCall(method="my_func", params='{"x": 1}', result="42")]
    model.turns[-1].run = _create_run(status=RunStatus.COMPLETED)
    # Second (active) turn
    model.start_turn()
    model.turns[-1].run = _create_run(status=RunStatus.RUNNING)

    # Act
    output = _render_group_to_str(writer, model)

    # Assert — function call from the old turn is not rendered
    assert "my_func" not in output


def test_build_display_should_show_function_calls_for_last_turn():
    # Arrange
    writer = _create_writer()
    model = ExecutionModel()
    model.start()
    model.start_turn()
    model.turns[-1].function_calls = [FunctionCall(method="active_func", params='{"y": 2}', result="99")]
    model.turns[-1].run = _create_run(status=RunStatus.RUNNING)

    # Act
    output = _render_group_to_str(writer, model)

    # Assert
    assert "active_func" in output


def test_build_display_should_show_executing_when_turns_are_running():
    # Arrange
    writer = _create_writer()
    model = ExecutionModel()
    model.start()
    model.start_turn()
    model.turns[-1].run = _create_run(status=RunStatus.RUNNING)

    # Act
    output = _render_group_to_str(writer, model)

    # Assert
    assert "Executing..." in output
    assert "All turns completed" not in output


def test_build_display_should_show_completed_when_all_turns_are_done():
    # Arrange
    writer = _create_writer()
    model = ExecutionModel()
    model.start()
    model.start_turn()
    model.turns[-1].run = _create_run(status=RunStatus.COMPLETED)

    # Act
    output = _render_group_to_str(writer, model)

    # Assert
    assert "All turns completed" in output
    assert "Executing..." not in output


def test_build_display_should_show_completed_when_all_turns_have_completed_or_error_status():
    # Arrange
    writer = _create_writer()
    model = ExecutionModel()
    model.start()
    # First turn completed
    model.start_turn()
    model.turns[-1].run = _create_run(status=RunStatus.COMPLETED)
    # Second turn has error
    model.start_turn()
    model.turns[-1].run = _create_run(status=RunStatus.ERROR)

    # Act
    output = _render_group_to_str(writer, model)

    # Assert
    assert "All turns completed" in output
    assert "Executing..." not in output


def test_build_display_should_not_show_execution_status_when_no_runs():
    # Arrange
    writer = _create_writer()
    model = ExecutionModel()
    model.start()
    model.start_turn()
    # Turn exists but has no run

    # Act
    output = _render_group_to_str(writer, model)

    # Assert
    assert "Executing..." not in output
    assert "All turns completed" not in output
