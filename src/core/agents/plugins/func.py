import re

from core.interfaces.agent_plugin import AgentPlugin
from core.interfaces.ui import UI
from entities.context import Context


class FuncPlugin(AgentPlugin):
    def __init__(self, context: Context, ui: UI):
        super().__init__()
        self.context = context
        self.ui = ui

    def is_match(self, token: str) -> bool:
        """Determine if the plugin matches the given token.

        Args:
            token (str): The token to check.
        """
        return token == "func"

    async def handle(self, params: str, globals_dict: dict):
        """Handle a request for the plugin.

        Args:
            params (str): The parameters for the request.
            globals_dict (dict): The global variables available to the plugin.
        """
        params = params.strip()

        result = re.match(r'^(.*?)\s*=>\s*(.+)$', params)

        method_value = result.groups()[0]
        result_value = result.groups()[1] if len(result.groups()) > 1 else None

        self.ui.on_run_function(params)

        results = eval(method_value, globals_dict)

        if result_value:
            self.context.set_variable(result_value, results)

