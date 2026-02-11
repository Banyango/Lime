from typing import Literal

from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.text import Text
from wireup import injectable

from core.interfaces.ui import UI


@injectable(as_type=UI)
class CliWriter(UI):
    def __init__(self):
        # Console instance used by various render helpers and Live
        self.console = Console(color_system="truecolor", force_terminal=True)

        # Accumulated text buffers
        self.response_buffer = ""
        self.reasoning_buffer = ""

        # State tracking
        self.in_reason_block = False
        self.in_response_block = False
        self.live_display = None
        self.static_content = []  # Content that's been finalized
        self.reasoning_progress = Progress(
            SpinnerColumn(),
            TextColumn(""),
            console=self.console,
            transient=True,
        )


    def _start_live_display(self):
        """Start or ensure live display is running."""
        if self.live_display is None:
            self.live_display = Live(
                console=self.console,
                refresh_per_second=50,
                auto_refresh=True,
                transient=False
            )
            self.live_display.start()

    def _stop_live_display(self):
        """Stop the live display and finalize content."""
        if self.live_display is not None:
            self.live_display.stop()
            self.live_display = None

    def _render_accumulated_content(self):
        """Render all accumulated content."""
        renderables = []

        # Add reasoning section if there's content
        if self.reasoning_buffer:
            buffer = self.reasoning_buffer.split("**")
            dots = ""
            dots = dots + "." * (len(self.reasoning_buffer) % 5)
            renderables.append(Text(buffer[1]+dots if len(buffer) > 1 else "", style="italic yellow"))

        # Add response section if there's content
        if self.response_buffer:
            renderables.append(Text("─" * self.console.width, style="grey"))
            renderables.append(Text("Response", style="grey"))
            renderables.append(Text("─" * self.console.width, style="grey"))
            renderables.append(Markdown(self.response_buffer))

        if renderables and self.live_display:
            self.live_display.update(Group(*renderables))

    def _set_heading(self, type: Literal["response", "reasoning"]):
        if type == "response":
            if not self.in_response_block:
                self._start_live_display()
                self.in_response_block = True
                self.in_reason_block = False

        elif type == "reasoning":
            if not self.in_reason_block:
                self._start_live_display()
                self.in_reason_block = True
                self.in_response_block = False

    def on_text_added(self, text: str):
        self._set_heading("response")
        self.response_buffer += text
        self._render_accumulated_content()

    def on_agent_execution_start(self):
        self.console.rule(f"Starting execution of .mgx file", style="dim italic")

    def on_run_function(self, method_value):
        self.console.print(f"Running function: {method_value}", end="", style="bold magenta")

    def on_parse_complete(self, metadata: dict):
        self.console.print("Parsing completed...", style="bold green")
        self.console.rule("Metadata", style="dim italic")
        for key, value in metadata.items():
            self.console.print(f"[bold]{key}:[/bold] {value}", style="bold blue")
        self.console.rule(style="dim italic")

    def on_text_terminated(self):
        self._stop_live_display()
        self.in_reason_block = False
        self.in_response_block = False
        self.response_buffer = ""
        self.response_buffer = ""
        self.console.print("")  # Add spacing after completion

    def on_reasoning_added(self, text: str):
        self._set_heading("reasoning")
        self.reasoning_buffer += text
        self._render_accumulated_content()

    def on_reasoning_terminated(self):
        self.console.print("")

    def on_function_complete(self, result: str):
        self.console.print(" (complete)", style="bold white")

    def on_tool_requested(self, tool_name: str, tool_input: str):
        self.console.print()
        self.console.rule(f"[bold white]Tool Requested: {tool_name}")
        self.console.print(tool_input, style="dim")
        self.console.print()

    def render_code(
        self,
        code: str,
        language: str = "python",
        filepath: str = None,
        theme: str = "monokai",
    ):
        """Render code block with syntax highlighting similar to Claude"""
        if filepath:
            # Display file path header
            header = Text()
            header.append("// ", style="dim")
            header.append(f"filepath: {filepath}", style="dim italic")
            self.console.print(header)

        # Render syntax highlighted code
        syntax = Syntax(
            code,
            language,
            theme=theme,
            line_numbers=False,
            word_wrap=False,
            background_color="default",
            padding=0,
        )
        self.console.print(syntax)
        self.console.print()  # Add spacing

    def render_markdown(self, markdown_text: str):
        """Render markdown text"""
        md = Markdown(markdown_text)
        self.console.print(md)

    def render_panel(self, content: str, title: str = None, border_style: str = "blue"):
        """Render content in a bordered panel"""
        panel = Panel(content, title=title, border_style=border_style, padding=(1, 2))
        self.console.print(panel)

    def render_text(self, text: str, style: str = None):
        """Render styled text"""
        self.console.print(text, style=style)

    def render_divider(self, char: str = "─"):
        """Render a horizontal divider"""
        width = self.console.width
        self.console.print(char * width, style="dim")

    def render_header(self, text: str, level: int = 1):
        """Render a header with appropriate styling"""
        styles = {1: "bold cyan", 2: "bold blue", 3: "bold"}
        style = styles.get(level, "bold")
        self.console.print(f"\n{text}", style=style)

    def clear(self):
        """Clear the console"""
        self.console.clear()
