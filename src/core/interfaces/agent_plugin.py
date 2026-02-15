from abc import ABC, abstractmethod

from core.agents.models import ExecutionModel


class AgentPlugin(ABC):
    @abstractmethod
    def is_match(self, token: str) -> bool:
        """Determine if the plugin matches the given token.

        Args:
            token (str): The token to check.

        Returns:
            bool: True if the plugin matches, False otherwise.
        """

    @abstractmethod
    async def handle(self, params: str, execution_model: ExecutionModel):
        """Handle a request for the plugin.

        Args:
            params (str): The parameters for the request.
            execution_model (ExecutionModel): The execution model for the current agent run.
        """
