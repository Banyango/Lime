from dataclasses import dataclass
from typing import Any


@dataclass
class FunctionCall:
    method: str
    params: str
    result: str | None = None
