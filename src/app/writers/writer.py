import re
from typing import Any

from rich.console import Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from wireup import injectable

from app.config import AppConfig
from app.writers.textual_app import LimeApp
from core.agents.models import ExecutionModel
from core.interfaces.ui import UI
from entities.function import FunctionCall
from entities.run import ContentBlock, ContentBlockType, Run, RunStatus, ToolCall

LOGO = Text.from_ansi(
    "\033[32m _ _\n| (_)_ __ ___   ___\n| | | '_ ` _ \\ / _ \\\n| | | | | | | |  __/\n|_|_|_| |_| |_|\\___|\n\033[0m"
)


@injectable(as_type=UI)
class CliWriter(UI):
    def __init__(self, app_config: AppConfig):
        self.app_config = app_config

    async def render_ui(self, execution_model: ExecutionModel):
        app = LimeApp(execution_model=execution_model, writer=self)
        await app.run_async()

    def build_header(self, model: ExecutionModel) -> list:
        """Return renderables for the static header section (logo, errors, warnings, metadata)."""
        renderables: list[Any] = [LOGO]
        if model.import_errors:
            renderables.append(Rule("Import Errors", style="red"))
            for err in model.import_errors:
                renderables.append(Text(str(err), style="red"))
            renderables.append(Rule(style="red"))
            renderables.append(Text())

        if model.warnings:
            renderables.append(Rule("Warnings", style="yellow"))
            for warning in model.warnings:
                renderables.append(Text(str(warning), style="yellow"))
            renderables.append(Rule(style="yellow"))
            renderables.append(Text())

        if model.header:
            renderables.append(Text(model.header, style="bold cyan"))
            renderables.append(Text())

        if model.metadata:
            renderables.append(Rule("Metadata", style="dim cyan"))
            for key, value in model.metadata.items():
                renderables.append(Text(f"{key}: {value}", style="dim"))
            renderables.append(Rule(style="dim cyan"))
            renderables.append(Text())

        if model.memory and model.memory.get_items():
            renderables.append(Rule("Memory", style="dim magenta"))
            for key, value in model.memory.get_items().items():
                renderables.append(Text(f"{key}: {value}", style="dim"))
            renderables.append(Rule(style="dim magenta"))
            renderables.append(Text())

        return renderables

    @staticmethod
    def _build_status(model: ExecutionModel) -> Text | None:
        """Return a status Text for the footer line, or None when there are no runs."""
        has_runs = model.turns and any(t.run for t in model.turns)
        if not has_runs:
            return None

        all_turns_complete = all(
            t.run and t.run.status in (RunStatus.COMPLETED, RunStatus.ERROR) for t in model.turns if t.run
        )
        if all_turns_complete:
            return Text("All turns completed. (press q to quit)", style="bold green")
        return Text("Executing...", style="dim green")

    def render_run(self, run: Run, index: int) -> list:
        parts = []

        if self.app_config.show_context and run.provider != "local":
            parts.append(Text("Prompt:", style="bold blue"))
            parts.append(Text(run.prompt, style="dim"))

        # Build tool call lookup by ID
        tool_call_map = {tc.tool_call_id: tc for tc in run.tool_calls}

        # Content blocks (interleaved chronologically)
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
                    parts.append(self._render_tool_call(tc))
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
            if run.total_cost > 0:
                usage.add_row(
                    Text("Cost:", style="dim"),
                    Text(f"${run.total_cost:.4f}", style="dim"),
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
