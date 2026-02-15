from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from entities.function import FunctionCall


class ContentBlockType(Enum):
    REASONING = "reasoning"
    RESPONSE = "response"
    FUNCTION_CALL = "function_call"
    TOOL_CALL = "tool_call"
    OTHER = "other"


@dataclass
class ContentBlock:
    type: ContentBlockType
    text: str = ""
    ref: Optional[str] = None


class RunStatus(Enum):
    PENDING = "starting"
    RUNNING = "running"
    IDLE = "idle"
    ERROR = "error"
    COMPLETED = "completed"


class ShutdownReason(Enum):
    ROUTINE = "routine"
    ERROR = "error"
    TIMEOUT = "timeout"
    ABORTED = "aborted"


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def accumulate(self, other: "TokenUsage"):
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.cache_read_tokens += other.cache_read_tokens
        self.cache_write_tokens += other.cache_write_tokens


@dataclass
class ModelUsage:
    model: str
    request_count: int = 0
    cost: float = 0.0
    tokens: TokenUsage = field(default_factory=TokenUsage)

@dataclass
class ToolCall:
    tool_name: str
    tool_call_id: str
    arguments: Any = None
    result: Optional[str] = None
    success: Optional[bool] = None
    duration_ms: Optional[float] = None
    parent_tool_call_id: Optional[str] = None


@dataclass
class CodeChanges:
    files_modified: list[str] = field(default_factory=list)
    lines_added: int = 0
    lines_removed: int = 0


@dataclass
class RunError:
    message: str
    code: Optional[str] = None
    stack: Optional[str] = None
    error_type: Optional[str] = None


@dataclass
class RunContext:
    cwd: Optional[str] = None
    git_root: Optional[str] = None
    branch: Optional[str] = None
    repository_owner: Optional[str] = None
    repository_name: Optional[str] = None


@dataclass
class Run:
    # Identity
    session_id: Optional[str] = None
    turn_id: Optional[str] = None

    # Lifecycle
    status: RunStatus = RunStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    shutdown_reason: Optional[ShutdownReason] = None

    # Model
    model: Optional[str] = None
    provider: Optional[str] = None

    # Usage (aggregated across all API calls in this run)
    tokens: TokenUsage = field(default_factory=TokenUsage)
    total_cost: float = 0.0
    request_count: int = 0
    model_usage: dict[str, ModelUsage] = field(default_factory=dict)

    # Content
    prompt: Optional[str] = None
    responses: Optional[list[str]] = None
    reasoning: Optional[list[str]] = None
    content_blocks: list[ContentBlock] = field(default_factory=list)

    # Tool execution
    tool_calls: list[ToolCall] = field(default_factory=list)

    # Code impact
    code_changes: Optional[CodeChanges] = None

    # Environment
    context: RunContext = field(default_factory=RunContext)

    # Errors
    errors: list[RunError] = field(default_factory=list)

    # Extensible metadata (provider-specific data, telemetry, etc.)
    metadata: dict[str, Any] = field(default_factory=dict)
