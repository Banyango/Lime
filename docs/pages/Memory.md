# Memory


Lime supports using memory to store information to json after a run.

memory variables will be stored into a `memory.json` file at the end of a run.

It then loads that same data back into memory at the beginning of the next run so that it can be used in the context and in func effects.

To use memory, you can use the `@memory var` node to create a new memory variable. For example:

```margarita
@memory var favorite_color

<<
If favorite_color is not set set it to "blue"
Otherwise write a log message saying "The user's favorite color is favorite_color"
>>

@effect run
```

## Immediate effects 

These operations on memory variables are immediate effects. This means that they will be executed immediately when the agent encounters them in the script, rather than being deferred until the `@effect run` node.

### Deleting Memory Variables

We can also delete variables from memory with the `@memory delete` node. For example:

```margarita
@memory delete favorite_color
```

### Clearing Memory

We can clear all variables from memory with the `@memory clear` node. For example:

```margarita
@memory clear
```


