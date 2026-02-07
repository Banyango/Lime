from core.agents.agent_plugin import AgentPlugin


class RunAgentPlugin(AgentPlugin):
    def is_match(self, token: str) -> bool:
        return token == "run"

    async def handle(self, params: str):
        await self.agent.run_current_context()
