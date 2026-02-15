from core.agents.models import ExecutionModel
from core.interfaces.agent_plugin import AgentPlugin
from entities.context import Context


class ContextPlugin(AgentPlugin):
    def is_match(self, token: str) -> bool:
        """Determine if the plugin matches the given token.

        Args:
            token (str): The token to check.
        """
        return token == "context"

    async def handle(self, params: str, execution_model: ExecutionModel):
        """Handle a request for the plugin.

        Args:
            params (str): The parameters for the request.
            execution_model (ExecutionModel): The execution model for the current agent run.
        """
        if params.lower() == "clear":
            execution_model.context.clear_context()
