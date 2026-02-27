import re
from typing import Any

from entities.tool import Tool


class Context:
    """Holds variables and execution window state used during agent runs.

    The Context stores persistent variables accessible to functions and tools and
    maintains the sliding window of messages sent to the LLM.
    """

    """
    Purpose
    - Represent the agent's runtime context, holding state variables, the context window, and available tools.

    Public API
    - __init__(initial_data: dict[str, Any] | None = None) -> None: Initialize context with optional data.
    - add_to_context_window(content: str) -> None: Append content to the context window.
    - get_variable_value(name: str) -> Any: Retrieve variable values supporting dotted notation, slicing and range().
    - set_variable(name: str, value: Any) -> None: Set a variable in state.
    - add_tool(tool: Tool) -> None: Register a tool for agent use.
    - clear_tools() -> None: Remove all registered tools.
    - clear_context() -> None: Clear the context window.

    Examples
    >>> ctx = Context({'user': {'name': 'A'}})
    >>> ctx.get_variable_value('user.name')
    'A'
    >>> ctx.add_to_context_window('Note')

    Notes
    - Docstring focuses on external behavior; internal implementation details are omitted.
    """

    def __init__(self, initial_data: dict[str, Any] | None = None):
        self.data = initial_data or {}
        self.window = ""
        self.tools: list[Tool] = []

    def add_to_context_window(self, content: str):
        """Add content to the agent's context.

        Args:
            content (str): The content to add to the context.
        """
        self.window += content

    def get_variable_value(self, name: str) -> Any:
        """Get a variable value from context, supporting dotted notation, range, and indexing.

        Args:
            name: Variable name, possibly with dots like "user.name",
                  range like "range(5)", or indexing like "items[0]" or "items[0:3]"
        """
        # Handle range() function calls
        if name.startswith("range(") and name.endswith(")"):
            try:
                # Extract the arguments from range(...)
                args_str = name[6:-1]  # Remove "range(" and ")"
                if not args_str:
                    return None

                # Parse arguments (can be 1, 2, or 3 integers)
                args = [int(arg.strip()) for arg in args_str.split(",")]
                return list(range(*args))
            except (ValueError, TypeError):
                return None

        # Handle array indexing and slicing (e.g., "items[0]" or "items[0:3]")
        if "[" in name and name.endswith("]"):
            bracket_pos = name.index("[")
            var_name = name[:bracket_pos]
            index_str = name[bracket_pos + 1 : -1]

            # Get the base variable
            value = self.get_variable_value(var_name)
            if value is None:
                return None

            try:
                # Handle slicing (e.g., "0:3" or ":3" or "1:")
                if ":" in index_str:
                    parts = index_str.split(":")
                    start = int(parts[0]) if parts[0] else None
                    end = int(parts[1]) if len(parts) > 1 and parts[1] else None
                    return value[start:end]
                else:
                    # Handle simple indexing (e.g., "0")
                    index = int(index_str)
                    return value[index]
            except (ValueError, TypeError, IndexError, KeyError):
                return None

        # Handle dotted notation (e.g., "user.name")
        parts = name.split(".")
        value = self.data

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None

            if value is None:
                return None

        return value

    def set_variable(self, name: str, value: Any):
        """Set a variable in the agent's state.

        Args:
            name (str): The name of the variable to set.
            value (Any): The value to set for the variable.
        """
        self.data[name] = value

    def add_to_state(self, iterator: str, item: Any):
        """Add an item to the agent's state.

        Args:
            iterator (str): The name of the state variable to update.
            item (Any): The item to add to the state variable.
        """
        self.data[iterator] = item

    def remove_from_state(self, key: str):
        """Remove an item from the agent's state.

        Args:
            key (str): The key of the item to remove from the state.
        """
        self.data.pop(key, None)

    def add_tool(self, tool: Tool):
        """Add a tool to the agent's available tools.

        Args:
            tool (Tool): The tool to add to the agent's available tools.
        """
        self.tools.append(tool)

    def clear_tools(self):
        """Clear all tools from the agent's available tools."""
        self.tools = []

    def clear_context(self):
        """Clear the agent's context."""
        self.window = ""

    def replace_variables_in_content(self, content: str) -> str:
        pattern = r"\$\{([a-zA-Z_][\w\.]*)\}"

        def resolve_variable(name: str):
            parts = name.split(".")
            value = self.get_variable_value(parts[0])
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
