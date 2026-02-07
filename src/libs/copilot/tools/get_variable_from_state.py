from copilot import define_tool
from pydantic import BaseModel

from entities.context import Context


class GetVariableFromState(BaseModel):
    variable: str


def create_get_variable_tool(context: Context):
    @define_tool(name="GetVariable", description="Get a variable from the shared state")
    async def get_variable(params: GetVariableFromState) -> dict:
        value = context.get_variable_value(params.variable)
        return {params.variable: value}

    return get_variable
