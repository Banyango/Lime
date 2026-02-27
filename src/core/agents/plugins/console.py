from core.agents.models import ExecutionModel
from core.interfaces.agent_plugin import AgentPlugin
from entities.run import ContentBlock, ContentBlockType


class ConsolePlugin(AgentPlugin):
    def is_match(self, token: str) -> bool:
        """Determine if the plugin matches the given token.

        Args:
            token (str): The token to check.
        """
        return token == "console"

    async def handle(self, params: str, execution_model: ExecutionModel):
        """Handle a request for the plugin.

        Args:
            params (str): The parameters for the request.
            execution_model (ExecutionModel): The execution model for the current agent run.
        """
        final_string = execution_model.context.replace_variables_in_content(params)

        execution_model.current_run.content_blocks.append(
            ContentBlock(type=ContentBlockType.LOGGING, text=final_string)
        )
