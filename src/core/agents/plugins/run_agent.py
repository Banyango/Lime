from core.agents.agent_plugin import AgentPlugin
from core.interfaces.agent_service import QueryService
from entities.context import Context


class RunAgentPlugin(AgentPlugin):
    def __init__(self, agent_service: QueryService, context: Context):
        super().__init__()
        self.agent_service = agent_service
        self.context = context

    def is_match(self, token: str) -> bool:
        return token == "run"

    async def handle(self, params: str):
        await self.agent_service.execute_query(prompt=self.context.window, tools={})
