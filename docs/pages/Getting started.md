# Getting started

## Installation

Run the following command to install Lime:

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

## Copilot 

Lime is using Copilot (currently), so you will need to have the [Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/install-copilot-cli) installed and configured to use Lime.

> Note: Lime will be adding support for other agents in the future, but for now Copilot is the only supported agent.

## Your first template

Create a file named `hello.mgx` with the following content:

```margarita
---
description: Hello world tutorial for Lime!
---

<<
# Hello World

Tell the user Hello, and welcome them to Lime!
>>

@effect run
```

```shell
lime execute hello.mgx
```

> Note: This template includes metadata, this is optional but recommended for better organization and discoverability. Metadata can contain any key value pair.

The << >> block contains markdown content, this is the main prompt that you will send to the agent.

`@effect run` is a special instruction that tells the agent to execute.

Once you run the command, you should see the following output in your terminal:

## Output

```Markdown
# Hello World

Hello, and welcome to Lime!
```

Now that you have run your first template, check out some of the other things you can do with Lime.

