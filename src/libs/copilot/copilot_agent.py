from datetime import datetime, timezone

from copilot import SessionConfig, MessageOptions, define_tool
from copilot.generated.session_events import SessionEventType
from copilot.types import SystemMessageAppendConfig, Tool, InfiniteSessionConfig
from wireup import injectable

from core.agents.models import ExecutionModel
from core.interfaces.query_service import QueryService
from entities.run import (
    RunStatus,
    ShutdownReason,
    TokenUsage,
    ModelUsage,
    ToolCall,
    CodeChanges,
    RunError,
    RunContext,
    ContentBlock,
    ContentBlockType,
)
from libs.copilot.client import GithubCopilotClient
from libs.copilot.tools.get_variable_from_state import create_get_variable_tool
from libs.copilot.tools.set_variable_in_state import (
    create_set_variable_tool,
)

SYSTEM_PROMPT = """You are an autonomous coding agent with explicit access to two tools for shared state: a get-variable tool and a set-variable tool. For every piece of state you need to read or update you must use these tools; do not assume, invent, or hardcode values from memory or ask the user for them.
Rules:
- Always call the get-variable tool before using any variable. If the variable is missing or empty, do not fabricate it — either compute it from available data or create it via the set-variable tool.
- Always call the set-variable tool to persist any information you want available to future steps.
- After each tool call, read and respect the tool's result. If a tool call fails, handle the failure and record an error variable via set-variable if needed.
- Use deterministic variable names and prefer primitive values (string/number/boolean). If you must store structured data, store it as JSON under a clear name.
- Do not prompt the user for missing values; act autonomously using available tools.

Tool call format (follow this pattern when requesting a tool):
- Read: CALL_TOOL: get_variable with arguments { "name": "<variable_name>" }
- Write: CALL_TOOL: set_variable with arguments { "name": "<variable_name>", "value": <value> }

Behavior after actions:
- Summarize the action taken and any state changes (variable names and values) in the assistant message so the run log is clear.
- Use temporary names like `temp_<short_desc>` if you need ephemeral storage.

Examples:
- To read build status: CALL_TOOL: get_variable { "name": "build_status" }
- To record an error: CALL_TOOL: set_variable { "name": "latest_error", "value": "stacktrace..." }

Always follow these rules for each run so the shared state remains accurate and consistent."""


