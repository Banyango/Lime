from abc import ABC, abstractmethod


class QueryService(ABC):
    @abstractmethod
    async def execute_query(self, prompt: str, tools: dict) -> str:
        """Execute the agent with the given context.

        Args:
            prompt (str): The context for the agent to execute.
            tools (dict): A dictionary of tools available to the agent.
        """
