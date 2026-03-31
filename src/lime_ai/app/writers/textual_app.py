"""TextualApp for lime execution output."""

from __future__ import annotations

import sys
from pathlib import Path
from time import monotonic
from typing import TYPE_CHECKING

from rich.console import Group
from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.events import Click
from textual.message import Message
from textual.reactive import var
from textual.widgets import Footer, Header, Input, Static

from lime_ai.core.agents.models import ExecutionModel, PermissionPrompt
from lime_ai.entities.run import ContentBlockType, RunStatus

if TYPE_CHECKING:
    from lime_ai.app.writers.writer import CliWriter
    from lime_ai.entities.function import FunctionCall
    from lime_ai.entities.run import Run


# ── Status mappings ──────────────────────────────────────────────────────────

_STATUS_STYLE: dict[RunStatus, str] = {
    RunStatus.PENDING: "dim",
    RunStatus.RUNNING: "bold yellow",
    RunStatus.IDLE: "bold cyan",
    RunStatus.COMPLETED: "bold green",
    RunStatus.ERROR: "bold red",
}

_STATUS_ICON: dict[RunStatus, str] = {
    RunStatus.PENDING: "○",
    RunStatus.RUNNING: "◉",
    RunStatus.IDLE: "◎",
    RunStatus.COMPLETED: "●",
    RunStatus.ERROR: "✗",
}

_SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


# ── InputOverlay ─────────────────────────────────────────────────────────────


class InputOverlay(Vertical):
    """Prompt + text input shown when the execution model needs user input.

    Posts InputOverlay.Submitted on Enter so the parent app can resolve the
    pending InputRequest without coupling this widget to the execution model.
    """

    class Submitted(Message):
        def __init__(self, value: str) -> None:
            super().__init__()
            self.value = value

    def compose(self) -> ComposeResult:
        yield Static(id="input-prompt")
        yield Input(id="input-field", placeholder="Type your answer and press Enter…")

    def show(self, prompt: str) -> None:
        self.display = True
        self.query_one("#input-prompt", Static).update(f"❯  {prompt}")
        self.query_one("#input-field", Input).focus()

    def hide(self) -> None:
        self.display = False

    @on(Input.Submitted)
    def _on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self.post_message(self.Submitted(event.value))
        self.query_one("#input-field", Input).clear()


# ── PermissionOverlay ────────────────────────────────────────────────────────


class PermissionOverlay(Vertical):
    """Approve/deny overlay shown when the Copilot agent requests a permission.

    Posts PermissionOverlay.Resolved so the parent app can unblock the pending
    PermissionPrompt without coupling this widget to the execution model.
    """

    _KIND_LABELS = {
        "shell": "Shell command",
        "write": "File write",
        "read": "File read",
        "url": "URL access",
        "mcp": "MCP tool",
        "custom-tool": "Custom tool",
    }

    class Resolved(Message):
        def __init__(self, approved: bool) -> None:
            super().__init__()
            self.approved = approved

    def compose(self) -> ComposeResult:
        yield Static(id="perm-title")
        yield Static(id="perm-details")
        yield Static("  [bold green]a[/] Approve   [bold red]d[/] Deny", markup=True)

    def show(self, prompt: PermissionPrompt) -> None:
        self.display = True
        label = self._KIND_LABELS.get(prompt.kind, prompt.kind)
        self.query_one("#perm-title", Static).update(
            Text.from_markup(f"[bold yellow]⚠  Permission request:[/]  {label}")
        )
        detail_parts = [f"{k}: {v}" for k, v in prompt.details.items() if k != "kind"]
        details_text = "  " + "  ".join(detail_parts) if detail_parts else "  (no additional details)"
        self.query_one("#perm-details", Static).update(details_text)

    def hide(self) -> None:
        self.display = False


# ── RunHeader ─────────────────────────────────────────────────────────────────


class RunHeader(Static):
    """Clickable one-line summary for a RunWidget."""

    ALLOW_SELECT = False

    DEFAULT_CSS = """
    RunHeader {
        width: 1fr;
        height: auto;
    }
    """


# ── RunWidget ─────────────────────────────────────────────────────────────────


