from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from rich.console import Group
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.events import Click
from textual.widgets import Footer, Header, Input, Static

from core.agents.models import ExecutionModel

if TYPE_CHECKING:
    from app.writers.writer import CliWriter
    from entities.function import FunctionCall
    from entities.run import Run


class ExecutionWidget(Static):
    """Widget that renders the Rich Group from _build_display()."""

    def __init__(self, build_display: Callable[[], Group]) -> None:
        super().__init__()
        self._build_display = build_display

    def on_mount(self) -> None:
        """Initialize the widget content on mount."""
        self.update(self._build_display())

    def refresh_display(self) -> None:
        """Update the widget with fresh content."""
        self.update(self._build_display())


class RunWidget(Static):
    """Widget for a single run turn, supporting expand/collapse toggle on click."""

    def __init__(self, run: Run, index: int, writer: CliWriter, is_last: bool = False) -> None:
        super().__init__()
        self._run = run
        self._index = index
        self._writer = writer
        self._expanded = is_last
        self._user_toggled = False
        self._function_calls: list[FunctionCall] = []

    def on_mount(self) -> None:
        self.update(self._build_renderable())

    def on_click(self, event: Click) -> None:
        self._expanded = not self._expanded
        self._user_toggled = True
        self.update(self._build_renderable())

    def update_run(self, run: Run, is_last: bool = False, function_calls: list | None = None) -> None:
        """Update run data and re-render; auto-manages expanded state unless user has toggled."""
        self._run = run
        if not self._user_toggled:
            self._expanded = is_last
        self._function_calls = function_calls or []
        self.update(self._build_renderable())

    def _build_renderable(self) -> Group:
        parts: list = []
        if self._expanded:
            if self._function_calls:
                parts.extend(self._writer._render_function_calls(self._function_calls))
            parts.extend(self._writer._render_run(self._run, self._index))
        else:
            parts.extend(self._writer._render_run_summary(self._run, self._index))
        return Group(*parts)


class LimeApp(App):
    """Textual app with a scrollable panel for lime execution output."""

    CSS = """
    VerticalScroll {
        scrollbar-size: 1 1;
    }
    #runs-container {
        height: auto;
    }
    #header-content {
        height: auto;
    }
    #status-line {
        height: auto;
    }
    #input-container {
        height: auto;
        display: none;
        padding: 0 1;
        border-top: solid $primary;
    }
    #input-prompt {
        height: auto;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("space", "toggle_auto_scroll", "Toggle Auto-scroll"),
    ]

    def __init__(
        self,
        build_display: Callable[[], Group],
        execution_model: ExecutionModel,
        writer: CliWriter | None = None,
    ) -> None:
        super().__init__()
        self._build_display = build_display
        self._execution_model = execution_model
        self._auto_scroll = True
        self._writer = writer
        self._widget_mode = writer is not None
        self._run_widgets: dict[int, RunWidget] = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        if self._widget_mode:
            with VerticalScroll(id="scroll"):
                yield Static(id="header-content")
                yield Vertical(id="runs-container")
                yield Static(id="status-line")
        else:
            with VerticalScroll(id="scroll"):
                yield ExecutionWidget(self._build_display)
        with Vertical(id="input-container"):
            yield Static(id="input-prompt")
            yield Input(id="input-field", placeholder="Type your answer and press Enter…")
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(0.12, self._poll)

    async def _poll(self) -> None:
        if self._widget_mode:
            await self._poll_widget_mode()
        else:
            widget = self.query_one(ExecutionWidget)
            widget.refresh_display()

        self._sync_input_widget()

        if self._auto_scroll:
            scroll = self.query_one("#scroll", VerticalScroll)
            scroll.scroll_end(animate=False)

    def _sync_input_widget(self) -> None:
        """Show or hide the input widget based on whether a pending input request exists."""
        pending = self._execution_model.pending_input
        container = self.query_one("#input-container", Vertical)
        if pending is not None and not container.display:
            self.query_one("#input-prompt", Static).update(f"[bold]{pending.prompt}[/bold]")
            container.display = True
            self.query_one("#input-field", Input).focus()
        elif pending is None and container.display:
            container.display = False

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Resolve a pending InputRequest when the user presses Enter."""
        pending = self._execution_model.pending_input
        if pending is None:
            return
        pending.response = event.value
        self.query_one("#input-field", Input).clear()
        pending.event.set()

    async def _poll_widget_mode(self) -> None:
        model = self._execution_model
        writer = self._writer

        # Update header section
        header_widget = self.query_one("#header-content", Static)
        header_widget.update(Group(*writer.build_header(model)))

        # Sync per-turn run widgets
        runs_container = self.query_one("#runs-container", Vertical)
        last_index = len(model.turns_with_runs) - 1
        for i, turn in enumerate(model.turns_with_runs):
            if turn.run is None:
                continue
            is_last = i == last_index
            if i not in self._run_widgets:
                widget = RunWidget(turn.run, i + 1, writer, is_last=is_last)
                widget._function_calls = turn.function_calls if is_last else []
                self._run_widgets[i] = widget
                await runs_container.mount(widget)
            else:
                fc = turn.function_calls if is_last else []
                self._run_widgets[i].update_run(turn.run, is_last=is_last, function_calls=fc)

        # Update status line
        status_widget = self.query_one("#status-line", Static)
        status = writer._build_status(model)
        status_widget.update(status or "")

    def action_toggle_auto_scroll(self) -> None:
        """Toggle auto-scroll on/off."""
        self._auto_scroll = not self._auto_scroll
        status = "enabled" if self._auto_scroll else "disabled"
        self.notify(f"Auto-scroll {status}")

    def on_key(self, event) -> None:
        """Disable auto-scroll when user uses arrow keys or page up/down."""
        if event.key in ("up", "down", "pageup", "pagedown", "home", "end"):
            self._auto_scroll = False
