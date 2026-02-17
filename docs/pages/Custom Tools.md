# Custom Tools

Register tools for the LLM with `@effect tools` and implement get/set variable helpers.

```mgx
from math import add

<<Add 3 and 5 >>

@effect tools add(x: int, y: int) => result

@effect run
```

This will register the `add` function as a tool that the LLM can call. 

Standard prompt engineering techniques can be used to get the LLM to call the tool and pass the correct arguments.

**Do note that the LLM may not always call the tool**, so it's important to design your prompts in a way that encourages the LLM to use the tool when appropriate.
