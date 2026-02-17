# Context Management

Keep the context small and use `@effect context clear` to reset between runs.

### Example

This example:

1. Gets 50 books and then summarizes them. 
2. Stores the summary in a variable called `summary` for later use.
3. Clears the context and gets 50 more books 
4. Summarizes the new books
5. Then we contrast the new summary with the previous summary stored in the `summary` variable.

```
// file:context_management_example.mg

@state summary = ""

<<
You are a helpful assistant.

I've loaded 50 books into your context so 
your context is quite large now.

Give a summary of the books.

Store the summary in a variable called "summary" for later use.
>>

@effect run

// If we load another 50 books, the context will be even larger and may cause issues with token limits.

// If we have a second mdx script we would lose any state from the first script.

// Use @effect context clear to reset the context while retaining the `summary` variable.
@effect context clear

// All variables are retained
<<
Load 50 more books and summarize.

Contrast with Previous Summary: ${summary}
>>

@effect run
```