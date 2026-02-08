from pathlib import Path

import click

from app.container import container
from app.lifecycle import with_lifecycle
from core.agents.plugins.context import ContextPlugin
from core.agents.plugins.func import FuncPlugin
from core.interfaces.ui import UI
from entities.context import Context
from core.agents.operations.execute_agent_operation import ExecuteAgentOperation
from core.agents.plugins.run_agent import RunAgentPlugin
from core.interfaces.query_service import QueryService


@click.command()
@click.option("--file-name", type=str, required=True)
@with_lifecycle
async def execute(file_name: str) -> None:
    """
    Executes an .mgx file.

    Args:
        file_name (str): The path to the .mgx file.
    """
    base_path = Path(file_name).parent

    ui = await container.get(UI)
    context = await container.get(Context)
    query_service = await container.get(QueryService)

    with open(file_name, "r") as f:
        mgx_code = f.read()

        operation = ExecuteAgentOperation(
            ui=ui,
            context=context,
            plugins=[
                RunAgentPlugin(agent_service=query_service, context=context),
                FuncPlugin(context=context, ui=ui),
                ContextPlugin(context=context),
            ],
        )

        result = await operation.execute_async(mgx_file=mgx_code, base_path=base_path)

        return result
