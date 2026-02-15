import pytest

from core.agents.models import ExecutionModel
from core.agents.plugins.tools import ToolsPlugin
from entities.context import Context
from entities.tool import Tool, Param


@pytest.mark.parametrize(
    "params, result",
    [
        (
            "my_func(param1: int, param2: str) => result_var",
            Tool(
                name="my_func",
                params=[
                    Param(name="param1", type="int"),
                    Param(name="param2", type="str"),
                ],
                return_types=["result_var"],
            ),
        ),
        (
            "my_func() => another_result",
            Tool(
                name="my_func",
                params=[],
                return_types=["another_result"],
            ),
        ),
        (
            "my_func()",
            Tool(
                name="my_func",
                params=[],
                return_types=[],
            ),
        ),
        (
            "my_func(test: list)",
            Tool(
                name="my_func",
                params=[Param(name="test", type="list")],
                return_types=[],
            ),
        ),
        (
            "my_func(param1: int, param2: str) => result, result2",
            Tool(
                name="my_func",
                params=[
                    Param(name="param1", type="int"),
                    Param(name="param2", type="str"),
                ],
                return_types=["result", "result2"],
            ),
        ),
    ],
)
@pytest.mark.asyncio
async def test_handle_should_parse_correctly(params, result):
    # Arrange
    execution_model = ExecutionModel()
    tools_plugin = ToolsPlugin()

    # Act
    await tools_plugin.handle(
        params, {"my_func": lambda x: x}, execution_model=execution_model
    )

    # Assert
    assert execution_model.context.tools[0].name == result.name
    assert execution_model.context.tools[0].params == result.params
    assert execution_model.context.tools[0].return_types == result.return_types


# test invalid input
@pytest.mark.parametrize(
    "params",
    [
        "invalid input",
        "not_in_globals() => result_var",
        "my_func(param1: int, param2: str => result_var",
        "my_func{param1: int, param2: str} => result_var",
    ],
)
@pytest.mark.asyncio
async def test_handle_should_not_add_tool_for_invalid_input(params):
    # Arrange
    execution_model = ExecutionModel()
    tools_plugin = ToolsPlugin()

    # Act
    await tools_plugin.handle(
        params, {"my_func": lambda x: x}, execution_model=execution_model
    )

    # Assert
    assert len(execution_model.context.tools) == 0
