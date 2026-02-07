from abc import ABC, abstractmethod


class AgentService(ABC):
    @abstractmethod
    async def execute_query(self, context: str, tools: dict) -> str:
        """
        Execute the agent with the given context.
        Args:
            context (str): The context for the agent to execute.
            tools (dict): A dictionary of tools available to the agent.
        """
