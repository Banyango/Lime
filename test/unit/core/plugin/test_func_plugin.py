import asyncio
from datetime import datetime

from core.agents.plugins.func import FuncPlugin
from core.agents.models import ExecutionModel
from entities.run import RunStatus


def test_func_should_do_thing_when_condition():
    # Arrange
    plugin = FuncPlugin()
    assert plugin.is_match("func")

    execution_model = ExecutionModel()
    execution_model.start_run(prompt="p", provider="prov", status=RunStatus.PENDING, start_time=datetime.utcnow())

    # Set variables that will be used as function arguments
    execution_model.context.set_variable("a", 2)
    execution_model.context.set_variable("b", 3)

    # Provide a function in the globals that will be invoked by the plugin
    globals_dict = {}
    exec("def add(a, b):\n    return a + b", globals_dict)

    params = "add(a, b) => sum_result"

    # Act
    asyncio.run(plugin.handle(params, globals_dict, execution_model))

    # Assert
    # One function call should be logged
    assert len(execution_model.function_calls) == 1
    call = execution_model.function_calls[0]

    # The logged method should match the invoked expression and params should contain the resolved args
    assert call.method == "add(a, b)"
    assert call.params == {"a": 2, "b": 3}

    # The call result should be set and the context should contain the result variable
    assert call.result == 5
    assert execution_model.context.get_variable_value("sum_result") == 5