class RunWidget(Vertical):
    """A single execution turn: clickable header + collapsible content.

    Uses `var` with `toggle_class` so CSS can drive show/hide of the content
    area declaratively, while `_refresh_header` and `_refresh_content` keep
    the rendered Rich content up to date on every poll tick.
    """

    DEFAULT_CLASSES = "block"

    expanded: var[bool] = var(False, toggle_class="-expanded")

    def __init__(self, index: int, writer: CliWriter) -> None:
        super().__init__()
        self._index = index
        self._writer = writer
        self._run: Run | None = None
        self._function_calls: list[FunctionCall] = []
        self._user_toggled = False

    def compose(self) -> ComposeResult:
        yield RunHeader(id="run-header")
        yield Static(id="run-content")

    def on_mount(self) -> None:
        self._refresh_header()
        self._refresh_content()

    # -- Reactive watcher ----------------------------------------------------

    def watch_expanded(self, _: bool) -> None:
        self._refresh_header()
        self._refresh_content()

    # -- Public sync API -----------------------------------------------------

    def sync(self, run: Run, function_calls: list[FunctionCall], is_last: bool) -> None:
        """Called every poll tick with the latest data for this turn."""
        self._run = run
        self._function_calls = function_calls
        if not self._user_toggled:
            if self.expanded != is_last:
                self.expanded = is_last  # triggers watch_expanded
            else:
                self._refresh_header()
                self._refresh_content()
        else:
            self._refresh_header()
            self._refresh_content()

    # -- Event handlers ------------------------------------------------------

    @on(Click, "RunHeader")
    def _on_header_click(self, event: Click) -> None:
        event.stop()
        self._user_toggled = True
        self.expanded = not self.expanded

    # -- Rendering -----------------------------------------------------------

    def _refresh_header(self) -> None:
        if self._run is None:
            return
        try:
            header = self.query_one("#run-header", RunHeader)
        except Exception:
            return

        run = self._run
        chevron = "▼" if self.expanded else "▶"
        status_icon = _STATUS_ICON.get(run.status, "○")
        status_style = _STATUS_STYLE.get(run.status, "dim")

        t = Text()
        t.append(f" {chevron} ", style="dim")
        t.append(f"Run {self._index + 1}", style="bold")
        if run.model:
            t.append(f"  {run.model}", style="dim")
        t.append(f"  {status_icon} {run.status.value}", style=status_style)
        if run.duration_ms is not None:
            t.append(f"  {run.duration_ms / 1000:.1f}s", style="dim")
        if run.tokens.total_tokens > 0 and not self.expanded:
            t.append(f"  {run.tokens.total_tokens:,} tok", style="dim")
        if run.event_name and not self.expanded:
            t.append(f"  {run.event_name.value}", style="dim")
        if not self.expanded and run.status not in (RunStatus.RUNNING, RunStatus.PENDING):
            t.append("  (expand)", style="italic dim")

        header.update(t)

    def _refresh_content(self) -> None:
        if self._run is None or not self.expanded:
            return
        try:
            content = self.query_one("#run-content", Static)
        except Exception:
            return
        parts: list = []
        if self._function_calls:
            parts.extend(self._writer.render_function_calls(self._function_calls))
        parts.extend(self._writer.render_run(self._run, self._index + 1))
        content.update(Group(*parts) if parts else Text(""))


# ── LimeApp ──────────────────────────────────────────────────────────────────


