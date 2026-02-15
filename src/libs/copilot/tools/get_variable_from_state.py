from copilot import define_tool
from pydantic import BaseModel

from core.agents.models import ExecutionModel


class GetVariableFromState(BaseModel):
    variable: str


async def create_get_variable_tool(execution_model: ExecutionModel):
    @define_tool(description="Get a variable from the shared state")
    async def get_variable(params: GetVariableFromState) -> dict:
        value = execution_model.context.get_variable_value(params.variable)
        return {params.variable: value}

    return get_variable
