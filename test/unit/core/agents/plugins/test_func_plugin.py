import asyncio

from core.agents.plugins.func import FuncPlugin


class DummyContext:
    def __init__(self):
        self.vars = {}
        self.set_calls = []

    def get_variable_value(self, key):
        return self.vars.get(key)

    def set_variable(self, name, value):
        self.set_calls.append((name, value))


class DummyUI:
    def __init__(self):
        self.run_calls = []
        self.complete_calls = []

    def on_run_function(self, params):
        self.run_calls.append(params)

    def on_function_complete(self, result):
        self.complete_calls.append(result)


def test_func_should_match_when_token_is_func():
    # Arrange
    ctx = DummyContext()
    ui = DummyUI()
    plugin = FuncPlugin(ctx, ui)

    # Act
    matched = plugin.is_match("func")
    not_matched = plugin.is_match("other")

    # Assert
    assert matched is True
    assert not_matched is False


def test_func_should_run_function_and_store_result_when_params_provided():
    # Arrange
    ctx = DummyContext()
    ctx.vars = {"x": 2, "y": 3}
    ui = DummyUI()
    plugin = FuncPlugin(ctx, ui)
    params = "add(x,y) => result"
    globals_dict = {"add": lambda x, y: x + y}

    # Act
    asyncio.run(plugin.handle(params, globals_dict))

    # Assert
    assert ui.run_calls == [params]
    assert ui.complete_calls == [5]
    assert ctx.set_calls == [("result", 5)]
