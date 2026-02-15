from abc import ABC, abstractmethod

from core.agents.models import ExecutionModel
from entities.run import Run


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
    async def handle(
        self, params: str, globals_dict: dict, execution_model: ExecutionModel
    ):
        """Handle a request for the plugin.

        Args:
            params (str): The parameters for the request.
            globals_dict (dict): The global variables available to the plugin.
            execution_model (ExecutionModel): The execution model for the current agent run.
        """
