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
)

from core.agents.agent import Agent
from core.agents.agent_plugin import AgentPlugin


class ExecuteAgentOperation:
    def __init__(self, agent: Agent, plugins: list[AgentPlugin]):
        self.base_path = None
        self.agent = agent
        self.plugins = plugins
        for plugin in self.plugins:
            plugin.set_agent(agent)

    async def execute_async(self, mgx_file: str, base_path: Path | None = None):
        """Execute an .mgx file with an agent

        Args:
            mgx_file: The content of the .mgx file to execute
            base_path: Optional base directory path for resolving include statements
        """
        self.base_path = base_path

        parser = Parser()
        metadata, nodes = parser.parse(mgx_file)

        await self._process_nodes_async(nodes)

    async def _process_nodes_async(self, nodes: list[Node]):
        """Process a list of AST nodes, executing actions based on node type.

        Args:
            nodes: List of parsed AST nodes to process
        """
        for node in nodes:
            if isinstance(node, TextNode):
                self.agent.add_to_context(node.content)

            elif isinstance(node, VariableNode):
                value = self.agent.get_variable_value(node.name)
                if value is not None:
                    self.agent.add_to_context(str(value))

            elif isinstance(node, IfNode):
                condition_value = self.agent.get_variable_value(node.condition)
                if self._is_truthy(condition_value):
                    await self._process_nodes_async(node.true_block)
                elif node.false_block:
                    await self._process_nodes_async(node.true_block)

            elif isinstance(node, ForNode):
                items = self.agent.get_variable_value(node.iterable)
                if items:
                    for item in items:
                        self.agent.add_to_state(node.iterator, item)
                        await self._process_nodes_async(node.block)
                        self.agent.remove_from_state(node.iterator)

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

        plugin = split[0] if len(split) == 1 else None
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
                await effect_plugin.handle(operation)
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
