# AGENTS.md

## Project Overview

**Lime** is a code agent framework that enables programmable markdown files (`.mgx` files) to execute agentic LLM
workflows. It bridges the [Margarita](http://github.com/Banyango/margarita) templating language with AI coding
assistants (currently GitHub Copilot), giving developers fine-grained control over context, state, and tool execution.

## Architecture

Lime follows **Clean Architecture** principles with dependencies pointing inward:

```
┌─────────────────────────────────────────────────┐
│                     App                         │
│  (CLI, Writers, Container, Lifecycle)           │
├─────────────────────────────────────────────────┤
│                     Core                        │
│  (Agents, Operations, Plugins, Interfaces)      │
├─────────────────────────────────────────────────┤
│                   Entities                      │
│  (Context, Run, Tool, FunctionCall)             │
├─────────────────────────────────────────────────┤
│                     Libs                        │
│  (Copilot Client, Tools, Type Mapper)           │
└─────────────────────────────────────────────────┘
```

### Layer Responsibilities

- **App**: Application entry points (CLI commands), UI rendering, dependency injection container, and lifecycle
  management
- **Core**: Business logic including agent execution operations, plugin system, and abstract interfaces
- **Entities**: Domain models representing Context, Runs, Tools, and Function Calls
- **Libs**: External service integrations (GitHub Copilot SDK)

## Directory Structure

```
src/
├── main.py                          # Entry point
├── app/
│   ├── cli.py                       # Click-based CLI commands
│   ├── config.py                    # Application configuration
│   ├── container.py                 # Wireup DI container setup
│   ├── lifecycle.py                 # App startup/shutdown context manager
│   ├── agents/
│   │   └── execute.py               # `execute` CLI command implementation
│   └── writers/
│       └── writer.py                # Rich-based terminal UI renderer
├── core/
│   ├── agents/
│   │   ├── models.py                # ExecutionModel, Turn dataclasses
│   │   ├── operations/
│   │   │   └── execute_agent_operation.py  # Main .mgx file execution logic
│   │   └── plugins/                 # AgentPlugin implementations
│   │       ├── context.py           # @effect context (clear)
│   │       ├── func.py              # @effect func (run Python functions)
│   │       ├── import_plugin.py     # Python import handling
│   │       ├── run_agent.py         # @effect run (execute LLM query)
│   │       └── tools.py             # @effect tools (register tools)
│   └── interfaces/
│       ├── agent_plugin.py          # AgentPlugin abstract base class
│       ├── query_service.py         # QueryService abstract interface
│       └── ui.py                    # UI abstract interface
├── entities/
│   ├── context.py                   # Context with variables, window, tools
│   ├── function.py                  # FunctionCall dataclass
│   ├── run.py                       # Run, ToolCall, TokenUsage models
│   └── tool.py                      # Tool, Param dataclasses
└── libs/
    ├── container.py                 # Startup/shutdown hooks for services
    └── copilot/
        ├── client.py                # GithubCopilotClient wrapper
        ├── copilot_agent.py         # CopilotQuery QueryService implementation
        ├── type_mapper.py           # Type mapping utilities
        └── tools/
            ├── get_variable_from_state.py  # get_variable tool for LLM
            └── set_variable_in_state.py    # set_variable tool for LLM
```

## Key Components

### ExecutionModel (`src/core/agents/models.py`)

Central state container for agent execution:

- Manages context (variables, window, tools)
- Tracks turns and runs
- Stores import errors and metadata
- Maintains globals dictionary for Python execution

### ExecuteAgentOperation (`src/core/agents/operations/execute_agent_operation.py`)

Orchestrates `.mgx` file execution:

- Parses Margarita syntax (TextNode, VariableNode, IfNode, ForNode, etc.)
- Dispatches `@effect` commands to appropriate plugins
- Handles includes, imports, and variable substitution

### Plugin System

All plugins implement `AgentPlugin` interface:

- **`is_match(token)`**: Returns `True` if plugin handles the given token
- **`handle(params, execution_model)`**: Executes the plugin logic

| Plugin           | Token     | Purpose                                        |
|------------------|-----------|------------------------------------------------|
| `RunAgentPlugin` | `run`     | Executes LLM query via QueryService            |
| `FuncPlugin`     | `func`    | Runs Python functions, stores results in state |
| `ToolsPlugin`    | `tools`   | Registers tools for LLM to call                |
| `ContextPlugin`  | `context` | Context operations (e.g., `clear`)             |

### CopilotQuery (`src/libs/copilot/copilot_agent.py`)

GitHub Copilot integration:

- Implements `QueryService` interface
- Creates Copilot sessions with tools
- Handles streaming events (reasoning, responses, tool calls)
- Tracks token usage, costs, and run metrics

## .mgx File Syntax

```mgx
---
description: "Metadata section"
---

// Python imports
from module import function, MyClass

// Add to context window
<<
System prompt or instructions for the LLM
>>

// Include other .mg files
[[ component.mg variable=value ]]

// State variables
@state my_var = "value"
@state counter = 0

// For loops
for i in range(5):
    <<Iteration ${i}>>

// Conditionals
if variable:
    <<Conditional content>>
else:
    <<Alternative content>>

// Run Python functions
@effect func my_function(arg1, arg2) => result_var

// Register tools for LLM
@effect tools my_tool(param: ParamType) => ReturnType

// Execute LLM query
@effect run

// Clear context/tools after run
@effect context clear
@effect tool clear
```

## Dependencies

- **Python 3.12+**
- **margarita**: `.mgx` file parsing
- **github-copilot-sdk**: Copilot API integration
- **wireup**: Dependency injection
- **rich**: Terminal UI rendering
- **click**: CLI framework
- **pydantic**: Data validation for tool parameters

## Development Commands

```bash
make install      # Install dependencies with uv
make test         # Run pytest
make lint         # Run ruff linter
make format       # Format code with ruff
make type-check   # Run mypy
make check        # Run all checks
```

## Running Lime

```bash
# Execute an .mgx file
uv run python src/main.py execute --file-name path/to/file.mgx
```

## Testing

- **Unit tests**: `test/unit/` - Component-level tests
- **Evals**: `test/evals/` - End-to-end `.mgx` file evaluations

Unit tests should be in the same test directory as the code they test, following the structure of `src/`. 

### Test Case Naming

tests should follow the pattern `test_[method]_should_[expected_behavior]_when_[condition]`:

```python
def test_handle_should_store_result_in_state_when_func_effect_is_called():
    ...
```

### Test Style

We should prefer to not use pytest Classes. Keep the tests as simple functions. 

Do not use fixtures for shared setup if needed, prefer a properly typed `_create_[data]` helper function instead.

Use `@pytest.mark.asyncio` for async tests. 

Tests should follow the Arrange-Act-Assert pattern:

```python
def test_example():
    # Arrange: Set up test data and mocks
    input_data = ...
    expected_result = ...
    mock_dependency = Mock(...) 
    
    # Act: Call the function/method being tested
    result = function_under_test(input_data, dependency=mock_dependency)
    
    # Assert: Verify the result is as expected
    assert result == expected_result
    mock_dependency.assert_called_once_with(...)
```

## Key Design Decisions

1. **Plugin-based extensibility**: New `@effect` commands can be added by implementing `AgentPlugin`
2. **Stateful execution**: `ExecutionModel` persists across turns, enabling multi-step workflows
3. **Context control**: Explicit `context clear` and `tools clear` prevent context explosion
4. **Local function execution**: Python functions run locally, only results go to LLM
5. **Tool injection**: LLM has `get_variable` and `set_variable` tools for state access

