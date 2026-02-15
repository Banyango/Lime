from dataclasses import dataclass


@dataclass
class FunctionCall:
    method: str
    params: str
    result: str | None = None
