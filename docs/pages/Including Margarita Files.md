# Including Margarita Files

Lime supports including other [Margarita](https://github.com/Banyango/margarita) files using the `[[ file ]]` syntax. This allows you to reuse template fragments across multiple templates.

### Example:

```margarita
// filename: tester_role.mg
<<
You are a tester AI assistant.

Run playwright tests on the provided files

${files}
>>
```

```margarita
// filename: page.mgx

[[ tester_role.mg files=["test1.spec.ts", "test2.spec.ts"] ]]

@effect run
```

### See also

See the [Margarita documentation](http://github.com/Banyango/margarita) for more details on template syntax, conditionals, loops, and metadata.
