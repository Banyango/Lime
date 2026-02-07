from pathlib import Path

import click
from rich.live import Live

from app.container import container
from app.lifecycle import with_lifecycle
from core.agents.agent import Agent
from core.agents.execute_agent_operation import ExecuteAgentOperation
from core.agents.plugins.run_agent import RunAgentPlugin
from core.interfaces.agent_service import AgentService
from core.interfaces.ui import UI


@click.command()
@click.option("--file-name", type=str, required=True)
@with_lifecycle
async def execute(file_name: str) -> None:
    """
    Executes an .mgx file.

    Args:
        file_name (str): The path to the .mgx file.
    """
    with open(file_name, "r") as f:
        mgx_code = f.read()

        base_path = Path(file_name).parent
        agent_service = await container.get(AgentService)
        operation = ExecuteAgentOperation(
            agent=Agent(agent_service=agent_service), plugins=[RunAgentPlugin()]
        )

        result = await operation.execute_async(mgx_file=mgx_code, base_path=base_path)

        return result
