import asyncio
from pathlib import Path

import click

from app.container import container
from app.lifecycle import with_lifecycle
from core.agents.models import ExecutionModel
from core.agents.operations.execute_agent_operation import ExecuteAgentOperation
from core.agents.plugins.context import ContextPlugin
from core.agents.plugins.func import FuncPlugin
from core.agents.plugins.run_agent import RunAgentPlugin
from core.agents.plugins.tools import ToolsPlugin
from core.interfaces.prompt_integrity import PromptIntegrity
from core.interfaces.query_service import QueryService
from core.interfaces.ui import UI
from entities.prompt_integrity import (
    PROMPT_LOCK_FILE_NAME,
    PROMPT_MANIFEST_FILE_NAME,
    PromptIntegrityError,
)


@click.command()
@click.argument("file_name", type=str)
@click.option("--verify-prompts/--no-verify-prompts", default=None)
@click.option("--allow-unverified", is_flag=True, default=False)
@with_lifecycle
async def execute(file_name: str, verify_prompts: bool | None, allow_unverified: bool) -> None:
    """Execute an .mgx file with optional prompt integrity verification.

    Args:
        file_name (str): The path to the .mgx file.
        verify_prompts: Explicitly enable/disable prompt verification.
        allow_unverified: If True, allow unverified includes with a warning.
    """
    base_path = Path(file_name).parent
    manifest_path = Path(PROMPT_MANIFEST_FILE_NAME)
    lock_path = Path(PROMPT_LOCK_FILE_NAME)
    has_manifest = manifest_path.exists()

    should_verify_prompts = verify_prompts if verify_prompts is not None else has_manifest

    ui = await container.get(UI)
    query_service = await container.get(QueryService)
    prompt_integrity = None

    if should_verify_prompts:
        if not has_manifest:
            raise click.ClickException(
                f"Prompt verification is enabled, but '{PROMPT_MANIFEST_FILE_NAME}' was not found."
            )

        prompt_integrity = await container.get(PromptIntegrity)
        try:
            prompt_integrity.load_policy(manifest_path=manifest_path, lock_path=lock_path)
            prompt_integrity.check_against_lock()
        except PromptIntegrityError as error:
            raise click.ClickException(str(error)) from error

    if not Path(file_name).is_file():
        print(f"File '{file_name}' does not exist.")
        return

    with open(file_name) as f:
        mgx_code = f.read()

        model = ExecutionModel()

        operation = ExecuteAgentOperation(
            plugins=[
                RunAgentPlugin(agent_service=query_service),
                FuncPlugin(),
                ToolsPlugin(),
                ContextPlugin(),
            ],
            execution_model=model,
            prompt_integrity=prompt_integrity,
            allow_unverified=allow_unverified,
        )

        ui_task = asyncio.create_task(ui.render_ui(model))

        try:
            await operation.execute_async(mgx_file=mgx_code, base_path=base_path)
        except (PromptIntegrityError, ValueError, FileNotFoundError) as error:
            raise click.ClickException(str(error)) from error

        await ui_task
