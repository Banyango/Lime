# User Input

Lime supports Getting user input during a run with the `@effect input` node.

```margarita
@effect input "What is your favorite color?" => favorite_color

// Then we can use the favorite_color variable in the context or in func effects.
@effect log "The user's favorite color is ${favorite_color}."
```

In the example above, the agent will ask the user "What is your favorite color?" and store the response in the variable 
`favorite_color`. The agent can then use this variable in subsequent context or function effects.
