from abc import ABC, abstractmethod

from core.agents.models import ExecutionModel


class QueryService(ABC):
    @abstractmethod
    async def execute_query(self, execution_model: ExecutionModel) -> str:
        """Execute the agent with the given context.

        Args:
            execution_model (ExecutionModel): The execution model for the current agent run.
        """
