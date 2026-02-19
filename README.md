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

```margaritascript
// file:example.mgx
---
description: Add metadata
team: Can put anything in metadata
---

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

## Prompt Integrity Locking

Prompt integrity locking helps you detect prompt tampering before prompt content is sent to the LLM.

### Why this exists

Prompt files can be edited accidentally or maliciously. This feature gives you a deterministic check that says:
- "These are the prompt files we trust."
- "These are the exact hashes we expect."

### Mental model

1. `prompts.toml` is the manifest (what to track).
2. `prompts.lock.json` is the lock (path -> sha256 hash).
3. Preflight verification checks all tracked prompt files against the lock at execute start.
4. Include-time verification checks included prompt bytes before include content is parsed/used.

### Schema compatibility

- `prompts.toml` and `prompts.lock.json` carry internal version checks (`version = 1` in v1) so Lime can fail fast on incompatible schema changes.
- The lock also pins `algorithm = "sha256"` to keep hashing deterministic and prevent silent verification drift.

### One-time setup

If you are running from source (without globally installing the `lime` binary), use the Make targets:

```sh
make prompts-init
make prompts-lock
make prompts-check
```

If you are not using `make`, run the equivalent source commands directly:

```sh
uv run python src/main.py prompts init
uv run python src/main.py prompts lock
uv run python src/main.py prompts check
```

This creates:
- `prompts.toml`
- `prompts.lock.json`

### Day-to-day workflow (for contributors)

1. Edit a tracked prompt file under `prompts/` (`.mg` / `.md`).
2. Run `make prompts-check` (it should fail until lock is updated).
3. Run `make prompts-lock` to regenerate hashes.
4. Run `make prompts-check` again (should pass).
5. Commit both the prompt changes and `prompts.lock.json`.

### Runtime behavior

During `execute`, verification is auto-enabled when `prompts.toml` exists.

- No `prompts.toml`: execution continues (feature is opt-in).
- `prompts.toml` exists but lock missing: execution fails (fail-closed).
- Any tracked file hash mismatch: execution fails.
- Include outside trusted `prompts/` root:
  - blocked by default
  - allowed only with `--allow-unverified`
- Missing include file: execution fails.

When verification is enabled, Lime performs a preflight lock check at execute start and still verifies included prompt bytes before include content is parsed.

### Execute flag behavior

- `--verify-prompts`: force verification on (fails if `prompts.toml` or `prompts.lock.json` is invalid/missing).
- `--no-verify-prompts`: force verification off (skip manifest/lock checks for this run).
- `--allow-unverified`: only affects include paths outside trusted `prompts/` root; it permits those includes with a warning.

How they interact:
- Default (`execute` with no verify flag): auto mode, verify only when `prompts.toml` exists.
- `--allow-unverified` only matters when verification is enabled (auto-enabled or `--verify-prompts`).

### Security notes

- This is tamper-evident integrity and change control, not a complete security boundary.
- Trust in `prompts.lock.json` comes from your review process (PR review, protected branches, CI checks).
- Recommended CI gate: run `make prompts-check` (or equivalent direct command) on pull requests.

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