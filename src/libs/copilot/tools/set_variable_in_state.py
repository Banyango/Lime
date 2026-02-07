from copilot import define_tool
from pydantic import BaseModel

from entities.context import Context


class SetVariableFromState(BaseModel):
    name: str
    value: str


def create_set_variable_tool(context: Context):
    @define_tool(name="SetVariable", description="Set a variable in the shared state")
    async def set_variable(params: SetVariableFromState) -> dict:
        value = context.set_variable(params.name, params.value)
        return {"value": value}

    return set_variable

