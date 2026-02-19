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

```markdown
// file:example.mgx
<svg width="400" height="120" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="400" height="120" fill="#f8f9fa" rx="8"/>
  
  <!-- Border -->
  <rect x="2" y="2" width="396" height="116" fill="none" stroke="#dee2e6" stroke-width="2" rx="6"/>
  
  <!-- Header line -->
  <line x1="20" y1="15" x2="380" y2="15" stroke="#6c757d" stroke-width="2" stroke-dasharray="5,5"/>
  
  <!-- Description section -->
  <text x="20" y="45" font-family="monospace" font-size="14" fill="#495057" font-weight="bold">description:</text>
  <text x="130" y="45" font-family="monospace" font-size="14" fill="#0d6efd">Add metadata</text>
  
  <!-- Team section -->
  <text x="20" y="75" font-family="monospace" font-size="14" fill="#495057" font-weight="bold">team:</text>
  <text x="130" y="75" font-family="monospace" font-size="14" fill="#198754">Can put anything in metadata</text>
  
  <!-- Footer line -->
  <line x1="20" y1="95" x2="380" y2="95" stroke="#6c757d" stroke-width="2" stroke-dasharray="5,5"/>
</svg>

// Import python functions for use with @effect func
from math import add, subtract, multiply, load_files

// Supports all markdown. Places this into the agent's context.
<<
You are an expert mathematician.
Your task is to solve addition problems accurately and efficiently.

When given a problem, you should:
1. Read the problem carefully.
2. Identify the two numbers to be added.
3. Calculate the sum of the two numbers.
4. Provide the final answer clearly.
>>

// Include other margarita files into the context
[[ create-a-react-component.mg ]]

// Execute a loop 
for i in items:
    // run Python functions and store results in state.
    @effect func add(12, test.data) => result

// The agent can access/ set state variables too!
<<
Add 12 + test.data and store the result in the variable 'result'.
>>

// Add tools, note: AddToolParam extends BaseModel from pydantic
@effect tools add(params: AddToolParams) => int

// Run the agent using tools and the context you built up.
@effect run

// clear the context and tools after running to avoid context explosion in future runs.
@effect context clear
@effect tools clear

// use the state result variables with a new context.
<<
Validate the following:
- The addition tool correctly adds two numbers.
- The subtraction tool correctly subtracts two numbers.
- The multiplication tool correctly multiplies two numbers.
- The load_files function correctly loads and reads files from the specified directory.
>>

// conditonal logic
if result.failed:
    <<
    The test failed. Please review the implementation of the math tools and the
    load_files function for any errors.
    >>
    @effect run
else:
    // We're done!
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