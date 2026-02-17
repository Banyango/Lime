# Loops

Use `for` loops inside `.mgx` to generate repeated sections.

```mgx
@state items = ["apple", "banana", "cherry"]

for i in items:
    <<Iteration ${i}>>
```

The prompt would be loaded with 
```markdown
Iteration apple
Iteration banana
Iteration cherry
```
