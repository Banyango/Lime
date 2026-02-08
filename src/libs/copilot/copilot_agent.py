from copilot import SessionConfig, MessageOptions
from copilot.generated.session_events import SessionEventType
from copilot.types import SystemMessageAppendConfig
from wireup import injectable

from core.interfaces.query_service import QueryService
from core.interfaces.ui import UI
from entities.context import Context
from libs.copilot.client import GithubCopilotClient
from libs.copilot.tools.get_variable_from_state import create_get_variable_tool
from libs.copilot.tools.set_variable_in_state import create_set_variable_tool


@injectable(as_type=QueryService)
class CopilotQuery(QueryService):
    def __init__(self, copilot_client: GithubCopilotClient, ui: UI, context: Context):
        self.ui = ui
        self.context = context
        self.client = copilot_client

    async def execute_query(self, prompt: str, tools: dict) -> str:
        """Execute a query using the Copilot client.

        Args:
            prompt (str): The prompt to send to the Copilot client.
            tools (dict): A dictionary of tools available to the agent.
        """
        if not self.client.con:
            raise Exception("Copilot client is not connected")

        get_var_tool = create_get_variable_tool(context=self.context)
        set_var_tool = create_set_variable_tool(context=self.context)

        session = await self.client.con.create_session(
            SessionConfig(
                system_message=SystemMessageAppendConfig(
                    content="""You are a coding agent, you have access to tools that allow you to set and 
                    get variables from a shared state. Use these tools to store and retrieve information as 
                    needed to complete your tasks."""
                ),
                model="gpt-5-mini",
                streaming=True,
                available_tools=["SetVariable", "GetVariable"],
                tools=[set_var_tool, get_var_tool],
            )
        )

        def handle_event(event):
            if event.type == SessionEventType.TOOL_USER_REQUESTED:
                self.ui.on_tool_requested(event.data.tool_name, event.data.tool_input)
            if event.type == SessionEventType.ASSISTANT_REASONING_DELTA:
                self.ui.on_reasoning_added(event.data.delta_content)
            if event.type == SessionEventType.ASSISTANT_MESSAGE_DELTA:
                self.ui.on_text_added(event.data.delta_content)
            if event.type == SessionEventType.SESSION_IDLE:
                self.ui.on_text_terminated()

        session.on(handle_event)

        response = await session.send_and_wait(MessageOptions(prompt=prompt))

        return response.data.content
