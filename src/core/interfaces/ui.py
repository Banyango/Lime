from abc import ABC, abstractmethod

from core.agents.models import ExecutionModel


class UI(ABC):
    @abstractmethod
    async def render_ui(self, execution_model: ExecutionModel):
        """Render the UI for the agent execution.

        Args:
            execution_model (ExecutionModel): The execution model for the current agent run.
        """
