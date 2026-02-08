import re
from pathlib import Path
from typing import Any

from margarita.parser import (
    Parser,
    TextNode,
    Node,
    VariableNode,
    IfNode,
    ForNode,
    IncludeNode,
    EffectNode,
    StateNode,
    ImportNode,
)

from core.agents.plugins.import_plugin import ImportPlugin
from core.interfaces.ui import UI
from entities.context import Context
from core.interfaces.agent_plugin import AgentPlugin


class ExecuteAgentOperation:
    def __init__(self, context: Context, plugins: list[AgentPlugin], ui: UI):
        self.base_path = None
        self.context = context
        self.plugins = plugins
        self.global_dict = {}
        self.ui = ui

    async def execute_async(self, mgx_file: str, base_path: Path | None = None):
        """Execute an .mgx file with an agent

        Args:
            mgx_file: The content of the .mgx file to execute
            base_path: Optional base directory path for resolving include statements
        """
        self.base_path = base_path

        self.ui.on_agent_execution_start()

        parser = Parser()
        metadata, nodes = parser.parse(mgx_file)

        self.ui.on_parse_complete(metadata)

        await self._process_nodes_async(nodes)

    async def _process_nodes_async(self, nodes: list[Node]):
        """Process a list of AST nodes, executing actions based on node type.

        Args:
            nodes: List of parsed AST nodes to process
        """
        for node in nodes:
            if isinstance(node, TextNode):
                final_content = self.replace_variables_in_text_node(node.content)
                self.context.add_to_context_window(final_content)

            elif isinstance(node, VariableNode):
                value = self.context.get_variable_value(node.name)
                if value is not None:
                    self.context.add_to_context_window(str(value))

            elif isinstance(node, IfNode):
                condition_value = self.context.get_variable_value(node.condition)
                if self._is_truthy(condition_value):
                    await self._process_nodes_async(node.true_block)
                elif node.false_block:
                    await self._process_nodes_async(node.true_block)

            elif isinstance(node, ForNode):
                items = self.context.get_variable_value(node.iterable)
                if items:
                    for item in items:
                        self.context.add_to_state(node.iterator, item)
                        await self._process_nodes_async(node.block)
                        self.context.remove_from_state(node.iterator)

            elif isinstance(node, StateNode):
                self.context.set_variable(node.variable_name, node.initial_value)

            elif isinstance(node, ImportNode):
                self.global_dict = ImportPlugin.execute_import(node.raw_import)

            elif isinstance(node, IncludeNode):
                # IncludeNodes render and add to context
                file_path = node.template_name

                if not file_path.endswith(".mg"):
                    file_path += ".mg"

                include_path = self.base_path / file_path
                if include_path.exists():
                    content = include_path.read_text()
                    parser = Parser()
                    _, include_nodes = parser.parse(content)
                    await self._process_nodes_async(include_nodes)

            elif isinstance(node, EffectNode):
                await self._execute_effect_async(node.raw_content)

    async def _execute_effect_async(self, parameters: str):
        """Execute Python code from EffectNodes using imported modules.

        Args:
            parameters: The parameters.
        """
        split = parameters.split(" ", 1)

        plugin = split[0] if len(split) >= 1 else None
        operation = split[1] if len(split) > 1 else None

        await self.execute_plugin(plugin=plugin, operation=operation)

    async def execute_plugin(self, plugin: str, operation: str):
        """Execute a plugin operation.

        Args:
            plugin (str): The name of the plugin to execute.
            operation (str): The operation to perform with the plugin.
        """
        for effect_plugin in self.plugins:
            if effect_plugin.is_match(plugin):
                await effect_plugin.handle(params=operation, globals_dict=self.global_dict)
                break

    @staticmethod
    def _is_truthy(value: Any) -> bool:
        """Determine if a value is truthy for conditional evaluation.

        Args:
            value: The value to check

        Returns:
            True if the value is truthy, False otherwise
        """
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (list, dict, str)):
            return len(value) > 0
        if isinstance(value, (int, float)):
            return value != 0
        return True

    def replace_variables_in_text_node(self, content: str) -> str:
        pattern = r"\$\{([a-zA-Z_][\w\.]*)\}"

        def resolve_variable(name: str):
            parts = name.split(".")
            value = self.context.get_variable_value(parts[0])
            if value is None:
                return None
            for part in parts[1:]:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = getattr(value, part, None)
                if value is None:
                    return None
            return value

        def repl(match: re.Match) -> str:
            name = match.group(1)
            val = resolve_variable(name)
            return str(val) if val is not None else ""

        return re.sub(pattern, repl, content)




