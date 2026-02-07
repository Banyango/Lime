from pathlib import Path

import click

from app.container import container
from app.lifecycle import with_lifecycle
from entities.context import Context
from core.agents.execute_agent_operation import ExecuteAgentOperation
from core.agents.plugins.run_agent import RunAgentPlugin
from core.interfaces.agent_service import QueryService


@click.command()
@click.option("--file-name", type=str, required=True)
@with_lifecycle
async def execute(file_name: str) -> None:
    """
    Executes an .mgx file.

    Args:
        file_name (str): The path to the .mgx file.
    """
    agent = await container.get(Context)

    with open(file_name, "r") as f:
        mgx_code = f.read()

        base_path = Path(file_name).parent
        query_service = await container.get(QueryService)
        operation = ExecuteAgentOperation(
            agent=agent,
            plugins=[RunAgentPlugin(agent_service=query_service, context=agent)],
        )

        result = await operation.execute_async(mgx_file=mgx_code, base_path=base_path)

        return result
