from collections.abc import Callable

from rich.console import Group
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widgets import Footer, Header, Static

from core.agents.models import ExecutionModel


class ExecutionWidget(Static):
    """Widget that renders the Rich Group from _build_display().

    Purpose
    - Render the composed Rich Group produced by the provided build_display callable inside a Textual Static widget.

    Public API
    - __init__(build_display: Callable[[], Group]) -> None: Initialize with a callable that returns a Rich Group.
    - on_mount() -> None: Mount hook that sets initial content.
    - refresh_display() -> None: Re-render the widget content from the build_display callable.

    Examples
    ```python
    def build_display() -> Group:
        return Group()

    widget = ExecutionWidget(build_display)
    widget.refresh_display()
    ```

    Notes
    - This widget delegates rendering to the provided callable and is intentionally lightweight.
    """

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
    """Textual app with a scrollable panel for lime execution output.

    Purpose
    - Provide a small Textual application UI that displays Lime execution output in a scrollable panel.

    Public API
    - __init__(build_display: Callable[[], Group], execution_model: ExecutionModel) -> None:
        Configure UI with display builder and execution model.
    - compose() -> ComposeResult: Build the Textual layout (Header, VerticalScroll with ExecutionWidget, Footer).
    - action_toggle_auto_scroll() -> None: Toggle automatic scrolling behavior.

    Examples
    ```python
    app = LimeApp(build_display=my_builder, execution_model=my_model)
    app.run()
    ```

    Notes
    - Auto-scroll is toggled off when the user navigates with keyboard keys; the polling interval is small for
     near-real-time updates.
    """

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


    def action_toggle_auto_scroll(self) -> None:
        """Toggle auto-scroll on/off."""
        self._auto_scroll = not self._auto_scroll
        status = "enabled" if self._auto_scroll else "disabled"
        self.notify(f"Auto-scroll {status}")

    def on_key(self, event) -> None:
        """Disable auto-scroll when user uses arrow keys or page up/down."""
        if event.key in ("up", "down", "pageup", "pagedown", "home", "end"):
            self._auto_scroll = False
