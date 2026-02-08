from abc import ABC, abstractmethod


class UI(ABC):
    @abstractmethod
    def on_text_added(self, text: str):
        """Handle the event when text is added to the UI.

        Args:
            text (str): The text that was added to the UI.
        """

    @abstractmethod
    def on_text_terminated(self):
        """Handle the event when text generation is terminated."""

    @abstractmethod
    def on_reasoning_added(self, text: str):
        """Handle the event when reasoning text is added to the UI.

        Args:
            text (str): The reasoning text that was added to the UI.
        """

    @abstractmethod
    def on_reasoning_terminated(self):
        """Handle the event when reasoning generation is terminated."""

    @abstractmethod
    def on_tool_requested(self, tool_name: str, tool_input: str):
        """Handle the event when a tool is requested by the agent.

        Args:
            tool_name (str): The name of the tool that was requested.
            tool_input (str): The input for the tool that was requested.
        """

    @abstractmethod
    def on_agent_execution_start(self):
        """Handle the event when agent execution starts."""

    @abstractmethod
    def on_parse_complete(self, metadata: dict):
        """Handle the event when parsing of the .mgx file is complete.

        Args:
            metadata (dict): The metadata extracted from the .mgx file.
        """
