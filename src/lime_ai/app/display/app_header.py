from typing import Any

from rich.rule import Rule
from rich.text import Text

from lime_ai.core.agents.models import ExecutionModel

LOGO = Text.from_ansi(
    "\033[32m _ _\n| (_)_ __ ___   ___\n| | | '_ ` _ \\ / _ \\\n| | | | | | | |  __/\n|_|_|_| |_| |_|\\___|\n\033[0m"
)

class AppHeader:
    @staticmethod
    def render(model: ExecutionModel) -> list:
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
