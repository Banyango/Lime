# Lime

Lime is a code agent built with programmable markdown files [margarita](http://github.com/Banyango/margarita) at it core.

**Most importantly Lime wants you have fun programming while being able to use LLMs and bring back more control into your hands. Stop being a code review/PRD blob and have fun programming again.**

Features
- Get all the benefits of margarita files now with agentic capabilities.
- Bring your favourite coding agent (Copilot for now) (roadmap for Claude code, codex and more soon)
- Store variables in state, and have the LLMs update/fetch state as needed.
- Don't waste tokens on having LLMs run functions. Run it locally and then pass the results to the LLM.
- Forget context explosion issues. Surgically control what context is sent to the LLM.
- Add only the tools you need for a query. Nuke them, then add others and repeat. This keeps context size small and relevant.

# Installation

Run the following command for your platform to install MARGARITA:

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
