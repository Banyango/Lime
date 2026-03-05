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

## Dictionary Iteration

Use `for key, value in dict_var:` to iterate over both keys and values of a dictionary.

```mgx
@state person = {"name": "Alice", "role": "admin"}

for key, value in person:
    <<${key}: ${value}>>
```

The prompt would be loaded with
```markdown
name: Alice
role: admin
```
