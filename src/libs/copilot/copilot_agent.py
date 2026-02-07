from copilot import SessionConfig, MessageOptions
from copilot.generated.session_events import SessionEventType
from wireup import injectable

from core.interfaces.agent_service import AgentService
from core.interfaces.ui import UI
from libs.copilot.client import GithubCopilotClient


@injectable(as_type=AgentService)
class CopilotAgent(AgentService):
    def __init__(self, copilot_client: GithubCopilotClient, ui: UI):
        self.client = copilot_client
        self.ui = ui

    async def execute_query(self, context: str, tools: dict) -> str:
        if not self.client.con:
            raise Exception("Copilot client is not connected")

        session = await self.client.con.create_session(
            SessionConfig(
                model="gpt-5-mini",
                streaming=True,
                tools=[]
            )
        )

        def handle_event(event):
            if event.type == SessionEventType.ASSISTANT_REASONING_DELTA:
                self.ui.on_reasoning_added(event.data.delta_content)
            if event.type == SessionEventType.ASSISTANT_MESSAGE_DELTA:
                self.ui.on_text_added(event.data.delta_content)
            if event.type == SessionEventType.SESSION_IDLE:
                self.ui.on_text_terminated()

        session.on(handle_event)

        response = await session.send_and_wait(MessageOptions(prompt=context))

        return response.data.content
