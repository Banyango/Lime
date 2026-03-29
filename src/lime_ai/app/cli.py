import click

from lime_ai.app.agents.execute import execute
from lime_ai.app.prompts.commands import prompts


@click.group()
def cli():
    """Lime - A tool for executing .mgx files and managing agents."""
    pass


cli.add_command(execute)
cli.add_command(prompts)
