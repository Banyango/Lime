from abc import ABC, abstractmethod

from core.agents.agent import Agent


class AgentPlugin(ABC):
    def __init__(self):
        self.agent = None

    @abstractmethod
    def is_match(self, token: str) -> bool:
        """
        Determine if the plugin matches the given token.

        Args:
            token (str): The token to check.

        Returns:
            bool: True if the plugin matches, False otherwise.
        """

    @abstractmethod
    async def handle(self, params: str):
        """
        Handle a request for the plugin.

        Args:
            params (str): The parameters for the request.
        """

    def set_agent(self, agent: Agent):
        """Set the agent for the plugin.

        Args:
            agent (Agent): The agent to set for the plugin.
        """
        self.agent = agent
