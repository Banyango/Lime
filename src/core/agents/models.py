import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from entities.context import Context
from entities.function import FunctionCall
from entities.memory import Memory
from entities.run import Run, RunStatus


@dataclass
class InputRequest:
    """A pending request for user input posted by InputPlugin and resolved by the UI.

    The plugin sets `pending_input` on the ExecutionModel and awaits `event`.
    The UI reads the prompt, shows an input widget, writes the user's answer into
    `response`, then calls `event.set()` to unblock the plugin.
    """

    prompt: str
    response: str | None = None
    event: asyncio.Event = field(default_factory=asyncio.Event)


@dataclass
class Turn:
    """Represents a single LLM turn during execution.

    Contains the prompt, model response, and any metadata produced for the
    turn that may be persisted in the run history.
    """

    run: Run | None
    function_calls: list[FunctionCall]


class ExecutionModel:
    """Central execution state for running an .mgx agent file.

    Holds context, globals, registered tools, and collected turns for the run.
    """

    """
    Purpose
    - Coordinate and store state for a running agent execution, including context, turns, and metadata.

    Public API
    - __init__() -> None: Create an empty execution model.
    - start() -> None: Initialize execution header and state for a run.
    - start_turn() -> Turn: Begin a new turn and return it.
    - start_run(prompt: str, provider: str, status: RunStatus, start_time: datetime) -> Run: Create and attach a Run to the current turn.
    - add_function_call_log(method: str, params: dict) -> FunctionCall: Record a function call for auditing.
    - add_import_error(error: str) -> None: Record an import error.
    - add_warning(warning: str) -> None: Record a warning message.

    Examples
    >>> em = ExecutionModel()
    >>> em.start()
    >>> turn = em.start_turn()
    >>> run = em.start_run('prompt', 'local', RunStatus.RUNNING, datetime.utcnow())

    Notes
    - The ExecutionModel exposes simple helpers intended for orchestration; detailed Run internals are documented in Run
    """

    def __init__(self):
        self.pending_input: InputRequest | None = None
        self.header: str = ""
        self.context = Context()
        self.import_errors = []
        self.warnings: list[str] = []
        self.metadata: dict[str, Any] = {}
        self.turns: list[Turn] = []
        self.memory: Memory | None = None
        self.globals_dict: dict[str, Any] = globals()

    def start(self):
        """Initialize the execution model for a new agent execution."""
        self.header = "Agent execution started."

    def start_turn(self) -> Turn:
        """Start a new turn in the agent execution with the given run and context."""
        turn = Turn(run=None, function_calls=[])

        self.turns.append(turn)

        return turn

    @property
    def model(self) -> str | None:
        """Get the model specified in the .mgx front-matter, or None if absent."""
        return self.metadata.get("model")

    @property
    def current_run(self) -> Run | None:
        """Get the current run for the latest turn in the execution model.

        None if there are no turns or the latest turn has no run.
        """
        return self.turns[-1].run if self.turns else None

    @property
    def current_turn(self) -> Turn:
        """Get the current turn in the execution model. None if there are no turns."""
        return self.turns[-1] if self.turns else None

    @property
    def turns_with_runs(self) -> list[Turn]:
        """Get a list of all turns that have an associated run."""
        return [turn for turn in self.turns if turn.run is not None]

    def start_run(self, prompt: str, provider: str, status: RunStatus, start_time: datetime) -> Run:
        """Start a new LLM Agent run with the given prompt, provider, status, and start time.

        Args:
            prompt (str): The prompt for the new run.
            provider (str): The provider for the new run.
            status (RunStatus): The status for the new run.
            start_time (datetime): The start time for the new run.
        """
        run = Run(
            tool_calls=[],
            prompt=prompt,
            provider=provider,
            status=status,
            start_time=start_time,
            metadata=self.metadata,
        )

        self.turns[-1].run = run

        return run

    def add_function_call_log(self, method: str, params: dict) -> FunctionCall:
        """Add a function call log to the execution model.

        Args:
            method (str): The method name for the function call.
            params (dict): The parameters for the function call.
        """
        function_call = FunctionCall(method=method, params=json.dumps(params))

        self.turns[-1].function_calls.append(function_call)

        return function_call

    def add_import_error(self, error: str):
        """Add an import error to the execution model.

        Args:
            error (str): The error message for the import error.
        """
        self.import_errors.append(error)

    def add_warning(self, warning: str):
        """Add a warning message to the execution model.

        Args:
            warning (str): The warning message.
        """
        self.warnings.append(warning)

    def add_log(self, param: str):
        """
        Add a log entry to the current run's content blocks with the given text.

        Args:
            param (str): The log message to add as a content block.
        """
        if self.current_run:
            self.current_run.add_log(param)


class BreakSignal(Exception):
    """Internal exception used to short-circuit execution of a loop or flow.

    Raised by plugins or execution logic to indicate an early stop condition.
    """

    """Internal signal raised when a BreakNode."""

    pass
