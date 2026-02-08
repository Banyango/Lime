from core.interfaces.agent_plugin import AgentPlugin
from core.interfaces.query_service import QueryService
from entities.context import Context


class RunAgentPlugin(AgentPlugin):
    def __init__(self, agent_service: QueryService, context: Context):
        super().__init__()
        self.agent_service = agent_service
        self.context = context

    def is_match(self, token: str) -> bool:
        """Determine if the plugin matches the given token.

        Args:
            token (str): The token to check.
        """
        return token == "run"

    async def handle(self, params: str, globals_dict: dict):
        """Handle a request for the plugin.

        Args:
            params (str): The parameters for the request.
            globals_dict (dict): The global variables available to the plugin.
        """
        await self.agent_service.execute_query(prompt=self.context.window, tools={})
