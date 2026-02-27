from copilot import CopilotClient, SessionConfig, CopilotSession
from wireup import injectable


@injectable
class GithubCopilotClient:
    """Wrapper around the GitHub Copilot SDK client used by the adapter.

    Provides convenience methods for opening sessions, sending events, and
    translating SDK errors into the project's error types.
    """
    def __init__(self):
        self.con: CopilotClient | None = None
        self.session: CopilotSession | None = None

    async def connect(self):
        self.con = CopilotClient()
        await self.con.start()

    async def disconnect(self):
        if self.con:
            await self.con.stop()

    async def create_session(self, session_config: SessionConfig):
        if not self.con:
            raise RuntimeError("Copilot client is not connected")

        self.session = await self.con.create_session(session_config)

    async def destroy_current_session(self):
        if not self.con:
            raise RuntimeError("Copilot client is not connected")

        await self.session.destroy()
        self.session = None

