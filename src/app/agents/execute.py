import asyncio
from pathlib import Path

import click

from app.container import container
from app.lifecycle import with_lifecycle
from core.agents.models import ExecutionModel
from core.agents.plugins.context import ContextPlugin
from core.agents.plugins.func import FuncPlugin
from core.agents.plugins.tools import ToolsPlugin
from core.interfaces.ui import UI
from entities.context import Context
from core.agents.operations.execute_agent_operation import ExecuteAgentOperation
from core.agents.plugins.run_agent import RunAgentPlugin
from core.interfaces.query_service import QueryService
from entities.run import Run


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
    query_service = await container.get(QueryService)

    if not Path(file_name).is_file():
        print(f"File '{file_name}' does not exist.")
        return

    with open(file_name, "r") as f:
        mgx_code = f.read()

        model = ExecutionModel()

        operation = ExecuteAgentOperation(
            plugins=[
                RunAgentPlugin(agent_service=query_service),
                FuncPlugin(),
                ToolsPlugin(),
                ContextPlugin(),
            ],
            execution_model=model,
        )

        asyncio.create_task(ui.render_ui(model))

        await operation.execute_async(mgx_file=mgx_code, base_path=base_path)

        await asyncio.sleep(0.5)  # Allow time for UI to update with final results
