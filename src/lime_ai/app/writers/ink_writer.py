"""Ink-based terminal UI writer for lime execution output.

Spawns a Node.js/Ink subprocess and communicates with it over stdio using
newline-delimited JSON. Python writes state updates to the child's stdin;
the child writes UI responses (user input, permission decisions) back to
its stdout.
"""

from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import click
from wireup import injectable

from lime_ai.core.agents.models import ExecutionModel
from lime_ai.core.interfaces.ui import UI
from lime_ai.entities.run import ContentBlockType

if TYPE_CHECKING:
    pass

_INK_UI_JS = Path(__file__).parent / "ink_ui" / "index.js"


@injectable(as_type=UI)
class InkWriter(UI):
    """UI implementation that delegates rendering to a bundled Ink (React) app."""

    async def render_ui(self, execution_model: ExecutionModel) -> None:
        node = _find_node()
        _ensure_bundle()

        proc = await asyncio.create_subprocess_exec(
            node,
            str(_INK_UI_JS),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=None,  # Inherited → goes to user's terminal
        )

        quit_event = asyncio.Event()

        try:
            # Wait for the Ink app to signal it's mounted and ready
            await asyncio.wait_for(_wait_for_ready(proc), timeout=15.0)

            # Run poll loop and response reader concurrently; either can stop both
            await asyncio.gather(
                _poll_loop(proc, execution_model, quit_event),
                _read_responses(proc, execution_model, quit_event),
            )
        except asyncio.TimeoutError:
            raise click.ClickException(
                "Ink UI did not start within 15 seconds. "
                "Run 'make build-ui' to rebuild the UI bundle."
            )
        finally:
            if proc.returncode is None:
                try:
                    proc.terminate()
                    await asyncio.wait_for(proc.wait(), timeout=3.0)
                except (asyncio.TimeoutError, ProcessLookupError):
                    proc.kill()


async def _wait_for_ready(proc: asyncio.subprocess.Process) -> None:
    assert proc.stdout is not None
    while True:
        line = await proc.stdout.readline()
        if not line:
            raise RuntimeError("Ink process exited before sending ui_ready")
        try:
            msg = json.loads(line.decode().strip())
            if msg.get("type") == "ui_ready":
                return
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass


async def _poll_loop(
    proc: asyncio.subprocess.Process,
    model: ExecutionModel,
    quit_event: asyncio.Event,
) -> None:
    assert proc.stdin is not None
    done_sent = False

    while not quit_event.is_set():
        try:
            payload = _serialize_model(model)
            line = json.dumps({"type": "state_update", "payload": payload}) + "\n"
            proc.stdin.write(line.encode())
            await proc.stdin.drain()
        except (BrokenPipeError, ConnectionResetError):
            return

        if model.done and not done_sent:
            done_sent = True
            try:
                done_line = json.dumps({"type": "agent_done", "payload": {}}) + "\n"
                proc.stdin.write(done_line.encode())
                await proc.stdin.drain()
            except (BrokenPipeError, ConnectionResetError):
                return

        await asyncio.sleep(0.1)


async def _read_responses(
    proc: asyncio.subprocess.Process,
    model: ExecutionModel,
    quit_event: asyncio.Event,
) -> None:
    assert proc.stdout is not None

    while not quit_event.is_set():
        line = await proc.stdout.readline()
        if not line:
            quit_event.set()
            return

        try:
            msg = json.loads(line.decode().strip())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        msg_type = msg.get("type")
        payload = msg.get("payload", {})

        if msg_type == "quit":
            quit_event.set()
            return
        elif msg_type == "input_response":
            pending = model.pending_input
            if pending is not None and id(pending) == payload.get("seq"):
                pending.response = payload.get("value", "")
                pending.event.set()
        elif msg_type == "permission_response":
            pending = model.pending_permission
            if pending is not None:
                pending.approved = bool(payload.get("approved", False))
                pending.event.set()


def _serialize_model(model: ExecutionModel) -> dict:
    turns = []
    for turn in model.turns:
        run_data = None
        if turn.run is not None:
            run = turn.run
            run_data = {
                "status": run.status.value,
                "model": run.model,
                "provider": run.provider,
                "duration_ms": run.duration_ms,
                "event_name": run.event_name.value if run.event_name else None,
                "tokens": {
                    "input_tokens": run.tokens.input_tokens,
                    "output_tokens": run.tokens.output_tokens,
                    "cache_read_tokens": run.tokens.cache_read_tokens,
                    "cache_write_tokens": run.tokens.cache_write_tokens,
                },
                "content_blocks": [
                    {
                        "type": block.type.value,
                        "text": _truncate(
                            block.text or "",
                            2000 if block.type == ContentBlockType.REASONING else None,
                        ),
                        "ref": block.ref,
                    }
                    for block in run.content_blocks
                ],
                "tool_calls": [
                    {
                        "tool_name": tc.tool_name,
                        "tool_call_id": tc.tool_call_id,
                        "arguments": tc.arguments,
                        "result": _truncate(tc.result, 500),
                        "success": tc.success,
                        "duration_ms": tc.duration_ms,
                        "parent_tool_call_id": tc.parent_tool_call_id,
                    }
                    for tc in run.tool_calls
                ],
                "errors": [
                    {
                        "message": err.message,
                        "code": err.code,
                        "error_type": err.error_type,
                    }
                    for err in run.errors
                ],
                "code_changes": {
                    "files_modified": run.code_changes.files_modified,
                    "lines_added": run.code_changes.lines_added,
                    "lines_removed": run.code_changes.lines_removed,
                }
                if run.code_changes
                else None,
                "request_count": run.request_count,
                "total_cost": run.total_cost,
                "prompt": run.prompt,
            }

        fc_data = [
            {
                "method": fc.method,
                "params": fc.params,
                "result": _truncate(fc.result, 150),
            }
            for fc in turn.function_calls
        ]

        turns.append({"run": run_data, "function_calls": fc_data})

    memory_data = None
    if model.memory:
        try:
            memory_data = dict(model.memory.get_items())
        except Exception:
            pass

    pending_input = None
    if model.pending_input:
        pending_input = {
            "prompt": model.pending_input.prompt,
            "seq": id(model.pending_input),
        }

    pending_permission = None
    if model.pending_permission:
        pending_permission = {
            "kind": model.pending_permission.kind,
            "details": model.pending_permission.details,
        }

    return {
        "header": model.header,
        "warnings": model.warnings,
        "import_errors": model.import_errors,
        "metadata": {k: str(v) for k, v in model.metadata.items()},
        "memory": memory_data,
        "turns": turns,
        "pending_input": pending_input,
        "pending_permission": pending_permission,
    }


def _truncate(text: str | None, limit: int | None) -> str | None:
    if text is None:
        return None
    if limit is None:
        return text
    return text[:limit] if len(text) > limit else text


def _find_node() -> str:
    node = shutil.which("node")
    if not node:
        raise click.ClickException(
            "Node.js is required to run the lime-ai UI. "
            "Install it from https://nodejs.org or run with --no-ui flag."
        )
    return node


def _ensure_bundle() -> None:
    if not _INK_UI_JS.exists():
        raise click.ClickException(
            f"Ink UI bundle not found at {_INK_UI_JS}. "
            "Run 'make build-ui' to build it."
        )
