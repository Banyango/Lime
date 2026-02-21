from copilot import CopilotClient
from wireup import injectable


@injectable
class GithubCopilotClient:
    def __init__(self):
        self.con: CopilotClient | None = None

    async def connect(self):
        self.con = CopilotClient()
        await self.con.start()

    async def disconnect(self):
        if self.con:
            await self.con.stop()
