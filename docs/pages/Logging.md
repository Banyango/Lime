# Logging

Lime supports logging output as your scripts are running.
This can be useful for debugging and monitoring the progress of your scripts.

To log output, use the `@effect log` node in your script. For example:

```margarita
@effect log "This is a log message."
```

Outputs:
```markdown
[INFO]: This is a log message.
```

You can also include variables in your log messages. For example:

```margarita
@state count = 0

@effect log "The current count is ${count}."
```

Outputs:
```markdown
[INFO]: The current count is 0.
```
