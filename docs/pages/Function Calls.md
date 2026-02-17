# Function Calls

Execute Python functions and save their results to state using `@effect func`.

> Note: The Python module (for example, `my_module`) must be available in the activated Python environment, and the import path must be correct.

```mgx
from my_module import compute

@effect func compute(x) => result
```

The example above calls `compute(x)` and stores its return value in the `result` state variable. You can reference this value in subsequent prompts using `${result}`.

Running functions this way avoids consuming LLM tokens for tool calls and lets you invoke deterministic logic directly instead of relying on the model to select the correct tool.
