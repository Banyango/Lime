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

        match = re.search(r'([A-Za-z_][\w\.]*)\(\s*(.*?)\s*\)', method_value)
        func_param_str = match.groups()[1] if match and len(match.groups()) > 1 else None
        func_params = func_param_str.split(",") if func_param_str else []

        all_params = dict()
        for param in func_params:
            key_stripped = param.replace(" ", "")
            value = self.context.get_variable_value(key_stripped)
            if value:
                all_params[key_stripped] = value

        self.ui.on_run_function(params)

        results = eval(method_value, globals_dict, all_params)

        self.ui.on_function_complete(results)

        if result_value:
            self.context.set_variable(result_value, results)

