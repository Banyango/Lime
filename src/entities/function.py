from dataclasses import dataclass


@dataclass
class FunctionCall:
    """Represents a call to a local Python function made during agent execution.

    Attributes:
        name: The function's name.
        args: Positional arguments for the function call.
        kwargs: Keyword arguments for the function call.
    """

    """One-line summary: Record of a function call executed by an agent.

    Purpose
    - Represent a single function invocation with its method name, serialized parameters, and optional result.

    Public API
    - method (str): The fully-qualified method name that was called.
    - params (str): Serialized representation of parameters passed to the function.
    - result (str | None): Serialized result of the call, or None if no result yet.

    Examples
    >>> FunctionCall(method='mymodule.do', params='{"x":1}')
    """
    method: str
    params: str
    result: str | None = None
