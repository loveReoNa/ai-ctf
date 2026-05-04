"""Tool call logging schema definitions for structured trace recording."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class TokenUsage:
    """Token usage record for a single API call or tool invocation.

    Attributes:
        input_tokens: Number of input/prompt tokens consumed.
        output_tokens: Number of output/completion tokens produced.
        total_tokens: Sum of input and output tokens.
        cost_usd: Estimated cost in USD based on model pricing.
    """

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0

    def __post_init__(self):
        if self.total_tokens == 0 and (self.input_tokens > 0 or self.output_tokens > 0):
            self.total_tokens = self.input_tokens + self.output_tokens


@dataclass
class LoggedToolCall:
    """Complete log record for a single tool call during an agent run.

    Attributes:
        call_id: Unique identifier for this call.
        timestamp_start: ISO 8601 timestamp when the call started.
        timestamp_end: ISO 8601 timestamp when the call completed.
        tool_name: Name of the tool invoked.
        server_name: MCP server that provided the tool.
        arguments: JSON-serializable arguments passed to the tool.
        result: Structured return data from the tool.
        success: Whether the tool call succeeded (no error).
        error_message: Error description if the call failed.
        token_usage: Token consumption for this call.
        turn_number: Which agent turn this call belongs to.
    """

    call_id: str = ""
    timestamp_start: Optional[datetime] = None
    timestamp_end: Optional[datetime] = None
    tool_name: str = ""
    server_name: str = ""
    arguments: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    success: bool = False
    error_message: Optional[str] = None
    token_usage: Optional[TokenUsage] = None
    turn_number: int = 0

    @property
    def execution_time_ms(self) -> float:
        """Calculate execution time in milliseconds."""
        if self.timestamp_start and self.timestamp_end:
            delta = self.timestamp_end - self.timestamp_start
            return delta.total_seconds() * 1000.0
        return 0.0