# Running the Agent

Run the agent CLI (example):

```bash
lime execute example.mgx
```

## Specify the model

You can specify the model to use by adding a model field to the metadata of your .mgx file:

```margaritascript
---
model: "gpt-4"
---

<< test >>

@effect run
```
