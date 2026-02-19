<div style="text-align: center;">
    <img src="lime.svg" alt="Margarita logo" width="180" />
    <h1>Lime</h1>
    <p>A code agent with programmable markdown files</p>
</div>

**Lime wants you have fun programming Agents/LLMs and bring back more control into your hands.**

Features
- Get all the benefits of [margarita](http://github.com/Banyango/margarita) files now with agentic capabilities.
- Bring your favourite coding agent (Copilot for now) (roadmap for Claude code, codex and more soon)
- React like composability through includes `[[ my-component is_admin=true ]]`
- Store variables in state, and have the LLMs update/fetch state as needed.
- Don't waste tokens on having LLMs run functions. Run it locally and then pass the results to the LLM.
- Forget context explosion issues. Surgically control what context is sent to the LLM.
- Add only the tools you need for a query. Nuke them, then add others and repeat. This keeps context size small and relevant.

# Example

<pre><code><code style="color: #6a9955;">// file:example.mgx</code>
<code style="color: #ce9178;">---
description: Add metadata
team: Can put anything in metadata
---</code>

<code style="color: #6a9955;">// Import python functions for use with @effect func</code>
<code style="color: #c586c0;">from</code> <code style="color: #4ec9b0;">math</code> <code style="color: #c586c0;">import</code> <code style="color: #dcdcaa;">add</code>, <code style="color: #dcdcaa;">subtract</code>, <code style="color: #dcdcaa;">multiply</code>, <code style="color: #dcdcaa;">load_files</code>

<code style="color: #6a9955;">// Supports all markdown. Places this into the agent's context.</code>
<code style="color: #569cd6;">&lt;&lt;</code>
<code style="color: #d4d4d4;">You are an expert mathematician.
Your task is to solve addition problems accurately and efficiently.

When given a problem, you should:
1. Read the problem carefully.
2. Identify the two numbers to be added.
3. Calculate the sum of the two numbers.
4. Provide the final answer clearly.</code>
<code style="color: #569cd6;">&gt;&gt;</code>

<code style="color: #6a9955;">// Include other margarita files into the context</code>
<code style="color: #569cd6;">[[</code> <code style="color: #ce9178;">create-a-react-component.mg</code> <code style="color: #569cd6;">]]</code>

<code style="color: #6a9955;">// Execute a loop</code>
<code style="color: #c586c0;">for</code> <code style="color: #9cdcfe;">i</code> <code style="color: #c586c0;">in</code> <code style="color: #9cdcfe;">items</code>:
    <code style="color: #6a9955;">// run Python functions and store results in state.</code>
    <code style="color: #569cd6;">@effect</code> <code style="color: #c586c0;">func</code> <code style="color: #dcdcaa;">add</code>(<code style="color: #b5cea8;">12</code>, <code style="color: #9cdcfe;">test</code>.<code style="color: #9cdcfe;">data</code>) <code style="color: #569cd6;">=&gt;</code> <code style="color: #9cdcfe;">result</code>

<code style="color: #6a9955;">// The agent can access/ set state variables too!</code>
<code style="color: #569cd6;">&lt;&lt;</code>
<code style="color: #d4d4d4;">Add 12 + test.data and store the result in the variable 'result'.</code>
<code style="color: #569cd6;">&gt;&gt;</code>

<code style="color: #6a9955;">// Add tools, note: AddToolParam extends BaseModel from pydantic</code>
<code style="color: #569cd6;">@effect</code> <code style="color: #c586c0;">tools</code> <code style="color: #dcdcaa;">add</code>(<code style="color: #9cdcfe;">params</code>: <code style="color: #4ec9b0;">AddToolParams</code>) <code style="color: #569cd6;">=&gt;</code> <code style="color: #4ec9b0;">int</code>

<code style="color: #6a9955;">// Run the agent using tools and the context you built up.</code>
<code style="color: #569cd6;">@effect</code> <code style="color: #c586c0;">run</code>

<code style="color: #6a9955;">// clear the context and tools after running to avoid context explosion in future runs.</code>
<code style="color: #569cd6;">@effect</code> <code style="color: #c586c0;">context</code> <code style="color: #dcdcaa;">clear</code>
<code style="color: #569cd6;">@effect</code> <code style="color: #c586c0;">tools</code> <code style="color: #dcdcaa;">clear</code>

<code style="color: #6a9955;">// use the state result variables with a new context.</code>
<code style="color: #569cd6;">&lt;&lt;</code>
<code style="color: #d4d4d4;">Validate the following:
- The addition tool correctly adds two numbers.
- The subtraction tool correctly subtracts two numbers.
- The multiplication tool correctly multiplies two numbers.
- The load_files function correctly loads and reads files from the specified directory.</code>
<code style="color: #569cd6;">&gt;&gt;</code>

# conditonal logic
if result.failed:
    <<
    The test failed. Please review the implementation of the math tools and the
    load_files function for any errors.
    >>
    @effect run
else:
    # We're done!
```

Hopefully this gives you a taste of the possibilities with Lime!


# Installation

Run the following command for your platform to install Lime:

Linux:
```sh
curl -fsSL https://raw.githubusercontent.com/Banyango/lime/main/install-linux.sh | bash -s -- --option
```

MacOS:
```sh
curl -fsSL https://raw.githubusercontent.com/Banyango/lime/main/install-macos.sh | bash -s -- --option
```

Windows (PowerShell):
```powershell
iwr -useb https://raw.githubusercontent.com/Banyango/lime/main/install-windows.ps1 | iex
```


Logo Designed by Freepik