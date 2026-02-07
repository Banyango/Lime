import click

from app.agents.execute import execute


@click.group()
def cli():
    """Lime - A tool for executing .mgx files and managing agents."""
    pass


cli.add_command(execute)
