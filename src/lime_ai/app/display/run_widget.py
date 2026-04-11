from __future__ import annotations

from rich.console import Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.events import Click
from textual.message import Message
from textual.widgets import Static

from lime_ai.app.display.run_header import RunHeader
from lime_ai.app.display.status_constants import STATUS_ICON, STATUS_STYLE, SUB_RUN_PALETTE, NUM_SUB_COLORS
from lime_ai.entities.function import FunctionCall
from lime_ai.entities.run import ContentBlockType, RunStatus, ToolCall, ContentBlock
from lime_ai.entities.run import Run



class RunWidget(Vertical):
    """A single execution turn: clickable header + collapsible content."""

    DEFAULT_CLASSES = "block"

    class CollapseChanged(Message):
        """Posted when the user explicitly collapses or expands a parent (non-sub) run."""

        def __init__(self, widget: RunWidget, expanded: bool) -> None:
            super().__init__()
            self.run_widget = widget
            self.expanded = expanded

    def __init__(self, index: int) -> None:
        super().__init__()
        self._index = index
        self._run: Run | None = None
        self._header_fp: tuple | None = None
        self._content_fp: tuple | None = None
        self._tool_call_cache: dict = {}

    def compose(self) -> ComposeResult:
        yield RunHeader(id="run-header")
        yield Static(id="run-content")

    def on_mount(self) -> None:
        self._refresh_header()
        self._refresh_content()

    def sync(self, run: Run) -> None:
        """Called every poll tick with the latest data for this turn."""
        self._run = run
        self.set_class(run.is_sub_run, "-sub-run")
        self.set_class(run.is_expanded, "-expanded")

        if run.is_sub_run:
            color_idx = self._index % NUM_SUB_COLORS
            for i in range(NUM_SUB_COLORS):
                self.set_class(i == color_idx, f"-sub-color-{i}")

        self._refresh_header()
        self._refresh_content()

    @on(Click, "RunHeader")
    def _on_header_click(self, event: Click) -> None:
        event.stop()
        self._run.on_expanded()
        self.set_class(self._run.is_expanded, "-expanded")
        self._content_fp = None
        self._header_fp = None
        self._refresh_header()
        self._refresh_content()
        if not self._run.is_sub_run:
            self.post_message(self.CollapseChanged(self, self._run.is_expanded))

    def _refresh_header(self) -> None:
        if self._run is None:
            return
        run = self._run
        fp = (run.status, run.duration_ms, run.tokens.total_tokens, run.model, run.event_name, run.title, run.is_sub_run, run.is_expanded)
        if fp == self._header_fp:
            return
        self._header_fp = fp
        try:
            header = self.query_one("#run-header", RunHeader)
        except Exception:
            return
        chevron = "▼" if run.is_expanded else "▶"
        status_icon = STATUS_ICON.get(run.status, "○")
        status_style = STATUS_STYLE.get(run.status, "dim")

        t = Text()
        t.append(f" {chevron} ", style="dim")
        if run.is_sub_run:
            color = SUB_RUN_PALETTE[self._index % NUM_SUB_COLORS]
            t.append("Sub Run", style=f"bold {color}")
            if run.title:
                t.append(f"  {run.title}", style=f"dim {color}")
        else:
            t.append(f"Run {self._index + 1}", style="bold")
            if run.title:
                t.append(f"  {run.title}", style="dim cyan")
        if run.model:
            t.append(f"  {run.model}", style="dim")
        t.append(f"  {status_icon} {run.status.value}", style=status_style)
        if run.duration_ms is not None:
            t.append(f"  {run.duration_ms / 1000:.1f}s", style="dim")
        if run.tokens.total_tokens > 0 and not self._run.is_expanded:
            t.append(f"  {run.tokens.total_tokens:,} tok", style="dim")
        if run.event_name and not self._run.is_expanded:
            t.append(f"  {run.event_name.value}", style="dim")
        if not self._run.is_expanded and run.status not in (RunStatus.RUNNING, RunStatus.PENDING):
            t.append("  (expand)", style="italic dim")

        header.update(t)

    def _refresh_content(self) -> None:
        if self._run is None or not self._run.is_expanded:
            return
        run = self._run
        last_text_len = len(run.content_blocks[-1].text) if run.content_blocks else 0
        completed_tool_calls = sum(1 for tc in run.tool_calls if tc.success is not None)
        fp = (len(run.content_blocks), len(run.tool_calls), run.status, last_text_len, completed_tool_calls)
        if fp == self._content_fp:
            return
        self._content_fp = fp
        try:
            content = self.query_one("#run-content", Static)
        except Exception:
            return
        parts: list = []
        parts.extend(self.render_run(self._run))
        content.update(Group(*parts) if parts else Text(""))

    def render_run(self, run: Run) -> list:
        parts = []

        if run.provider != "local":
            parts.append(Text("Prompt:", style="bold blue"))
            parts.append(Text(run.prompt, style="dim"))

        tool_call_map = {tc.tool_call_id: tc for tc in run.tool_calls}

        for block in run.content_blocks:
            if block.type == ContentBlockType.REASONING:
                continue
            elif block.type == ContentBlockType.RESPONSE:
                if not block.text:
                    continue
                parts.append(Text("Response:", style="bold blue"))
                try:
                    parts.append(Markdown(block.text))
                except Exception:
                    parts.append(Text(block.text))
            elif block.type == ContentBlockType.TOOL_CALL:
                tc = tool_call_map.get(block.ref)
                if tc:
                    parts.append(self._get_or_render_tool_call(tc))
            elif block.type == ContentBlockType.INPUT:
                parts.append(self._render_input(block))
            elif block.type == ContentBlockType.LOGGING:
                if not block.text:
                    continue
                parts.append(Text(f"[INFO] {block.text}", style="cyan dim"))

        # Errors
        for err in run.errors:
            parts.append(
                Panel(
                    Text(err.message, style="red"),
                    title=f"Error{f' ({err.error_type})' if err.error_type else ''}",
                    border_style="red",
                    expand=True,
                )
            )

        # Usage summary (only when run is done)
        if run.status == RunStatus.COMPLETED and run.tokens.total_tokens > 0:
            usage = Table.grid(padding=(0, 2))
            usage.add_row(
                Text("Tokens:", style="dim"),
                Text(f"{run.tokens.input_tokens:,} in", style="dim"),
                Text(f"{run.tokens.output_tokens:,} out", style="dim"),
            )
            if run.request_count > 0:
                usage.add_row(
                    Text("Requests:", style="dim"),
                    Text(str(run.request_count), style="dim"),
                )
            parts.append(usage)

        # Code changes
        if run.code_changes:
            cc = run.code_changes
            changes_text = Text()
            changes_text.append(f"{len(cc.files_modified)} files", style="dim")
            changes_text.append(f"  +{cc.lines_added}", style="green")
            changes_text.append(f"  -{cc.lines_removed}", style="red")
            parts.append(changes_text)

        return parts

    def _get_or_render_tool_call(self, tc: ToolCall) -> Panel:
        if tc.success is not None:
            cached = self._tool_call_cache.get(tc.tool_call_id)
            if cached is not None:
                return cached
            rendered = self._render_tool_call(tc)
            self._tool_call_cache[tc.tool_call_id] = rendered
            return rendered
        return self._render_tool_call(tc)

    @staticmethod
    def _render_tool_call(tc: ToolCall) -> Panel:
        import json

        if tc.success is None:
            status_icon, status_style, border_style = "⌛", "yellow", "yellow dim"
        elif tc.success:
            status_icon, status_style, border_style = "✔", "green", "green dim"
        else:
            status_icon, status_style, border_style = "✗", "red", "red dim"

        tool_text = Text()
        tool_text.append(f"{status_icon} ", style=status_style)
        tool_text.append(tc.tool_name, style="bold")
        if tc.duration_ms is not None:
            tool_text.append(f"  {tc.duration_ms:.0f}ms", style="dim")

        tool_parts = [tool_text]

        if tc.arguments:
            try:
                args_str = json.dumps(tc.arguments, indent=2)
                tool_parts.append(Syntax(args_str, "json", theme="monokai", line_numbers=False))
            except (TypeError, ValueError):
                tool_parts.append(Text(str(tc.arguments), style="dim"))

        if tc.result:
            tool_parts.append(Text(tc.result, style="dim"))

        return Panel(Group(*tool_parts), border_style=border_style, expand=True, padding=(0, 1))

    @staticmethod
    def _render_input(tc: ContentBlock) -> Panel:
        return Panel(Group(Markdown(tc.text)), border_style="dim", expand=True)

    def render_function_calls(self, function_calls: list[FunctionCall]) -> list:
        return [
            Panel(
                Group(
                    Text("❯  " + fc.method, style="bold cyan"),
                    Syntax(fc.params, "python", theme="monokai", line_numbers=False),
                    Text((fc.result or "")[0:150], style="dim"),
                ),
                title="fn",
                border_style="cyan dim",
                expand=True,
                padding=(0, 1),
            )
            for fc in function_calls
        ]
