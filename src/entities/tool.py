from dataclasses import dataclass


@dataclass
class Param:
    name: str
    type: str
    required: bool = True


@dataclass
class Tool:
    name: str
    params: list[Param]
    return_types: list[str]
    description: str | None = None
