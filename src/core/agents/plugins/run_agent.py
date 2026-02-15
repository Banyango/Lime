from core.agents.models import ExecutionModel
from core.interfaces.agent_plugin import AgentPlugin
from core.interfaces.query_service import QueryService
from entities.context import Context
from entities.run import RunStatus


class RunAgentPlugin(AgentPlugin):
    def __init__(self, agent_service: QueryService):
        super().__init__()
        self.agent_service = agent_service

    def is_match(self, token: str) -> bool:
        """Determine if the plugin matches the given token.

        Args:
            token (str): The token to check.
        """
        return token == "run"

    async def handle(
        self, params: str, globals_dict: dict, execution_model: ExecutionModel
    ):
        """Handle a request for the plugin.

        Args:
            params (str): The parameters for the request.
            globals_dict (dict): The global variables available to the plugin.
            execution_model (ExecutionModel): The execution model for the current agent run.
        """
        await self.agent_service.execute_query(
            execution_model=execution_model
        )

        execution_model.start_turn()