@injectable(as_type=QueryService)
class CopilotQuery(QueryService):
    def __init__(self, copilot_client: GithubCopilotClient):
        self.client = copilot_client

    async def execute_query(self, execution_model: ExecutionModel) -> str:
        """Execute a query using the Copilot client.

        Args:
            execution_model (ExecutionModel): The execution model for the current agent run.
        """
        if not self.client.con:
            raise Exception("Copilot client is not connected")

        # Convert any internal Tool descriptors into Copilot SDK Tool objects.
        # We'll build a list of extra tools and pass them into the session.
        extra_tools: list[Tool] = []
        if execution_model.context.tools:
            for tool in execution_model.context.tools:
                name = tool.name
                params = tool.params
                description = tool.description

                funct = execution_model.globals_dict[name]
                if not funct:
                    break

                if params and len(params) == 1:
                    params_type = execution_model.globals_dict[params[0].type]

                    if not params_type:
                        execution_model.current_run.errors.append(
                            "Invalid tool parameter type: (Did you forget to import this type?)"
                            + params[0].type
                        )

                    tool = define_tool(
                        name=name,
                        description=description or "",
                        params_type=params_type,
                        handler=funct,
                    )

                    extra_tools.append(tool)

        get_var_tool = await create_get_variable_tool(execution_model=execution_model)
        set_var_tool = await create_set_variable_tool(execution_model=execution_model)

        # Build tool list for the session (set and get variable tools first)
        session_tools = [set_var_tool, get_var_tool] + extra_tools

        session = await self.client.con.create_session(
            SessionConfig(
                system_message=SystemMessageAppendConfig(content=SYSTEM_PROMPT),
                model="gpt-5-mini",
                streaming=True,
                infinite_sessions=InfiniteSessionConfig(
                    enabled=True,
                ),
                tools=session_tools,
            ),
        )

        run = execution_model.start_run(
            prompt=execution_model.context.window,
            provider="copilot",
            status=RunStatus.RUNNING,
            start_time=datetime.now(timezone.utc),
        )

        def handle_event(event):
            d = event.data

            execution_model.current_run.event_name = event.type.value

            if event.type == SessionEventType.SESSION_START:
                run.session_id = d.session_id
                run.model = d.selected_model or d.current_model
                if d.context and hasattr(d.context, "cwd"):
                    run.context = RunContext(
                        cwd=d.context.cwd,
                        git_root=d.context.git_root,
                        branch=d.context.branch,
                    )
                if d.repository:
                    run.context.repository_owner = d.repository.owner
                    run.context.repository_name = d.repository.name

            elif event.type == SessionEventType.ASSISTANT_REASONING_DELTA:
                if run.reasoning is None:
                    run.reasoning = [""]
                run.reasoning[-1] += d.delta_content
                if (
                    not run.content_blocks
                    or run.content_blocks[-1].type != ContentBlockType.REASONING
                ):
                    run.content_blocks.append(
                        ContentBlock(type=ContentBlockType.REASONING)
                    )
                run.content_blocks[-1].text += d.delta_content

            elif event.type == SessionEventType.ASSISTANT_MESSAGE_DELTA:
                if run.responses is None:
                    run.responses = [""]
                run.responses[-1] += d.delta_content
                if (
                    not run.content_blocks
                    or run.content_blocks[-1].type != ContentBlockType.RESPONSE
                ):
                    run.content_blocks.append(
                        ContentBlock(type=ContentBlockType.RESPONSE)
                    )
                run.content_blocks[-1].text += d.delta_content

            elif (
                event.type == SessionEventType.ASSISTANT_TURN_END
                or event.type == SessionEventType.ASSISTANT_MESSAGE
            ):
                # Start a new entry for the next turn
                if run.responses is not None:
                    run.responses.append("")
                if run.reasoning is not None:
                    run.reasoning.append("")
            elif event.type == SessionEventType.SESSION_USAGE_INFO:
                pass
            elif event.type == SessionEventType.ASSISTANT_USAGE:
                run.request_count += 1
                turn_tokens = TokenUsage(
                    input_tokens=int(d.input_tokens or 0),
                    output_tokens=int(d.output_tokens or 0),
                    cache_read_tokens=int(d.cache_read_tokens or 0),
                    cache_write_tokens=int(d.cache_write_tokens or 0),
                )
                run.tokens.accumulate(turn_tokens)
                if d.cost:
                    run.total_cost += d.cost
                model = d.model or run.model
                if model:
                    if model not in run.model_usage:
                        run.model_usage[model] = ModelUsage(model=model)
                    mu = run.model_usage[model]
                    mu.request_count += 1
                    mu.tokens.accumulate(turn_tokens)
                    if d.cost:
                        mu.cost += d.cost

            elif event.type == SessionEventType.TOOL_EXECUTION_START:
                if d.tool_name == "report_intent":
                    return  # This is an internal tool used for logging the agent's intent, we can ignore it in the run log.
                run.tool_calls.append(
                    ToolCall(
                        tool_name=d.tool_name,
                        tool_call_id=d.tool_call_id,
                        arguments=d.arguments,
                    )
                )
                run.content_blocks.append(
                    ContentBlock(
                        type=ContentBlockType.TOOL_CALL,
                        ref=d.tool_call_id,
                    )
                )

            elif event.type == SessionEventType.TOOL_EXECUTION_COMPLETE:
                for tc in reversed(run.tool_calls):
                    if tc.tool_call_id == d.tool_call_id:
                        tc.result = d.result.content if d.result else None
                        tc.success = d.success
                        tc.duration_ms = d.duration
                        break

            elif event.type == SessionEventType.SESSION_MODEL_CHANGE:
                run.model = d.new_model

            elif event.type == SessionEventType.SESSION_ERROR:
                run.errors.append(
                    RunError(
                        message=d.message or "Unknown error",
                        code=d.error_type,
                        stack=d.stack,
                        error_type=d.error_type,
                    )
                )

            elif event.type == SessionEventType.SESSION_SHUTDOWN:
                run.end_time = datetime.now(timezone.utc)
                run.status = RunStatus.COMPLETED
                if d.shutdown_type:
                    run.shutdown_reason = ShutdownReason(d.shutdown_type.value)
                if d.code_changes:
                    run.code_changes = CodeChanges(
                        files_modified=d.code_changes.files_modified,
                        lines_added=int(d.code_changes.lines_added),
                        lines_removed=int(d.code_changes.lines_removed),
                    )
                if d.model_metrics:
                    for model_name, metric in d.model_metrics.items():
                        if model_name not in run.model_usage:
                            run.model_usage[model_name] = ModelUsage(model=model_name)
                        mu = run.model_usage[model_name]
                        mu.request_count = int(metric.requests.count)
                        mu.cost = metric.requests.cost

            elif event.type == SessionEventType.SESSION_IDLE:
                run.status = RunStatus.IDLE

        session.on(handle_event)

        response = await session.send_and_wait(
            MessageOptions(prompt=execution_model.context.window), timeout=300
        )

        if run.status != RunStatus.COMPLETED:
            run.end_time = datetime.now(timezone.utc)
            run.status = RunStatus.COMPLETED
        if run.start_time and run.end_time:
            run.duration_ms = (run.end_time - run.start_time).total_seconds() * 1000

        await session.destroy()

        execution_model.current_run.result = response.data.content if response else None

        return response.data.content