class LimeApp(App):
    """Textual app for lime execution output."""

    CSS_PATH = (
        Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "app/writers/lime.tcss"
        if getattr(sys, "frozen", False)
        else Path(__file__).parent / "lime.tcss"
    )

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("space", "toggle_auto_scroll", "Auto-scroll"),
        Binding("p", "toggle_permissions", "Permissions"),
    ]

    def __init__(self, execution_model: ExecutionModel, writer: CliWriter) -> None:
        super().__init__()
        self._model = execution_model
        self._writer = writer
        self._auto_scroll = True
        self._run_widgets: dict[int, RunWidget] = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll(id="scroll"):
            yield Static(id="header-content")
            yield Vertical(id="runs-container")
            yield Static(id="status-line")
        yield PermissionOverlay(id="perm-overlay")
        yield InputOverlay(id="input-overlay")
        yield Footer()

    def on_mount(self) -> None:
        self.theme = self._writer.app_config.theme
        self.set_interval(0.016, self._poll)

    def watch_theme(self, theme: str) -> None:
        from lime_ai.app.config import save_app_config

        self._writer.app_config.theme = theme
        save_app_config(self._writer.app_config)

    # -- Poll loop -----------------------------------------------------------

    async def _poll(self) -> None:
        await self._sync_runs()
        self._sync_header()
        self._sync_status()
        self._sync_input()
        self._sync_permission()
        if self._auto_scroll:
            self.query_one("#scroll", VerticalScroll).scroll_end(animate=False)

    def _sync_header(self) -> None:
        renderables = self._writer.build_header(self._model)
        self.query_one("#header-content", Static).update(Group(*renderables))

    async def _sync_runs(self) -> None:
        turns = self._model.turns_with_runs
        last_idx = len(turns) - 1
        container = self.query_one("#runs-container", Vertical)

        for i, turn in enumerate(turns):
            if turn.run is None:
                continue
            is_last = i == last_idx
            fc = turn.function_calls if is_last else []

            if i not in self._run_widgets:
                widget = RunWidget(i, self._writer)
                self._run_widgets[i] = widget
                await container.mount(widget)

            self._run_widgets[i].sync(turn.run, fc, is_last)

    def _sync_status(self) -> None:
        model = self._model
        has_runs = model.turns and any(t.run for t in model.turns)
        if not has_runs:
            self.query_one("#status-line", Static).update("")
            return

        all_done = all(t.run and t.run.status in (RunStatus.COMPLETED, RunStatus.ERROR) for t in model.turns if t.run)
        if all_done:
            self._auto_scroll = False
            t = Text()
            t.append("● ", style="bold green")
            t.append("All turns completed  ", style="dim")
            t.append("q", style="bold")
            t.append(" to quit", style="dim")
            self.query_one("#status-line", Static).update(t)
        else:
            frame = _SPINNER_FRAMES[int(monotonic() * 10) % len(_SPINNER_FRAMES)]
            t = Text()
            t.append(f"{frame} ", style="green")
            t.append("Executing…", style="dim")

            run = model.current_run
            if run is not None:
                reasoning_blocks = [b for b in run.content_blocks if b.type == ContentBlockType.REASONING and b.text]
                if reasoning_blocks:
                    import re

                    latest = reasoning_blocks[-1].text
                    condensed = re.findall(r"\*\*(.+?)\*\*", latest)
                    snippet = condensed[-1] if condensed else latest
                    snippet = snippet.replace("\n", " ").strip()
                    if len(snippet) > 80:
                        snippet = snippet[:77] + "…"
                    t.append(f"  {snippet}", style="dim italic")

            self.query_one("#status-line", Static).update(t)

    def _sync_input(self) -> None:
        pending = self._model.pending_input
        overlay = self.query_one("#input-overlay", InputOverlay)
        if pending is not None and not overlay.display:
            overlay.show(pending.prompt)
        elif pending is None and overlay.display:
            overlay.hide()

    def _sync_permission(self) -> None:
        pending = self._model.pending_permission
        overlay = self.query_one("#perm-overlay", PermissionOverlay)
        if pending is not None and not overlay.display:
            overlay.show(pending)
        elif pending is None and overlay.display:
            overlay.hide()

    # -- Message handlers ----------------------------------------------------

    @on(PermissionOverlay.Resolved)
    def _on_permission_resolved(self, event: PermissionOverlay.Resolved) -> None:
        pending = self._model.pending_permission
        if pending is None:
            return
        pending.approved = event.approved
        pending.event.set()

    @on(InputOverlay.Submitted)
    def _on_input_submitted(self, event: InputOverlay.Submitted) -> None:
        pending = self._model.pending_input
        if pending is None:
            return
        pending.response = event.value
        pending.event.set()

    # -- Actions -------------------------------------------------------------

    def action_toggle_auto_scroll(self) -> None:
        self._auto_scroll = not self._auto_scroll
        self.notify(f"Auto-scroll {'on' if self._auto_scroll else 'off'}")

    def action_toggle_permissions(self) -> None:
        from lime_ai.app.config import save_app_config

        config = self._writer.app_config
        config.ignore_permissions = not config.ignore_permissions
        save_app_config(config)
        self.notify(f"Permission requests {'off' if config.ignore_permissions else 'on'}")

    def on_key(self, event) -> None:
        if event.key in ("up", "down", "pageup", "pagedown", "home", "end"):
            self._auto_scroll = False

        perm_overlay = self.query_one("#perm-overlay", PermissionOverlay)
        if perm_overlay.display:
            if event.key == "a":
                perm_overlay.post_message(PermissionOverlay.Resolved(approved=True))
                event.stop()
                return
            elif event.key == "d":
                perm_overlay.post_message(PermissionOverlay.Resolved(approved=False))
                event.stop()
                return
        # Intercept Shift+Enter when input overlay is visible to insert a newline
        try:
            key = getattr(event, "key", None)
            shift = getattr(event, "shift", False)
        except Exception:
            return

        if key == "enter" and shift:
            overlay = self.query_one("#input-overlay", InputOverlay)
            if overlay.display:
                event.stop()
                inp = self.query_one("#input-field", Input)
                current = getattr(inp, "value", "") or ""
                # Try to obtain cursor position; fallback to appending at end
                pos = getattr(inp, "cursor_position", None)
                if pos is None:
                    try:
                        pos = inp._cursor_position  # private fallback
                    except Exception:
                        pos = len(current)
                # Insert newline at cursor position
                new_val = current[:pos] + "\n" + current[pos:]
                inp.value = new_val
                # Move cursor after inserted newline if supported
                try:
                    inp.cursor_position = pos + 1
                except Exception:
                    try:
                        inp._cursor_position = pos + 1
                    except Exception:
                        pass
                inp.focus()
                return
