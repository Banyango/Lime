import click

from app.agents.execute import execute
from app.prompts.commands import prompts


@click.group()
def cli():
    """Lime - A tool for executing .mgx files and managing agents."""
    pass


cli.add_command(execute)
cli.add_command(prompts)
