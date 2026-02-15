import asyncio
import re
from typing import Any

from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax
from rich.text import Text
from rich.table import Table
from wireup import injectable

from core.agents.models import ExecutionModel
from core.interfaces.ui import UI
from entities.function import FunctionCall
from entities.run import Run, RunStatus, ContentBlockType, ToolCall


@injectable(as_type=UI)
class CliWriter(UI):
    async def render_ui(self, execution_model: ExecutionModel):
        console = Console()

        with Live(console=console, auto_refresh=False, vertical_overflow="visible") as live:
            while True:
                live.update(self._build_display(execution_model))
                live.refresh()

                all_done = execution_model.turns and all(
                    r.run and r.run.status in (RunStatus.COMPLETED, RunStatus.ERROR)
                    for r in execution_model.turns
                )
                if all_done:
                    break

                await asyncio.sleep(0.12)

    LOGO = Text.from_ansi(
        "\033[32m"
        " _ _\n"
        "| (_)_ __ ___   ___\n"
        "| | | '_ ` _ \\ / _ \\\n"
        "| | | | | | | |  __/\n"
        "|_|_|_| |_| |_|\\___|\n"
        "\033[0m"
    )

    def _build_display(self, model: ExecutionModel) -> Group:
        renderables: list[Any] = [self.LOGO]

        if model.import_errors:
            renderables.append(Rule("Import Errors", style="red"))
            for err in model.import_errors:
                renderables.append(Text(str(err), style="red"))
            renderables.append(Rule(style="red"))
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

        renderables.append(Text("Executing...", style="dim green"))
        renderables.append(Text())

        for i, turn in enumerate(model.turns):
            renderables.extend(self._render_function_calls(turn.function_calls))

            if turn.run:
                renderables.extend(self._render_run(turn.run, i + 1))

        return Group(*renderables) if renderables else Group(Text("Waiting..."))

    def _render_run(self, run: Run, index: int) -> list:
        parts = []

        # Run header
        status_style = {
            RunStatus.PENDING: "dim",
            RunStatus.RUNNING: "bold yellow",
            RunStatus.IDLE: "bold blue",
            RunStatus.COMPLETED: "bold green",
            RunStatus.ERROR: "bold red",
        }.get(run.status if run else RunStatus.PENDING, "dim")

        header = Text()
        header.append(f"Run {index}", style="bold")
        if run.model:
            header.append(f"  {run.model}", style="dim")
        header.append(f"  [{run.status.value}]", style=status_style)
        if run.duration_ms is not None:
            header.append(f"  {run.duration_ms / 1000:.1f}s", style="dim")
        parts.append(header)

        # Build tool call lookup by ID
        tool_call_map = {tc.tool_call_id: tc for tc in run.tool_calls}

        # Content blocks (interleaved chronologically)
        for block in run.content_blocks:
            if block.type == ContentBlockType.REASONING:
                if not block.text:
                    continue
                condensed_reasoning = re.findall(r'\*\*(.+?)\*\*', block.text)
                parts.append(
                    Panel(
                        Text("\n".join(condensed_reasoning) if condensed_reasoning else block.text, style="dim"),
                        title="Reasoning",
                        border_style="dim",
                        expand=False,
                    )
                )
            elif block.type == ContentBlockType.RESPONSE:
                if not block.text:
                    continue
                try:
                    parts.append(Markdown(block.text))
                except Exception:
                    parts.append(Text(block.text))
            elif block.type == ContentBlockType.TOOL_CALL:
                tc = tool_call_map.get(block.ref)
                if tc:
                    parts.append(self._render_tool_call(tc))

        # Errors
        for err in run.errors:
            parts.append(
                Panel(
                    Text(err.message, style="red"),
                    title=f"Error{f' ({err.error_type})' if err.error_type else ''}",
                    border_style="red",
                    expand=False,
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

        parts.append(Text())
        return parts

    @staticmethod
    def _render_tool_call(tc: ToolCall) -> Panel:
        import json

        tool_text = Text()
        if tc.success is None:
            tool_text.append("~ ", style="yellow")
        elif tc.success:
            tool_text.append("+ ", style="green")
        else:
            tool_text.append("x ", style="red")
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

        return Panel(Group(*tool_parts), border_style="dim", expand=False)

    def _render_function_calls(self, function_calls: list[FunctionCall]) -> list:
        return [
            Panel(
                Group(
                    Text(fc.method, style="bold blue"),
                    Syntax(fc.params, "python", theme="monokai", line_numbers=False),
                    Text(fc.result[0:150], style="dim")
                ),
                title="Function Call",
                border_style="blue",
                expand=False,
            )
            for fc in function_calls
        ]

