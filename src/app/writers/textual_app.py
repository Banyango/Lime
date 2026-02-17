from typing import Callable

from rich.console import Group
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widgets import Footer, Header, Static

from core.agents.models import ExecutionModel
from entities.run import RunStatus


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


class LimeApp(App):
    """Textual app with a scrollable panel for lime execution output."""

    CSS = """
    VerticalScroll {
        scrollbar-size: 1 1;
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
    ) -> None:
        super().__init__()
        self._build_display = build_display
        self._execution_model = execution_model
        self._auto_scroll = True

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll(id="scroll"):
            yield ExecutionWidget(self._build_display)
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(0.12, self._poll)

    def _poll(self) -> None:
        widget = self.query_one(ExecutionWidget)
        widget.refresh_display()

        if self._auto_scroll:
            scroll = self.query_one("#scroll", VerticalScroll)
            scroll.scroll_end(animate=False)

        all_done = self._execution_model.turns and all(
            t.run and t.run.status in (RunStatus.COMPLETED, RunStatus.ERROR)
            for t in self._execution_model.turns
        )
        if all_done:
            self.set_timer(0.5, self._exit)

    def _exit(self) -> None:
        self.exit()

    def action_toggle_auto_scroll(self) -> None:
        """Toggle auto-scroll on/off."""
        self._auto_scroll = not self._auto_scroll
        status = "enabled" if self._auto_scroll else "disabled"
        self.notify(f"Auto-scroll {status}")

    def on_key(self, event) -> None:
        """Disable auto-scroll when user uses arrow keys or page up/down."""
        if event.key in ("up", "down", "pageup", "pagedown", "home", "end"):
            self._auto_scroll = False

