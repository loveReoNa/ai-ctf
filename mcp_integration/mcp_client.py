"""MCP protocol client wrapper for communication with MCP servers."""

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from mcp_integration.schemas.tool_call_schema import TokenUsage


class TransportType(str, Enum):
    """MCP transport types."""

    STDIO = "stdio"
    SSE = "sse"
    STREAMABLE_HTTP = "streamable_http"


@dataclass
class MCPConnectionConfig:
    """Configuration for connecting to an MCP server.

    Attributes:
        server_name: Unique name identifying the server.
        transport_type: Communication transport mechanism.
        command: CLI command to launch server (stdio mode).
        args: CLI arguments for server launch (stdio mode).
        url: Server URL (sse/http modes).
        timeout_seconds: Connection and request timeout.
    """

    server_name: str = ""
    transport_type: TransportType = TransportType.STDIO
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    timeout_seconds: int = 30


@dataclass
class ToolSchema:
    """Schema definition for a tool provided by an MCP server.

    Attributes:
        name: Tool name.
        description: Human-readable tool description.
        input_schema: JSON Schema for tool input parameters.
        server_name: Which server provides this tool.
        tool_category: Category classification for the tool.
    """

    name: str = ""
    description: str = ""
    input_schema: Dict[str, Any] = field(default_factory=dict)
    server_name: str = ""
    tool_category: str = "utility"


@dataclass
class ServerInfo:
    """Information about a connected MCP server.

    Attributes:
        name: Server name.
        version: Server version string.
        tool_count: Number of tools available.
        transport: Transport type in use.
        connected: Whether currently connected.
    """

    name: str = ""
    version: str = "unknown"
    tool_count: int = 0
    transport: str = "stdio"
    connected: bool = False


@dataclass
class ToolCallResult:
    """Result of a tool invocation via MCP.

    Attributes:
        success: Whether the call completed without error.
        tool_name: Name of the tool called.
        arguments: Arguments passed to the tool.
        result: Structured return data.
        raw_output: Raw text output from the tool.
        error_message: Error description if failed.
        execution_time_ms: Time taken in milliseconds.
        token_usage: Estimated token usage.
    """

    success: bool = False
    tool_name: str = ""
    arguments: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    raw_output: str = ""
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    token_usage: Optional[TokenUsage] = None


class MCPClient:
    """MCP protocol client managing connection and tool calls to one server.

    Handles the lifecycle of a connection to an MCP server and provides
    interfaces to discover tools and execute them.
    """

    def __init__(self, server_config: MCPConnectionConfig):
        """Initialize MCP client with server configuration.

        Args:
            server_config: Connection parameters for the MCP server.
        """
        self.config = server_config
        self._connected = False
        self._tools: List[ToolSchema] = []

    def connect(self) -> bool:
        """Establish connection to the MCP server.

        Returns:
            True if connection successful, False otherwise.

        Note:
            In a full implementation, this would use the mcp Python package
            to establish stdio/sse/http connections. Currently uses mock data.
        """
        try:
            self._connected = True
            self._tools = self._load_mock_tools()
            return True
        except Exception:
            self._connected = False
            return False

    def disconnect(self) -> None:
        """Close the connection to the MCP server."""
        self._connected = False
        self._tools = []

    def list_tools(self) -> List[ToolSchema]:
        """Get all tools available from this server.

        Returns:
            List of tool schemas.
        """
        if not self._connected:
            return []
        return self._tools

    def call_tool(self, tool_name: str, arguments: dict) -> ToolCallResult:
        """Execute a tool on the MCP server.

        Args:
            tool_name: Name of the tool to invoke.
            arguments: JSON-serializable arguments to pass.

        Returns:
            Structured result of the tool call.
        """
        start_time = time.time()
        try:
            if not self._connected:
                return ToolCallResult(
                    success=False,
                    tool_name=tool_name,
                    arguments=arguments,
                    error_message="Client not connected",
                )
            # In full implementation, this would use mcp client calls
            result_data = {"tool": tool_name, "args": arguments, "output": "mock result"}
            end_time = time.time()
            return ToolCallResult(
                success=True,
                tool_name=tool_name,
                arguments=arguments,
                result=result_data,
                raw_output=json.dumps(result_data),
                execution_time_ms=(end_time - start_time) * 1000.0,
                token_usage=TokenUsage(input_tokens=50, output_tokens=30),
            )
        except Exception as e:
            end_time = time.time()
            return ToolCallResult(
                success=False,
                tool_name=tool_name,
                arguments=arguments,
                error_message=str(e),
                execution_time_ms=(end_time - start_time) * 1000.0,
            )

    def get_server_info(self) -> ServerInfo:
        """Get information about the connected server.

        Returns:
            ServerInfo with connection details.
        """
        return ServerInfo(
            name=self.config.server_name,
            transport=self.config.transport_type.value,
            connected=self._connected,
            tool_count=len(self._tools),
        )

    def _load_mock_tools(self) -> List[ToolSchema]:
        """Load mock tool definitions for testing.

        Returns:
            List of mock ToolSchema entries.
        """
        return [
            ToolSchema(
                name="nmap_scan",
                description="Scan target for open ports and services",
                input_schema={
                    "type": "object",
                    "properties": {
                        "target": {"type": "string", "description": "Target IP or hostname"},
                        "ports": {"type": "string", "description": "Port range (e.g. 1-1000)"},
                    },
                    "required": ["target"],
                },
                server_name=self.config.server_name,
                tool_category="reconnaissance",
            ),
            ToolSchema(
                name="gobuster_scan",
                description="Directory/file enumeration on web servers",
                input_schema={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "Target URL"},
                        "wordlist": {"type": "string", "description": "Wordlist path"},
                    },
                    "required": ["url"],
                },
                server_name=self.config.server_name,
                tool_category="web_scanning",
            ),
            ToolSchema(
                name="sqlmap_scan",
                description="Automated SQL injection detection and exploitation",
                input_schema={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "Target URL"},
                        "data": {"type": "string", "description": "POST data"},
                    },
                    "required": ["url"],
                },
                server_name=self.config.server_name,
                tool_category="web_exploitation",
            ),
        ]