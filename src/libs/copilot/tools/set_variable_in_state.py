from copilot import define_tool
from pydantic import BaseModel

from core.agents.models import ExecutionModel


class SetVariableFromState(BaseModel):
    """Pydantic model representing parameters for the set_variable tool.

    Fields correspond to the expected API for storing variables in the agent's
    state from within the LLM tool call.
    """
    name: str
    value: str | list | dict | int | float | bool | None


async def create_set_variable_tool(execution_model: ExecutionModel):
    @define_tool(
        description="Set a variable in the shared state, for putting it in a var",
    )
    async def set_variable(params: SetVariableFromState) -> dict:
        value = execution_model.context.set_variable(params.name, params.value)
        return {"value": value}

    return set_variable
