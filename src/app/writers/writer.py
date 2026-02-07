from typing import Literal

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from wireup import injectable

from core.interfaces.ui import UI


@injectable(as_type=UI)
class CliWriter(UI):
    def __init__(self):
        # Console instance used by various render helpers and Live
        self.console = Console(width=12)
        self.current_index = 0
        self.output_text = [""]
        self.current_reasoning_index = 0
        self.reasoning_text = [""]
        self.in_reason_block = False
        self.in_response_block = False

    def _set_heading(self, type: Literal["response","reasoning"]):
        if type == "response":
            if not self.in_response_block:
                self.console.print()
                self.console.rule("[bold white]Response")
                self.in_response_block = True
                self.in_reason_block = False

        elif type == "reasoning":
            if not self.in_reason_block:
                self.console.print()
                self.console.rule("[bold white]Reasoning")
                self.in_reason_block = True
                self.in_response_block = False


    def on_text_added(self, text: str):
        self._set_heading("response")
        self.console.print(text, end="", overflow="fold", style="bold green")

    def on_text_terminated(self):
        self.console.print("")
        self.in_reason_block = False
        self.in_response_block = False

    def on_reasoning_added(self, text: str):
        self._set_heading("reasoning")
        self.console.print(text, end="", overflow="fold", style="bold yellow")

    def on_reasoning_terminated(self):
        self.console.print("")


    def render_code(self, code: str, language: str = "python", filepath: str = None, theme: str = "monokai"):
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
            padding=0
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
        styles = {
            1: "bold cyan",
            2: "bold blue",
            3: "bold"
        }
        style = styles.get(level, "bold")
        self.console.print(f"\n{text}", style=style)

    def clear(self):
        """Clear the console"""
        self.console.clear()
