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

<pre><code><span style="color: #6a9955;">// file:example.mgx</span>
<span style="color: #ce9178;">---
description: Add metadata
team: Can put anything in metadata
---</span>

<span style="color: #6a9955;">// Import python functions for use with @effect func</span>
<span style="color: #c586c0;">from</span> <span style="color: #4ec9b0;">math</span> <span style="color: #c586c0;">import</span> <span style="color: #dcdcaa;">add</span>, <span style="color: #dcdcaa;">subtract</span>, <span style="color: #dcdcaa;">multiply</span>, <span style="color: #dcdcaa;">load_files</span>

<span style="color: #6a9955;">// Supports all markdown. Places this into the agent's context.</span>
<span style="color: #569cd6;">&lt;&lt;</span>
<span style="color: #d4d4d4;">You are an expert mathematician.
Your task is to solve addition problems accurately and efficiently.

When given a problem, you should:
1. Read the problem carefully.
2. Identify the two numbers to be added.
3. Calculate the sum of the two numbers.
4. Provide the final answer clearly.</span>
<span style="color: #569cd6;">&gt;&gt;</span>

<span style="color: #6a9955;">// Include other margarita files into the context</span>
<span style="color: #569cd6;">[[</span> <span style="color: #ce9178;">create-a-react-component.mg</span> <span style="color: #569cd6;">]]</span>

<span style="color: #6a9955;">// Execute a loop</span>
<span style="color: #c586c0;">for</span> <span style="color: #9cdcfe;">i</span> <span style="color: #c586c0;">in</span> <span style="color: #9cdcfe;">items</span>:
    <span style="color: #6a9955;">// run Python functions and store results in state.</span>
    <span style="color: #569cd6;">@effect</span> <span style="color: #c586c0;">func</span> <span style="color: #dcdcaa;">add</span>(<span style="color: #b5cea8;">12</span>, <span style="color: #9cdcfe;">test</span>.<span style="color: #9cdcfe;">data</span>) <span style="color: #569cd6;">=&gt;</span> <span style="color: #9cdcfe;">result</span>

<span style="color: #6a9955;">// The agent can access/ set state variables too!</span>
<span style="color: #569cd6;">&lt;&lt;</span>
<span style="color: #d4d4d4;">Add 12 + test.data and store the result in the variable 'result'.</span>
<span style="color: #569cd6;">&gt;&gt;</span>

<span style="color: #6a9955;">// Add tools, note: AddToolParam extends BaseModel from pydantic</span>
<span style="color: #569cd6;">@effect</span> <span style="color: #c586c0;">tools</span> <span style="color: #dcdcaa;">add</span>(<span style="color: #9cdcfe;">params</span>: <span style="color: #4ec9b0;">AddToolParams</span>) <span style="color: #569cd6;">=&gt;</span> <span style="color: #4ec9b0;">int</span>

<span style="color: #6a9955;">// Run the agent using tools and the context you built up.</span>
<span style="color: #569cd6;">@effect</span> <span style="color: #c586c0;">run</span>

<span style="color: #6a9955;">// clear the context and tools after running to avoid context explosion in future runs.</span>
<span style="color: #569cd6;">@effect</span> <span style="color: #c586c0;">context</span> <span style="color: #dcdcaa;">clear</span>
<span style="color: #569cd6;">@effect</span> <span style="color: #c586c0;">tools</span> <span style="color: #dcdcaa;">clear</span>

<span style="color: #6a9955;">// use the state result variables with a new context.</span>
<span style="color: #569cd6;">&lt;&lt;</span>
<span style="color: #d4d4d4;">Validate the following:
- The addition tool correctly adds two numbers.
- The subtraction tool correctly subtracts two numbers.
- The multiplication tool correctly multiplies two numbers.
- The load_files function correctly loads and reads files from the specified directory.</span>
<span style="color: #569cd6;">&gt;&gt;</span>

<span style="color: #6a9955;">// conditonal logic</span>
<span style="color: #c586c0;">if</span> <span style="color: #9cdcfe;">result</span>.<span style="color: #9cdcfe;">failed</span>:
    <span style="color: #569cd6;">&lt;&lt;</span>
    <span style="color: #d4d4d4;">The test failed. Please review the implementation of the math tools and the
    load_files function for any errors.</span>
    <span style="color: #569cd6;">&gt;&gt;</span>
    <span style="color: #569cd6;">@effect</span> <span style="color: #c586c0;">run</span>
<span style="color: #c586c0;">else</span>:
    <span style="color: #6a9955;">// We're done!</span>
</code></pre>

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