import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from entities.context import Context
from entities.function import FunctionCall
from entities.run import Run, RunStatus


@dataclass
class Turn:
    run: Run | None
    function_calls: list[FunctionCall]


class ExecutionModel:
    def __init__(self):
        self.header: str = ""
        self.context = Context()
        self.import_errors = []
        self.metadata: dict[str, Any] = {}
        self.turns: list[Turn] = []
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
    def current_run(self) -> Run | None:
        """Get the current run for the latest turn in the execution model. None if there are no turns or the latest turn has no run."""
        return self.turns[-1].run if self.turns else None

    @property
    def current_turn(self) -> Turn:
        """Get the current turn in the execution model. None if there are no turns."""
        return self.turns[-1] if self.turns else None

    def start_run(
        self, prompt: str, provider: str, status: RunStatus, start_time: datetime
    ) -> Run:
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
