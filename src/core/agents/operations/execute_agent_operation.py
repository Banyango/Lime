import json
import re
from pathlib import Path
from typing import Any

from loguru import logger
from margarita.parser import (
    EffectNode,
    ForNode,
    IfNode,
    ImportNode,
    IncludeNode,
    Node,
    Parser,
    StateNode,
    TextNode,
    VariableNode,
)

from core.agents.models import ExecutionModel
from core.agents.plugins.import_plugin import ImportPlugin
from core.interfaces.agent_plugin import AgentPlugin
from core.interfaces.prompt_integrity import PromptIntegrity
from entities.prompt_integrity import TRACKED_PROMPT_EXTENSIONS, PromptUnverifiedPathError


class ExecuteAgentOperation:
    def __init__(
        self,
        plugins: list[AgentPlugin],
        execution_model: ExecutionModel,
        prompt_integrity: PromptIntegrity | None = None,
        allow_unverified: bool = False,
    ):
        self.base_path = None
        self.plugins = plugins
        self.execution_model = execution_model
        self.prompt_integrity = prompt_integrity
        self.allow_unverified = allow_unverified

    async def execute_async(self, mgx_file: str, base_path: Path | None = None):
        """Execute an .mgx file with an agent

        Args:
            mgx_file: The content of the .mgx file to execute
            base_path: Optional base directory path for resolving include statements
        """
        self.base_path = base_path or Path.cwd()

        parser = Parser()
        metadata, nodes = parser.parse(mgx_file)

        self.execution_model.metadata = metadata

        self.execution_model.start_turn()

        await self._process_nodes_async(nodes)

    async def _process_nodes_async(self, nodes: list[Node]):
        """Process a list of AST nodes, executing actions based on node type.

        Args:
            nodes: List of parsed AST nodes to process
        """
        for node in nodes:
            if isinstance(node, TextNode):
                final_content = self.replace_variables_in_text_node(node.content)
                self.execution_model.context.add_to_context_window(final_content)

            elif isinstance(node, VariableNode):
                value = self.execution_model.context.get_variable_value(node.name)
                if value is not None:
                    self.execution_model.context.add_to_context_window(str(value))

            elif isinstance(node, IfNode):
                condition_value = self.execution_model.context.get_variable_value(node.condition)
                if self._is_truthy(condition_value):
                    await self._process_nodes_async(node.true_block)
                elif node.false_block:
                    await self._process_nodes_async(node.false_block)

            elif isinstance(node, ForNode):
                items = self.execution_model.context.get_variable_value(node.iterable)
                if items:
                    for item in items:
                        self.execution_model.context.add_to_state(node.iterator, item)
                        await self._process_nodes_async(node.block)
                        self.execution_model.context.remove_from_state(node.iterator)

            elif isinstance(node, StateNode):
                variable = json.loads(node.initial_value)
                self.execution_model.context.set_variable(node.variable_name, variable)

            elif isinstance(node, ImportNode):
                ImportPlugin.execute_import(node.raw_import, self.execution_model)

            elif isinstance(node, IncludeNode):
                # IncludeNodes render and add to context
                file_path = self._normalize_include_path(node.template_name)
                include_path = (self.base_path / file_path).resolve(strict=False)
                if not include_path.exists():
                    raise FileNotFoundError(f"Included prompt file was not found: '{include_path}'.")

                should_verify_file = True
                if self.prompt_integrity:
                    try:
                        self.prompt_integrity.verify_trusted_path(include_path)
                    except PromptUnverifiedPathError as error:
                        if not self.allow_unverified:
                            raise

                        should_verify_file = False
                        logger.warning(
                            "Allowing unverified include outside trusted prompt root: path='{}' reason='{}' "
                            "(enabled by --allow-unverified)",
                            include_path,
                            error,
                        )

                content_bytes = include_path.read_bytes()
                if self.prompt_integrity and should_verify_file:
                    self.prompt_integrity.verify_bytes(path=include_path, content_bytes=content_bytes)

                content = content_bytes.decode()
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
                await effect_plugin.handle(
                    params=operation,
                    execution_model=self.execution_model,
                )
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
            value = self.execution_model.context.get_variable_value(parts[0])
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

    def _normalize_include_path(self, template_name: str) -> str:
        """Normalize the include path.

        Args:
            template_name: The name of the template to normalize.

        Returns:
            The normalized template name.
        """
        include_path = template_name.strip()
        suffix = Path(include_path).suffix
        if not suffix:
            return f"{include_path}.mg"

        if suffix not in TRACKED_PROMPT_EXTENSIONS:
            raise ValueError(
                f"Unsupported include extension '{suffix}' in '{template_name}'. Only .mg and .md are allowed."
            )

        return include_path
