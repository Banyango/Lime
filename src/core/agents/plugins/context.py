from core.interfaces.agent_plugin import AgentPlugin
from entities.context import Context


class ContextPlugin(AgentPlugin):
    def __init__(self, context: Context):
        super().__init__()
        self.context = context

    def is_match(self, token: str) -> bool:
        """Determine if the plugin matches the given token.

        Args:
            token (str): The token to check.
        """
        return token == "context"

    async def handle(self, params: str):
        """Handle a request for the plugin.

        Args:
            params (str): The parameters for the request.
        """
        if params.lower() == "clear":
            self.context.clear()
